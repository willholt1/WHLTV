from demoparser2 import DemoParser
import gc
import os
import re
import shutil
import sys
import tempfile
import traceback

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from models import enums

from . import conversion_constants as c


# Events where player state is sampled AT the event tick (T), not the tick
# before (T-1). Determined empirically by comparing parse_event output with
# parse_ticks at both offsets.
_EVENTS_USING_CURRENT_TICK: frozenset[str] = frozenset({
    "inferno_startburn",
    "inferno_expire",
})
# main memory consumer, so it is parsed and flushed to disk in sub-sections of
# roughly this many rows. Smaller values use less memory but require more parse
# passes over each demo; larger values use more memory but fewer passes.
DEFAULT_CHUNK_SIZE = 50_000


# Number of rows read/written at a time when combining the temporary parquet
# files into the final output. Temp files are written with this row-group size
# so the combine step can stream them one batch at a time, keeping peak memory
# bounded regardless of how large an individual event or tick file grows.
COMBINE_BATCH_SIZE = 50_000

# When True, emit per-chunk/per-piece write lines and RSS delta logs.
# Leave False in production — the volume of output can fill Docker's pipe
# buffer and cause the process to block on pipe_write with 0% CPU.
VERBOSE_LOGGING = False


def _log(message: str) -> None:
    print(message, file=sys.stderr)


def _vlog(message: str) -> None:
    """Log only when VERBOSE_LOGGING is enabled."""
    if VERBOSE_LOGGING:
        print(message, file=sys.stderr)


def _rss_mib() -> float | None:
    """Current process RSS in MiB, Linux /proc only (returns None elsewhere)."""
    try:
    	with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    except (FileNotFoundError, OSError, ValueError):
        pass
    return None


def _log_rss(label: str, prev: float | None = None) -> float | None:
    """Log RSS with an optional delta vs ``prev``. Returns current RSS.
    Output is suppressed unless VERBOSE_LOGGING is True.
    """
    if not VERBOSE_LOGGING:
        return _rss_mib()
    cur = _rss_mib()
    if cur is None:
        return None
    if prev is not None:
        delta = cur - prev
        sign = "+" if delta >= 0 else ""
        _log(f"[MEM] {label}: rss={cur:.1f}MiB delta={sign}{delta:.1f}MiB")
    else:
        _log(f"[MEM] {label}: rss={cur:.1f}MiB")
    return cur


def _release_memory() -> None:
    """GC cycle + best-effort glibc malloc_trim to return free arenas to OS."""
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        if hasattr(libc, "malloc_trim"):
            libc.malloc_trim(0)
    except BaseException:
    	pass


def _df_stats(df: pd.DataFrame) -> str:
    """Compact dataframe diagnostics for memory/failure debugging logs."""
    if df is None:
        return "df=None"

    rows, cols = df.shape
    if rows == 0:
        return f"rows=0 cols={cols}"

    mem_mib = float(df.memory_usage(deep=True).sum()) / (1024 * 1024)
    parts = [f"rows={rows}", f"cols={cols}", f"mem={mem_mib:.2f}MiB"]

    if "tick" in df.columns:
        tick_series = df["tick"]
        if not tick_series.empty:
            parts.append(f"tick_min={tick_series.min()}")
            parts.append(f"tick_max={tick_series.max()}")

    return " ".join(parts)


def demoToParquet(demoPaths, output_dir="ParquetFiles", chunk_size=DEFAULT_CHUNK_SIZE, combine_batch_size=COMBINE_BATCH_SIZE):
    map_groups = get_map_groups(demoPaths)
    if not map_groups:
        raise RuntimeError("No valid demos could be grouped for conversion.")

    created_files = {}

    os.makedirs(output_dir, exist_ok=True)

    for map_name, map_data in map_groups.items():
        parquet_path = os.path.join(output_dir, generate_parquet_filename(map_data["demos"][0][0], map_name))

        temp_dir = tempfile.mkdtemp(prefix=f"{map_name}_chunks_", dir=output_dir)
        try:
            temp_files = write_demo_temp_files(map_data["demos"], temp_dir, chunk_size, combine_batch_size)
            if not temp_files:
                raise RuntimeError(f"No demos could be parsed successfully for map {map_name}.")

            _log(f"Combining {len(temp_files)} temp file(s) for map {map_name} into {parquet_path}...")
            combine_temp_files(temp_files, parquet_path, batch_size=combine_batch_size)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            # Release memory between map groups so native allocations from
            # one map don't persist into the next.
            _release_memory()
            _log_rss(f"after {map_name} cleanup")

        created_files[enums.de_map_from_str(map_name)] = [parquet_path, map_data["patch_version"]]
    return created_files


def write_demo_temp_files(demos, temp_dir, chunk_size, combine_batch_size=COMBINE_BATCH_SIZE):
    """Parse each demo and stream its tick/event data to temporary parquet files.

    Tick data is parsed and flushed in sub-sections of roughly ``chunk_size``
    rows so the full tick table for a demo never has to live in memory at once.
    Large event tables are likewise sliced into ``chunk_size`` row pieces when
    written so the pandas->arrow conversion never spikes on a single huge event.
    Returns the list of temporary parquet paths that were written.
    """
    temp_files = []
    tick_offset = 0

    for idx, (demoPath, _, max_tick) in enumerate(sorted(demos, key=lambda x: x[1])):
        stage = "initialization"
        demo_tag = f"demo{idx}"
        stage_context = ""
        try:
            parser = DemoParser(demoPath)
            rss = _log_rss(f"parser init {demoPath}")

            stage = "parse_ticks"
            chunk_idx = 0
            demo_max_tick = None
            for tick_data in iter_tick_chunks(parser, max_tick, chunk_size):
                if "tick" in tick_data.columns and not tick_data.empty:
                    chunk_max = int(tick_data["tick"].max())
                    if demo_max_tick is None or chunk_max > demo_max_tick:
                        demo_max_tick = chunk_max

                for col in c.TICK_COLS:
                    if col in tick_data.columns:
                        tick_data[col] += tick_offset
                clean_steamID_cols(tick_data, "steamid")

                chunk_path = os.path.join(temp_dir, f"{demo_tag}_ticks_{chunk_idx}.parquet")
                _vlog(f"Writing tick chunk {chunk_idx} ({len(tick_data)} rows) for {demoPath}")
                tick_data.to_parquet(chunk_path, index=False, row_group_size=combine_batch_size)
                temp_files.append(chunk_path)
                chunk_idx += 1

            stage = "parse_grenades"
            _log("Parsing grenade data")
            rss = _log_rss("before parse_grenades", rss)
            df = pd.DataFrame(parser.parse_grenades())
            rss = _log_rss("after parse_grenades", rss)
            if not df.empty:
                df["event_type"] = "grenade_data"
                for col in c.TICK_COLS:
                    if col in df.columns:
                        df[col] += tick_offset
                _vlog(f"Grenade dataframe stats for {demoPath}: {_df_stats(df)}")
                stage_context = f"event=grenade_data stats=({_df_stats(df)})"
                temp_files.extend(
                    _write_event_temp_files(df, temp_dir, f"{demo_tag}_grenades", chunk_size, combine_batch_size)
                )
            del df
            _release_memory()
            rss = _log_rss("after grenade cleanup", rss)

            non_player_events = {"server_cvar"}

            # ----------------------------------------------------------------
            # Phase 1 – parse all events raw (no player/world props).
            # Accumulate every unique tick seen across all events so we can
            # do a single targeted parse_ticks call in phase 2.
            # ----------------------------------------------------------------
            raw_event_dfs: dict[str, pd.DataFrame] = {}
            all_event_ticks: set[int] = set()

            for event in c.TRACKED_EVENTS:
                stage = f"parse_event_raw:{event}"
                _log(f"Parsing event (raw): {event} from {demoPath}")
                rss = _log_rss(f"before parse_event_raw:{event}", rss)
                df = pd.DataFrame(parser.parse_event(event))
                rss = _log_rss(f"after parse_event_raw:{event}", rss)

                if df.empty:
                    del df
                    continue

                df["event_type"] = event
                for col in c.TICK_COLS:
                    if col in df.columns:
                        df[col] += tick_offset

                if event not in non_player_events and "tick" in df.columns:
                    all_event_ticks.update(df["tick"].dropna().astype(int).tolist())

                raw_event_dfs[event] = df
                del df

            # ----------------------------------------------------------------
            # Phase 2 – one targeted parse_ticks call for only the ticks
            # where events occurred.
            # • Player props (DEFAULT_PLAYER_PROPS): per-player per-tick rows,
            #   joined per role (user_*, attacker_*, etc.) by (tick, steamid).
            #   Cost: n_event_ticks × 10 players × props – typically ~64 MB,
            #   not the full all_ticks timeline that caused OOM.
            # • World props (DEFAULT_WORLD_PROPS + team-entity props): dedup'd
            #   to 1 row per tick, joined 1:1 to event rows by tick.
            #   ct_team_name / t_team_name are added here so that awpy's
            #   fix_common_names can rename them to ct_side / t_side.
            # ----------------------------------------------------------------
            player_state_by_tick: pd.DataFrame | None = None
            world_state_by_tick: pd.DataFrame | None = None
            if all_event_ticks:
                event_tick_list = sorted(all_event_ticks)
                # Player state is joined at T-1 for most events and T for
                # inferno events.  Fetch all needed ticks in one call.
                player_tick_set = (
                    set(event_tick_list)                          # T (for infernos + world state)
                    | {max(0, t - 1) for t in event_tick_list}  # T-1 (for most events)
                )
                n_ticks = len(event_tick_list)
                _vlog(f"Fetching player+world state for {n_ticks} unique event ticks (+ T-1 for player props)")
                rss = _log_rss("before event-tick state parse", rss)
                raw_state = pd.DataFrame(
                    parser.parse_ticks(
                        c.DEFAULT_PLAYER_PROPS + c.DEFAULT_WORLD_PROPS,
                        ticks=sorted(player_tick_set),
                    )
                )
                rss = _log_rss("after event-tick state parse", rss)
                _vlog(f"Event-tick state frame: {_df_stats(raw_state)}")

                if not raw_state.empty and "tick" in raw_state.columns:
                    # Player-only subset for per-role enrichment.
                    # Use the full DEFAULT_PLAYER_PROPS so event rows carry the
                    # same player context as the old parse_event(player=...) approach
                    # (armor_value, has_defuser, flash_duration, etc.). We already
                    # fetched all these columns above so there is no extra parse cost.
                    player_only_cols = (
                        ["tick", "steamid"]
                        + [col for col in c.DEFAULT_PLAYER_PROPS if col in raw_state.columns]
                    )
                    player_state_by_tick = raw_state[[col for col in player_only_cols if col in raw_state.columns]].copy()

                    # World-only subset (1 row per tick).
                    # Derive ct/t team name AND clan name so both the game-side
                    # identifier (ct_team_name → ct_side) and the display clan name
                    # (ct_team_clan_name) are present on all event rows, matching
                    # the old parse_event(other=DEFAULT_WORLD_PROPS) output.
                    world_prop_cols = [col for col in c.DEFAULT_WORLD_PROPS if col in raw_state.columns]
                    world_base = (
                        raw_state[["tick"] + world_prop_cols]
                        .drop_duplicates(subset=["tick"])
                        .reset_index(drop=True)
                    )
                    if "team_name" in raw_state.columns:
                        ct_names = (
                            raw_state[raw_state["team_name"] == "CT"][["tick", "team_name"]]
                            .drop_duplicates(subset=["tick"])
                            .rename(columns={"team_name": "ct_team_name"})
                        )
                        t_names = (
                            raw_state[raw_state["team_name"] == "TERRORIST"][["tick", "team_name"]]
                            .drop_duplicates(subset=["tick"])
                            .rename(columns={"team_name": "t_team_name"})
                        )
                        world_base = world_base.merge(ct_names, on="tick", how="left")
                        world_base = world_base.merge(t_names, on="tick", how="left")
                    if "team_name" in raw_state.columns and "team_clan_name" in raw_state.columns:
                        ct_clans = (
                            raw_state[raw_state["team_name"] == "CT"][["tick", "team_clan_name"]]
                            .dropna(subset=["team_clan_name"])
                            .drop_duplicates(subset=["tick"])
                            .rename(columns={"team_clan_name": "ct_team_clan_name"})
                        )
                        t_clans = (
                            raw_state[raw_state["team_name"] == "TERRORIST"][["tick", "team_clan_name"]]
                            .dropna(subset=["team_clan_name"])
                            .drop_duplicates(subset=["tick"])
                            .rename(columns={"team_clan_name": "t_team_clan_name"})
                        )
                        world_base = world_base.merge(ct_clans, on="tick", how="left")
                        world_base = world_base.merge(t_clans, on="tick", how="left")
                    world_state_by_tick = world_base
                del raw_state
                _release_memory()
                rss = _log_rss("after event-tick state split", rss)

            # ----------------------------------------------------------------
            # Phase 3 – enrich and write each event:
            #   a) join world state 1:1 by tick
            #   b) join player state per role by (tick, *_steamid)
            # ----------------------------------------------------------------
            for event, df in raw_event_dfs.items():
                stage = f"write_event:{event}"

                if event not in non_player_events and "tick" in df.columns:
                    if (
                        world_state_by_tick is not None
                        and not world_state_by_tick.empty
                        and "tick" in world_state_by_tick.columns
                    ):
                        df = df.merge(
                            world_state_by_tick,
                            on="tick",
                            how="left",
                            suffixes=("", "_world"),
                        )

                    if player_state_by_tick is not None and not player_state_by_tick.empty:
                        tick_offset_for_event = 0 if event in _EVENTS_USING_CURRENT_TICK else -1
                        df = _enrich_event_with_player_state(df, player_state_by_tick, tick_offset=tick_offset_for_event)

                event_stats = _df_stats(df)
                _vlog(f"Event dataframe stats for {event} from {demoPath}: {event_stats}")
                stage_context = f"event={event} stats=({event_stats})"
                temp_files.extend(
                    _write_event_temp_files(df, temp_dir, f"{demo_tag}_event_{event}", chunk_size, combine_batch_size)
                )
                del df
                _release_memory()
                rss = _log_rss(f"after event write+cleanup:{event}", rss)

            del raw_event_dfs
            if player_state_by_tick is not None:
                del player_state_by_tick
            if world_state_by_tick is not None:
                del world_state_by_tick
            _release_memory()
            rss = _log_rss("after all events cleanup", rss)

            if demo_max_tick is not None:
                tick_offset += demo_max_tick + 1
            elif max_tick is not None:
                tick_offset += max_tick + 1

        except BaseException as ex:
            if isinstance(ex, (KeyboardInterrupt, SystemExit, MemoryError)):
                raise
            _log(
                f"Skipping demo {demoPath} at stage '{stage}' due to "
                f"{type(ex).__name__}: {ex}"
            )
            if stage_context:
                _log(f"Stage context: {stage_context}")
            _log(traceback.format_exc())
            continue
        finally:
            try:
                del parser
            except UnboundLocalError:
                pass
            _release_memory()
            _log_rss(f"after demo finally cleanup {demoPath}")

    return temp_files


def _enrich_event_with_player_state(
    df: pd.DataFrame, player_state: pd.DataFrame, tick_offset: int = -1
) -> pd.DataFrame:
    """Add role-prefixed player state columns to an event DataFrame.

    ``tick_offset`` controls which tick to sample player state from relative
    to the event's own tick.  -1 (default) matches demoparser2's behaviour
    for most events (state sampled at T-1, before the event fires).  0 is
    used for entity-creation events (e.g. inferno_startburn) where the state
    is sampled at the event tick itself.
    """
    if "steamid" not in player_state.columns or "tick" not in player_state.columns:
        return df

    # Align steamid dtypes: event *_steamid columns are strings (after
    # clean_steamID_cols), but demoparser2 returns steamid as uint64.
    # Cast the player_state steamid to string so the merge keys match.
    ps_join = player_state.copy()
    ps_join["steamid"] = ps_join["steamid"].astype(str)

    # Columns in player_state that carry per-player values (not tick/steamid).
    state_prop_cols = [
        col for col in ps_join.columns if col not in ("tick", "steamid")
    ]
    if not state_prop_cols:
        return df

    # Role columns present in the event df (e.g. user_steamid, attacker_steamid).
    role_steamid_cols = [col for col in df.columns if col.endswith("_steamid")]
    if not role_steamid_cols:
        return df

    # Use tick + tick_offset for player state lookup.
    df["_player_lookup_tick"] = (df["tick"] + tick_offset).clip(lower=0)

    for role_col in role_steamid_cols:
        role_prefix = role_col[: -len("steamid")]  # "user_steamid" -> "user_"

        # Build a sub-frame: merge event rows with player state by (tick-1, role_steamid).
        role_lookup = (
            df[["_player_lookup_tick", role_col]]
            .merge(
                ps_join[["tick", "steamid"] + state_prop_cols],
                left_on=["_player_lookup_tick", role_col],
                right_on=["tick", "steamid"],
                how="left",
            )
            [state_prop_cols]
        )
        role_lookup.index = df.index

        for prop in state_prop_cols:
            target_col = f"{role_prefix}{prop}"
            # Skip if a column with this name already exists (e.g. native event field).
            if target_col not in df.columns:
                df[target_col] = role_lookup[prop].values

    df.drop(columns=["_player_lookup_tick"], inplace=True)
    return df


def _write_event_temp_files(df, temp_dir, name, chunk_size, combine_batch_size=COMBINE_BATCH_SIZE):
    """Write an event/grenade dataframe to one or more temp parquet files.

    The frame is sliced into ``chunk_size`` row pieces so the pandas->arrow
    conversion performed by ``to_parquet`` is bounded, even for very large
    events such as ``fire_bullets`` or ``player_sound``.
    """
    clean_steamID_cols(df, "user_steamid")
    clean_steamID_cols(df, "steamid")

    paths = []
    n = len(df)
    if n == 0:
        return paths

    step = max(1, chunk_size)
    total_pieces = (n + step - 1) // step
    _vlog(
        f"Writing event temp files for {name}: rows={n} chunk_rows={step} "
        f"pieces={total_pieces} row_group_size={combine_batch_size}"
    )
    for piece_idx, start in enumerate(range(0, n, step)):
        piece = df.iloc[start:start + step]
        end = start + len(piece) - 1
        path = os.path.join(temp_dir, f"{name}_{piece_idx}.parquet")
        _vlog(
            f"  piece {piece_idx + 1}/{total_pieces} rows={len(piece)} "
            f"range=[{start}:{end}] stats=({_df_stats(piece)}) -> {path}"
        )
        piece.to_parquet(path, index=False, row_group_size=combine_batch_size)
        paths.append(path)
        del piece
        _release_memory()
    return paths


def iter_tick_chunks(parser, max_tick, chunk_size):
    """Yield tick dataframes for a demo in sub-sections of ~``chunk_size`` rows.

    Uses demoparser2's ``ticks`` argument to only materialise a window of ticks
    at a time. The tick window is sized from the observed number of players per
    tick so each yielded chunk is close to ``chunk_size`` rows.
    """
    if max_tick is None or max_tick < 0:
        tick_data = parser.parse_ticks(c.TRACKED_TICK_PROPS)
        if tick_data is not None and not tick_data.empty:
            yield tick_data
        return

    players_per_tick = 10
    start = 0
    while start <= max_tick:
        ticks_per_chunk = max(1, chunk_size // max(1, players_per_tick))
        end = min(start + ticks_per_chunk, max_tick + 1)

        tick_data = parser.parse_ticks(c.TRACKED_TICK_PROPS, ticks=list(range(start, end)))
        if tick_data is not None and not tick_data.empty:
            n_ticks = tick_data["tick"].nunique() if "tick" in tick_data.columns else (end - start)
            if n_ticks > 0:
                players_per_tick = max(1, round(len(tick_data) / n_ticks))
            yield tick_data

        start = end


def _has_concrete_value_type(arrow_type):
    """True if a list-like type has a non-null element type (e.g. list<int64>)."""
    if (
        pa.types.is_list(arrow_type)
        or pa.types.is_large_list(arrow_type)
        or pa.types.is_fixed_size_list(arrow_type)
    ):
        return not pa.types.is_null(arrow_type.value_type)
    # Non-list nested types (struct/map) are treated as already concrete.
    return True


def _resolve_arrow_type(types):
    non_null = [t for t in types if not pa.types.is_null(t)]
    if not non_null:
        return pa.string()

    # Nested columns (e.g. inventory lists) must never be collapsed to a scalar
    # type. If any file carries the column as a nested type, keep that type;
    # conflicting scalar columns (usually all-null placeholders) are null-filled
    # during the combine step. Prefer a list whose element type is concrete: an
    # all-empty chunk types the column as list<null>, which would otherwise drop
    # the real list<...> values from other chunks.
    nested = [t for t in non_null if pa.types.is_nested(t)]
    if nested:
        for t in nested:
            if _has_concrete_value_type(t):
                return t
        return nested[0]

    first = non_null[0]
    if all(t.equals(first) for t in non_null):
        return first

    if all(pa.types.is_integer(t) or pa.types.is_floating(t) for t in non_null):
        return pa.float64()

    return pa.string()


def _coerce_column(column, target_type, num_rows):
    """Coerce a column (or missing column) to ``target_type`` for the writer."""
    if column is None:
        return pa.nulls(num_rows, type=target_type)

    if column.type.equals(target_type):
        return column

    try:
        return column.cast(target_type, safe=False)
    except (pa.ArrowInvalid, pa.ArrowNotImplementedError, pa.ArrowTypeError):
        # Incompatible types (e.g. an all-null utf8 placeholder colliding with a
        # list column). All-null sources can be safely represented as nulls of
        # the target type; anything else is stringified as a last resort.
        if column.null_count == len(column):
            return pa.nulls(len(column), type=target_type)
        if pa.types.is_string(target_type):
            return pa.array(
                [None if v is None else str(v) for v in column.to_pylist()],
                type=target_type,
            )
        _log(
            f"Dropping incompatible values while coercing column to {target_type}; "
            f"source type was {column.type}."
        )
        return pa.nulls(len(column), type=target_type)


def build_unified_schema(temp_files):
    """Build a single arrow schema covering the union of columns across files."""
    col_order = []
    col_types = {}
    for path in temp_files:
        schema = pq.read_schema(path)
        for field in schema:
            if field.name not in col_types:
                col_types[field.name] = []
                col_order.append(field.name)
            col_types[field.name].append(field.type)

    return pa.schema([pa.field(name, _resolve_arrow_type(col_types[name])) for name in col_order])


def combine_temp_files(temp_files, final_path, batch_size=COMBINE_BATCH_SIZE):
    """Stream temporary parquet files into a single parquet, one batch at a time.

    This reproduces the row-union of the old ``pd.concat`` step without ever
    holding more than ``batch_size`` rows in memory: each temp file is read in
    row-group sized batches, missing columns are filled with nulls and
    conflicting column types are promoted to a common type.
    """
    schema = build_unified_schema(temp_files)

    writer = pq.ParquetWriter(final_path, schema)
    try:
        for path in temp_files:
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                name_to_idx = {name: idx for idx, name in enumerate(batch.schema.names)}
                arrays = []
                for field in schema:
                    idx = name_to_idx.get(field.name)
                    column = batch.column(idx) if idx is not None else None
                    arrays.append(_coerce_column(column, field.type, batch.num_rows))
                writer.write_table(pa.table(arrays, schema=schema))
    finally:
        writer.close()


def get_map_groups(demoPaths):
    map_groups = {}

    for demoPath in demoPaths:
        stage = "header_grouping"
        try:
            if os.path.getsize(demoPath) == 0:
                _log(f"Skipping empty demo file: {demoPath}")
                continue

            stage = "parse_header"
            parser = DemoParser(demoPath)
            header = parser.parse_header()
            map_name = header["map_name"]
            patch_version = header["patch_version"]

            stage = "parse_total_rounds_played"
            rounds_df = parser.parse_ticks(["total_rounds_played"])
            total_rounds_played = rounds_df["total_rounds_played"].max() if "total_rounds_played" in rounds_df else 0
            max_tick = int(rounds_df["tick"].max()) if "tick" in rounds_df.columns and not rounds_df.empty else None

            _log(f"Grouped demo {demoPath}: map={map_name}, patch={patch_version}, rounds={total_rounds_played}, max_tick={max_tick}")

            if map_name not in map_groups:
                map_groups[map_name] = {"patch_version": patch_version, "demos": []}
            map_groups[map_name]["demos"].append((demoPath, total_rounds_played, max_tick))

        except BaseException as ex:
            if isinstance(ex, (KeyboardInterrupt, SystemExit)):
                raise
            _log(
                f"Skipping demo {demoPath} at stage '{stage}' due to "
                f"{type(ex).__name__}: {ex}"
            )
            _log(traceback.format_exc())
            continue

    return map_groups


def generate_parquet_filename(demo_path, map_name):
    filename = os.path.basename(demo_path)
    name_no_ext = filename.rsplit(".", 1)[0]

    parts = name_no_ext.split("-")

    last = parts[-1]
    has_part_suffix = re.fullmatch(r"p\d+", last) is not None

    if has_part_suffix:
        base = "-".join(parts[:-2])
    else:
        base = "-".join(parts[:-1])

    parquet_name = f"{base}-{map_name}.parquet"
    return parquet_name


def clean_steamID_cols(df: pd.DataFrame, column_name: str) -> None:
    if column_name in df.columns:
        df[column_name] = df[column_name].astype(str)
        df.loc[df[column_name].isin(["None", "nan", "NaN", "<NA>"]), column_name] = None
