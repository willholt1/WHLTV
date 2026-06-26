--
-- PostgreSQL database dump
--

\restrict ZG80D4TWDsL9EZuyoknZFybJnhz2jmvhxL5YsZ3aOmW2ebCy3RFORpsO0MVVi9v

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 18.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: dbo; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA dbo;


--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: demo_conversion_status; Type: TYPE; Schema: dbo; Owner: -
--

CREATE TYPE dbo.demo_conversion_status AS ENUM (
    'ReadyToConvert',
    'Converting',
    'ReadyToValidate',
    'Validating',
    'ReadyToStore',
    'Storing',
    'Stored',
    'Failed'
);


--
-- Name: demo_download_status; Type: TYPE; Schema: dbo; Owner: -
--

CREATE TYPE dbo.demo_download_status AS ENUM (
    'PendingDownload',
    'Downloading',
    'ReadyToExtract',
    'Extracting',
    'Extracted',
    'Completed',
    'Failed'
);


--
-- Name: parquet_file_status; Type: TYPE; Schema: dbo; Owner: -
--

CREATE TYPE dbo.parquet_file_status AS ENUM (
    'Created',
    'Stored',
    'Failed'
);


--
-- Name: pipeline_entity_type; Type: TYPE; Schema: dbo; Owner: -
--

CREATE TYPE dbo.pipeline_entity_type AS ENUM (
    'DemoDownloadJob',
    'DemoConversionJob',
    'ParquetFile'
);


--
-- Name: pipeline_stage_status; Type: TYPE; Schema: dbo; Owner: -
--

CREATE TYPE dbo.pipeline_stage_status AS ENUM (
    'Started',
    'Succeeded',
    'Failed'
);


--
-- Name: udf_get_current_ranking(integer, boolean); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_current_ranking(p_top_x integer, p_vrs_ranking boolean) RETURNS TABLE(ranking_date timestamp without time zone, team_name text, rank integer, points integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_ranking_date timestamp;
BEGIN

    SELECT tr.rankingdate
    INTO v_ranking_date
    FROM tblteamrankings AS tr
    ORDER BY tr.rankingdate DESC
    LIMIT 1;

    if p_vrs_ranking = True THEN
        RETURN QUERY
        SELECT tr.rankingdate, tt.teamname, tr.vrsrank, tr.vrspoints
        FROM tblteamrankings AS tr
        INNER JOIN tblteams AS tt ON tt.teamid = tr.teamid
        WHERE tr.rankingdate = v_ranking_date
        LIMIT (p_top_x);
    ELSE
        RETURN QUERY
        SELECT tr.rankingdate, tt.teamname, tr.hltvrank, tr.hltvpoints
        FROM tblteamrankings AS tr
        INNER JOIN tblteams AS tt ON tt.teamid = tr.teamid
        WHERE tr.rankingdate = v_ranking_date
        LIMIT (p_top_x);
    END IF;

END;
$$;


--
-- Name: udf_get_high_value_events(); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_high_value_events() RETURNS TABLE(eventid integer, hltvurl text)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY
    WITH e AS (
        SELECT t.eventid, t.hltvurl, t.startdate, t.downloadevent
        FROM dbo.tblevents t
        WHERE t.prizepool LIKE '%$%'
          AND LENGTH(t.prizepool) >= 8

        UNION

        SELECT t2.eventid, t2.hltvurl, t2.startdate, t2.downloadevent
        FROM dbo.tblevents t2
        WHERE t2.EventName LIKE '%BLAST%'
           OR (t2.EventName LIKE '%IEM%' AND t2.eventname NOT LIKE '%Qualifier%')
           OR (t2.EventName LIKE '%Major%' AND t2.eventname NOT LIKE '%Open Qualifier%')
           OR (t2.EventName LIKE '%ESL Pro League%' AND t2.eventname NOT LIKE '%Qualifier%')
    )
    SELECT e.eventid, e.hltvurl
    FROM e
    WHERE NOT EXISTS(select 1 from dbo.tbleventteams et where et.eventid = e.eventid)
    AND downloadevent ISNULL
    ORDER BY e.startdate DESC;
END;
$_$;


--
-- Name: udf_get_match_pages(); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_match_pages() RETURNS TABLE(matchid integer, hltvmatchpageurl text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY

    SELECT m.matchid, m.hltvmatchpageurl
    FROM dbo.tblmatches m
    WHERE demolink IS NULL;

END;
$$;


--
-- Name: udf_get_match_players(integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_match_players(p_matchid integer) RETURNS TABLE(teamid integer, teamname text, playerid integer, alias text, steamid text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY

    SELECT mp.teamid, t.teamname, p.playerid, p.alias, p.steamid
    FROM tblmatchplayers mp
    INNER JOIN tblplayers p on p.playerid = mp.playerid
    INNER JOIN tblteams t on t.teamid = mp.teamid
    WHERE matchid = p_matchid
    ORDER BY t.teamid, p.playerid;
END;
$$;


--
-- Name: udf_get_results_pages(); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_results_pages() RETURNS TABLE(eventid integer, hltvresultspageurl text)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY

    SELECT te.eventid
        , 'https://www.hltv.org/results?event=' ||
        regexp_replace(te.hltvurl, '^https://www\.hltv\.org/events/([0-9]+).*$', '\1')
        AS HLTVResultsPageURL
    FROM dbo.tblevents te
    WHERE te.downloadevent = true
    AND NOT exists(SELECT 1 FROM dbo.tblmatches tm WHERE tm.eventid = te.eventid);
END;
$_$;


--
-- Name: udf_get_teams(); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_teams() RETURNS TABLE(team_name text, team_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN

    RETURN QUERY
    SELECT t.teamname, t.teamid
    FROM tblteamrankings AS tr
    INNER JOIN dbo.tblteams t ON tr.teamid = t.teamid
    WHERE hltvrank < 20
    GROUP BY teamname, t.teamid
    ORDER BY COUNT(*) DESC;

END;
$$;


--
-- Name: udf_get_veto_data(date, date, integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_get_veto_data(p_from_date date, p_to_date date, p_team_id integer) RETURNS TABLE(map_name text, pick_total bigint, ban_total bigint, remaining_total bigint, round_dif bigint, ct_round_dif bigint, t_round_dif bigint, wins bigint, times_played bigint, win_pct numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH
    mappool as (
        SELECT DISTINCT t6.mapid
        FROM tblmatches mt
        INNER JOIN tblmatchveto t6 on t6.matchid = mt.matchid
        WHERE mt.matchdate >= p_from_date
            AND mt.matchdate <= p_to_date
    ),
    matches as (
        SELECT t.matchid
                ,t.team1id AS teamid
                ,t3.mapid
                ,t3.team1score
                ,t3.team2score
                ,t3.team1tscore
                ,t3.team2tscore
                ,t3.team1ctscore
                ,t3.team2ctscore
        FROM tblmatches t
        INNER JOIN tblmatchmaps t3 ON t3.matchid = t.matchid
        WHERE t.matchdate >= p_from_date
            AND t.matchdate <= p_to_date
            AND t.team1id = p_team_id

        UNION

        SELECT t2.matchid
            ,t2.team2id AS teamid
            ,t4.mapid
            ,t4.team2score AS team1score
            ,t4.team1score AS team2score
            ,t4.team2tscore AS team1tscore
            ,t4.team1tscore AS team2tscore
            ,t4.team2ctscore AS team1ctscore
            ,t4.team1ctscore AS team2ctscore
        FROM tblmatches t2
        INNER JOIN tblmatchmaps t4 ON t4.matchid = t2.matchid
        WHERE t2.matchdate >= p_from_date
            AND t2.matchdate <= p_to_date
            AND t2.team2id = p_team_id
    ),
    record as (
        SELECT m.matchid
                ,m.mapid
                ,m.team1score - m.team2score AS round_dif
                ,m.team1tscore - m.team2tscore AS t_round_dif
                ,m.team1ctscore - m.team2ctscore AS ct_round_dif
                ,CASE
                    WHEN m.team1score > m.team2score THEN 1
                    WHEN m.team1score < m.team2score THEN 0
                END AS result
        FROM matches AS m
        WHERE m.team1score IS NOT NULL
    ),
    recordpivot AS (
        SELECT r.mapid
                ,SUM(r.round_dif) AS round_dif
                ,SUM(r.t_round_dif) AS t_round_dif
                ,SUM(r.ct_round_dif) AS ct_round_dif
                ,SUM(result) AS wins
                ,count(*) AS times_played
        FROM record r
        GROUP BY r.mapid
    ),
    pickban AS (
        SELECT COUNT(*) AS total
             , mv.mapid
             , mv.vetoactionid
        FROM tblmatchveto mv
        WHERE EXISTS(SELECT 1 FROM matches m2 WHERE m2.matchid = mv.matchid)
          AND (mv.teamid = p_team_id OR mv.teamid IS NULL)
        GROUP BY mv.mapid, mv.vetoactionid
    ),
    pickbanpivot AS (
        SELECT  mn.mapid
                ,mn.mapname
                ,COALESCE(pb1.total, 0) AS pick_total
                ,COALESCE(pb2.total, 0) AS ban_total
                ,COALESCE(pb3.total, 0) AS remaining_total
        FROM tblmaps mn
        LEFT JOIN pickban pb1 ON pb1.mapid = mn.mapid AND pb1.vetoactionid = 1  -- Pick
        LEFT JOIN pickban pb2 ON pb2.mapid = mn.mapid AND pb2.vetoactionid = 2  -- Ban
        LEFT JOIN pickban pb3 ON pb3.mapid = mn.mapid AND pb3.vetoactionid = 3  -- Remaining
        WHERE EXISTS(SELECT 1 FROM mappool mp WHERE mp.mapid = mn.mapid)
    )

    SELECT pbp.mapname AS map_name
            ,pbp.pick_total
            ,pbp.ban_total
            ,pbp.remaining_total
            ,rp.round_dif
            ,rp.ct_round_dif
            ,rp.t_round_dif
            ,rp.wins
            ,rp.times_played
            ,ROUND(rp.wins::DECIMAL / NULLIF(rp.times_played, 0), 4) AS win_pct
    FROM pickbanpivot pbp
    LEFT JOIN recordpivot rp ON rp.mapid = pbp.mapid;

END;
$$;


--
-- Name: udf_insert_match_playerdata(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_insert_match_playerdata(p_payload jsonb, p_matchid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN

    -- 1) Flatten players + nested statlines from JSON
    CREATE TEMP TABLE tmp_flat ON COMMIT DROP AS
    SELECT
        p_matchID                              AS match_id,
        p.alias                                AS alias,
        p.team                                 AS team_name,
        (s->>'mapID')::int                     AS map_id,
        (s->>'sideID')::int                    AS side_id,
        (s->>'kills')::int                     AS kills,
        (s->>'deaths')::int                    AS deaths,
        (s->>'ADR')::numeric(5,2)              AS adr,
        (s->>'swingPct')::numeric(5,2)         AS swing_pct,
        (s->>'HLTVRating')::numeric(5,2)       AS hltv_rating,
        (s->>'HLTVRatingVersion')::text        AS hltv_rating_ver
    FROM (
        SELECT p_payload::jsonb AS j
    ) pld
    CROSS JOIN LATERAL jsonb_to_recordset(pld.j->'players') AS p(alias text, team text, stats jsonb)
    CROSS JOIN LATERAL jsonb_array_elements(p.stats) AS s;


    -- 2) Ensure Players exist
    INSERT INTO dbo.tblplayers (alias)
    SELECT DISTINCT f.alias
    FROM tmp_flat f
    WHERE NOT exists(SELECT 1 FROM dbo.tblplayers p WHERE p.alias = f.alias);

    -- 3) Insert match player records
    INSERT INTO dbo.tblmatchplayers (matchid, teamid, playerid)
    SELECT DISTINCT
        f.match_id,
        t.teamid,
        tp.playerid
    FROM tmp_flat f
    INNER JOIN dbo.tblTeams t ON t.teamname = f.team_name
    INNER JOIN tblplayers tp on tp.alias = f.alias
    WHERE NOT exists(SELECT 1 FROM tblmatchplayers tmp WHERE tmp.playerid = tp.playerid AND tmp.teamid = t.teamid AND tmp.matchid = f.match_id);

    -- 4) Insert HLTV player statlines
    INSERT INTO dbo.tblhltvplayerstats
    (matchmapid, playerid, sideid, kills, deaths, adr, swingpct, hltvrating, hltvratingversion)
    SELECT mm.matchmapid,
           pl.playerid,
           f.side_id,
           f.kills,
           f.deaths,
           f.adr,
           f.swing_pct,
           f.hltv_rating,
           f.hltv_rating_ver
    FROM tmp_flat f
             INNER JOIN dbo.tblteams t ON t.teamname = f.team_name
             INNER JOIN dbo.tblPlayers pl ON pl.alias = f.alias
             INNER JOIN dbo.tblMatchMaps mm ON mm.matchid = f.match_id
        AND mm.MapID = f.map_id
    WHERE NOT EXISTS(SELECT 1
                     FROM dbo.tblhltvplayerstats thps
                     WHERE thps.matchmapid = mm.matchmapid
                       AND thps.playerid = pl.playerid
                       AND thps.sideid = f.side_id);


END $$;


--
-- Name: udf_insert_match_veto(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_insert_match_veto(p_payload jsonb, p_matchid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
    DELETE FROM dbo.tblmatchveto mv WHERE mv.matchid = p_matchid;

    WITH payload AS (SELECT p_payload AS j),
    ins AS (
        INSERT INTO dbo.tblmatchveto
          (matchid, stepnumber, teamid, vetoactionid, mapid)
        SELECT
            p_matchid,
            (e.elem->>'stepNumber')::int,
            tt.teamid,
            (e.elem->>'vetoActionID')::int,
            (e.elem->>'mapID')::int
        FROM payload p
        CROSS JOIN LATERAL jsonb_array_elements(p.j->'matchVeto') AS e(elem)
        LEFT JOIN tblteams tt on tt.teamname = e.elem->>'teamName'
        ORDER BY (e.elem->>'stepNumber')::int

        RETURNING 1
    )
    INSERT INTO dbo.tblmatchmaps (matchid, mapid)
    SELECT DISTINCT
        p_matchid,
        (e.elem->>'mapID')::int
    FROM payload p
    CROSS JOIN LATERAL jsonb_array_elements(p.j->'matchVeto') AS e(elem)
    WHERE (e.elem->>'vetoActionID')::int IN (1,3)  -- picks + leftover
    AND NOT EXISTS(SELECT 1 FROM tblmatchmaps mm WHERE mm.matchid = p_matchid and mm.mapid = (e.elem->>'mapID')::int);
END $$;


--
-- Name: udf_insert_matchpage_match_data(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_insert_matchpage_match_data(p_payload jsonb, p_matchid integer) RETURNS void
    LANGUAGE sql
    AS $$
    UPDATE dbo.tblMatches AS m
    SET matchdate = NULLIF(p_payload->>'matchDate','')::timestamptz,
        matchnotes = p_payload->>'matchNotes',
        demolink = COALESCE(p_payload->>'demoLink', 'ERROR')
    WHERE m.matchid = p_matchID;
$$;


--
-- Name: udf_set_match_results(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: -
--

CREATE FUNCTION dbo.udf_set_match_results(p_payload jsonb, p_matchid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN

    CREATE TEMP TABLE tmp_flat_res ON COMMIT DROP AS
    SELECT
        p_matchID       AS match_id,
        r."mapID"         AS mapID,
        r."team1Score"    AS team1Score,
        r."team2Score"    AS team2Score,
        r."team1TScore"   AS team1TScore,
        r."team1CTScore"  AS team1CTScore,
        r."team2TScore"   AS team2TScore,
        r."team2CTScore"  AS team2CTScore
    FROM (
        SELECT p_payload::jsonb AS j
    ) pld
    CROSS JOIN LATERAL jsonb_to_recordset(pld.j->'results') AS r
    (
        "mapID" int,
        "team1Score" int,
        "team2Score" int,
        "team1TScore" int,
        "team1CTScore" int,
        "team2TScore" int,
        "team2CTScore" int
    );

    UPDATE tblmatchmaps as t
    SET team1score = tf.team1Score,
        team2score = tf.team2Score,
        team1ctscore = tf.team1CTScore,
        team1tscore = tf.team1TScore,
        team2ctscore = tf.team2CTScore,
        team2tscore = tf.team2TScore
    FROM tmp_flat_res tf WHERE tf.mapID = t.mapid AND tf.match_id = t.matchid;

END $$;


--
-- Name: usp_insert_event(text, text, timestamp with time zone, timestamp with time zone, text, text, text); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_insert_event(IN p_eventname text, IN p_prizepool text, IN p_startdate timestamp with time zone, IN p_enddate timestamp with time zone, IN p_eventtypename text, IN p_locationname text, IN p_hltvurl text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_eventTypeID INT;
    v_locationID INT;
BEGIN
    -- Upsert EventType
    INSERT INTO dbo.tblEventTypes(EventTypeName)
    VALUES (p_eventTypeName)
    ON CONFLICT (EventTypeName) DO NOTHING;

    SELECT EventTypeID INTO v_eventTypeID
    FROM dbo.tblEventTypes
    WHERE EventTypeName = p_eventTypeName;

    -- Upsert Location
    INSERT INTO dbo.tblLocations(LocationName)
    VALUES (p_locationName)
    ON CONFLICT (LocationName) DO NOTHING;

    SELECT LocationID INTO v_locationID
    FROM dbo.tblLocations
    WHERE LocationName = p_locationName;

    -- Insert Event (skip if already exists via URL)
    INSERT INTO dbo.tblEvents (
        EventName, PrizePool, StartDate, EndDate,
        EventTypeID, LocationID, HLTVUrl
    )
    VALUES (
        p_eventName, p_prizePool, p_startDate, p_endDate,
        v_eventTypeID, v_locationID, p_hltvUrl
    )
    ON CONFLICT (HLTVUrl) DO NOTHING;
END;
$$;


--
-- Name: usp_insert_event_teams(integer, text[]); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_insert_event_teams(IN p_eventid integer, IN p_teams text[])
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_teamname TEXT;
    v_teamid INT;
BEGIN

    FOREACH v_teamname IN ARRAY p_teams
    LOOP
        RAISE NOTICE 'inserting team % into event %', v_teamname, p_eventid;
        -- Get or insert the team
        SELECT teamid
        INTO v_teamid
        FROM tblTeams
        WHERE lower(teamname) = lower(v_teamname)
        LIMIT 1;

        IF v_teamid IS NULL THEN
            INSERT INTO tblTeams (teamname)
            VALUES (v_teamname)
            RETURNING teamid INTO v_teamid;
        END IF;

        -- Insert linking record
        INSERT INTO tblEventTeams (eventid, teamid)
        SELECT p_eventid, v_teamid
        WHERE NOT EXISTS (
            SELECT 1
            FROM tblEventTeams et
            WHERE et.eventid = p_eventid
              AND et.teamid = v_teamid
        );
    END LOOP;
END;
$$;


--
-- Name: usp_insert_match(integer, text, text, text, integer); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_insert_match(IN p_eventid integer, IN p_team1name text, IN p_team2name text, IN p_hltmatchurl text, IN p_bestof integer)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_team1ID INT;
    v_team2ID INT;
BEGIN

    -- Insert team if it somehow doesn't exist yet
    INSERT INTO dbo.tblTeams (teamname)
    VALUES (p_team1Name), (p_team2Name)
    ON CONFLICT (TeamName) DO NOTHING;

    -- Get team IDs
    SELECT TeamID INTO v_team1ID
    FROM dbo.tblTeams
    WHERE TeamName = p_team1Name;

    SELECT TeamID INTO v_team2ID
    FROM dbo.tblTeams
    WHERE TeamName = p_team2Name;

    INSERT INTO dbo.tblmatches
    (eventid, team1id, team2id, bestof, hltvmatchpageurl)
    VALUES
    (p_eventid, v_team1ID, v_team2ID, p_bestOf, p_hltMatchURL);

END;
$$;


--
-- Name: usp_insert_matchpage_data_from_json(jsonb); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_insert_matchpage_data_from_json(IN p_payload jsonb)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_match_id int := (p_payload->>'matchID')::int;
BEGIN

    PERFORM dbo.udf_insert_matchpage_match_data(p_payload, v_match_id);
    PERFORM dbo.udf_insert_match_veto(p_payload, v_match_id);
    PERFORM dbo.udf_set_match_results(p_payload, v_match_id);
    PERFORM dbo.udf_insert_match_playerdata(p_payload, v_match_id);

EXCEPTION WHEN OTHERS THEN
    RAISE;
END $$;


--
-- Name: usp_insert_team_ranking(text, integer, integer, integer, integer, timestamp without time zone); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_insert_team_ranking(IN p_teamname text, IN p_hltvpoints integer, IN p_hltvrank integer, IN p_vrspoints integer, IN p_vrsrank integer, IN p_rankingdate timestamp without time zone DEFAULT NULL::timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_teamID INTEGER;
    v_rankingDate TIMESTAMP;
BEGIN
    -- current timestamp if null date
    v_rankingDate := COALESCE(p_rankingDate, CURRENT_TIMESTAMP);

    -- Insert team if it doesn't exist
    INSERT INTO dbo.tblTeams (TeamName)
    VALUES (p_teamName)
    ON CONFLICT (TeamName) DO NOTHING;

    -- Get team ID
    SELECT TeamID INTO v_teamID
    FROM dbo.tblTeams
    WHERE TeamName = p_teamName;

    -- Insert team ranking snapshot
    INSERT INTO dbo.tblTeamRankings (TeamID, HLTVPoints, HLTVRank, VRSPoints, VRSRank, RankingDate)
    VALUES (v_teamID, p_HLTVPoints, p_HLTVRank, p_VRSPoints, p_VRSRank, v_rankingDate);
END;
$$;


--
-- Name: usp_mark_events_for_download(); Type: PROCEDURE; Schema: dbo; Owner: -
--

CREATE PROCEDURE dbo.usp_mark_events_for_download()
    LANGUAGE plpgsql
    AS $$
BEGIN

    UPDATE dbo.tblevents te
    SET downloadevent = true
    WHERE EXISTS (
        SELECT 1
        FROM dbo.tbleventteams et
        WHERE et.eventid = te.eventid
          AND (
                SELECT tr.hltvrank
                FROM dbo.tblteamrankings tr
                WHERE tr.teamid = et.teamid
                  AND tr.rankingdate <= te.startdate
                ORDER BY tr.rankingdate DESC
                LIMIT 1
              ) <= 10
    )
    AND te.downloadevent IS NULL;
    
    RAISE NOTICE 'Marked % events for download', FOUND;

END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: tbldemoconversionjobs; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbldemoconversionjobs (
    democonversionjobid integer NOT NULL,
    demodownloadjobid integer NOT NULL,
    extractedfolderrelativepath text NOT NULL,
    parquettempfolderrelativepath text,
    status dbo.demo_conversion_status DEFAULT 'ReadyToConvert'::dbo.demo_conversion_status NOT NULL,
    attemptcount integer DEFAULT 0 NOT NULL,
    errormessage text,
    createdat timestamp without time zone DEFAULT now() NOT NULL,
    startedat timestamp without time zone,
    completedat timestamp without time zone,
    updatedat timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tbldemoconversionjobs_democonversionjobid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbldemoconversionjobs_democonversionjobid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbldemoconversionjobs_democonversionjobid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbldemoconversionjobs_democonversionjobid_seq OWNED BY dbo.tbldemoconversionjobs.democonversionjobid;


--
-- Name: tbldemodownloadjobs; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbldemodownloadjobs (
    demodownloadjobid integer NOT NULL,
    matchid integer NOT NULL,
    demolink text NOT NULL,
    status dbo.demo_download_status DEFAULT 'PendingDownload'::dbo.demo_download_status NOT NULL,
    archiverelativepath text,
    attemptcount integer DEFAULT 0 NOT NULL,
    errormessage text,
    createdat timestamp without time zone DEFAULT now() NOT NULL,
    startedat timestamp without time zone,
    completedat timestamp without time zone,
    updatedat timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tbldemodownloadjobs_demodownloadjobid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbldemodownloadjobs_demodownloadjobid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbldemodownloadjobs_demodownloadjobid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbldemodownloadjobs_demodownloadjobid_seq OWNED BY dbo.tbldemodownloadjobs.demodownloadjobid;


--
-- Name: tbldemoparquetfiles; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbldemoparquetfiles (
    demoparquetfileid integer NOT NULL,
    democonversionjobid integer NOT NULL,
    matchmapid integer,
    parquettemprelativepath text,
    parquetfinalrelativepath text,
    status dbo.parquet_file_status DEFAULT 'Created'::dbo.parquet_file_status NOT NULL,
    attemptcount integer DEFAULT 0 NOT NULL,
    errormessage text,
    createdat timestamp without time zone DEFAULT now() NOT NULL,
    startedat timestamp without time zone,
    completedat timestamp without time zone,
    updatedat timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tbldemoparquetfiles_demoparquetfileid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbldemoparquetfiles_demoparquetfileid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbldemoparquetfiles_demoparquetfileid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbldemoparquetfiles_demoparquetfileid_seq OWNED BY dbo.tbldemoparquetfiles.demoparquetfileid;


--
-- Name: tbldemopipelinelogs; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbldemopipelinelogs (
    pipelinestagelogid integer NOT NULL,
    entitytype dbo.pipeline_entity_type NOT NULL,
    entityid integer NOT NULL,
    stagename text NOT NULL,
    status dbo.pipeline_stage_status NOT NULL,
    startedat timestamp without time zone DEFAULT now() NOT NULL,
    completedat timestamp without time zone,
    exitcode integer,
    errormessage text
);


--
-- Name: tbldemopipelinelogs_pipelinestagelogid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbldemopipelinelogs_pipelinestagelogid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbldemopipelinelogs_pipelinestagelogid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbldemopipelinelogs_pipelinestagelogid_seq OWNED BY dbo.tbldemopipelinelogs.pipelinestagelogid;


--
-- Name: tblevents; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblevents (
    eventid integer NOT NULL,
    eventname text NOT NULL,
    prizepool text,
    startdate timestamp with time zone,
    enddate timestamp with time zone,
    eventtypeid integer,
    locationid integer,
    hltvurl text,
    downloadevent boolean
);


--
-- Name: tblevents_eventid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblevents_eventid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblevents_eventid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblevents_eventid_seq OWNED BY dbo.tblevents.eventid;


--
-- Name: tbleventteams; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbleventteams (
    eventteamid integer NOT NULL,
    eventid integer NOT NULL,
    teamid integer NOT NULL
);


--
-- Name: tbleventteams_eventteamid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbleventteams_eventteamid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbleventteams_eventteamid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbleventteams_eventteamid_seq OWNED BY dbo.tbleventteams.eventteamid;


--
-- Name: tbleventtypes; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbleventtypes (
    eventtypeid integer NOT NULL,
    eventtypename text NOT NULL
);


--
-- Name: tbleventtypes_eventtypeid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbleventtypes_eventtypeid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbleventtypes_eventtypeid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbleventtypes_eventtypeid_seq OWNED BY dbo.tbleventtypes.eventtypeid;


--
-- Name: tblhltvplayerstats; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblhltvplayerstats (
    hltvplayerstatsid integer NOT NULL,
    matchmapid integer NOT NULL,
    playerid integer NOT NULL,
    sideid integer NOT NULL,
    kills integer NOT NULL,
    deaths integer NOT NULL,
    adr numeric(5,2),
    swingpct numeric(5,2),
    hltvrating numeric(5,2),
    hltvratingversion text
);


--
-- Name: tblhltvplayerstats_hltvplayerstatsid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblhltvplayerstats_hltvplayerstatsid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblhltvplayerstats_hltvplayerstatsid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblhltvplayerstats_hltvplayerstatsid_seq OWNED BY dbo.tblhltvplayerstats.hltvplayerstatsid;


--
-- Name: tbllocations; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tbllocations (
    locationid integer NOT NULL,
    locationname text NOT NULL
);


--
-- Name: tbllocations_locationid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tbllocations_locationid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tbllocations_locationid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tbllocations_locationid_seq OWNED BY dbo.tbllocations.locationid;


--
-- Name: tblmaps; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblmaps (
    mapid integer NOT NULL,
    mapname text
);


--
-- Name: tblmaps_mapid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblmaps_mapid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblmaps_mapid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblmaps_mapid_seq OWNED BY dbo.tblmaps.mapid;


--
-- Name: tblmatches; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblmatches (
    matchid integer NOT NULL,
    eventid integer,
    team1id integer,
    team2id integer,
    bestof integer,
    matchdate timestamp without time zone,
    hltvmatchpageurl text,
    matchnotes text,
    demolink text
);


--
-- Name: tblmatches_matchid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblmatches_matchid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblmatches_matchid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblmatches_matchid_seq OWNED BY dbo.tblmatches.matchid;


--
-- Name: tblmatchmaps; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblmatchmaps (
    matchmapid integer NOT NULL,
    matchid integer,
    mapid integer,
    team1score integer,
    team2score integer,
    team1tscore integer,
    team1ctscore integer,
    team2tscore integer,
    team2ctscore integer
);


--
-- Name: tblmatchmaps_matchmapid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblmatchmaps_matchmapid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblmatchmaps_matchmapid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblmatchmaps_matchmapid_seq OWNED BY dbo.tblmatchmaps.matchmapid;


--
-- Name: tblmatchplayers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblmatchplayers (
    matchid integer,
    teamid integer,
    playerid integer
);


--
-- Name: tblmatchveto; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblmatchveto (
    matchvetoid integer NOT NULL,
    matchid integer,
    stepnumber integer,
    teamid integer,
    vetoactionid integer,
    mapid integer
);


--
-- Name: tblmatchveto_matchvetoid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblmatchveto_matchvetoid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblmatchveto_matchvetoid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblmatchveto_matchvetoid_seq OWNED BY dbo.tblmatchveto.matchvetoid;


--
-- Name: tblplayers; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblplayers (
    playerid integer NOT NULL,
    alias text,
    steamid text,
    fullname text
);


--
-- Name: tblplayers_playerid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblplayers_playerid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblplayers_playerid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblplayers_playerid_seq OWNED BY dbo.tblplayers.playerid;


--
-- Name: tblteamrankings; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblteamrankings (
    teamrankingid integer NOT NULL,
    teamid integer NOT NULL,
    hltvpoints integer,
    hltvrank integer,
    vrspoints integer,
    vrsrank integer,
    rankingdate timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: tblteamrankings_teamrankingid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblteamrankings_teamrankingid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblteamrankings_teamrankingid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblteamrankings_teamrankingid_seq OWNED BY dbo.tblteamrankings.teamrankingid;


--
-- Name: tblteams; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblteams (
    teamid integer NOT NULL,
    teamname text NOT NULL
);


--
-- Name: tblteams_teamid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblteams_teamid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblteams_teamid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblteams_teamid_seq OWNED BY dbo.tblteams.teamid;


--
-- Name: tblvetoactions; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblvetoactions (
    vetoactionid integer NOT NULL,
    vetoaction text
);


--
-- Name: tblvetoactions_vetoactionid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblvetoactions_vetoactionid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblvetoactions_vetoactionid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblvetoactions_vetoactionid_seq OWNED BY dbo.tblvetoactions.vetoactionid;


--
-- Name: tblworkerconfig; Type: TABLE; Schema: dbo; Owner: -
--

CREATE TABLE dbo.tblworkerconfig (
    workerconfigid integer NOT NULL,
    workername text NOT NULL,
    enabled boolean DEFAULT false NOT NULL
);


--
-- Name: tblworkerconfig_workerconfigid_seq; Type: SEQUENCE; Schema: dbo; Owner: -
--

CREATE SEQUENCE dbo.tblworkerconfig_workerconfigid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tblworkerconfig_workerconfigid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: -
--

ALTER SEQUENCE dbo.tblworkerconfig_workerconfigid_seq OWNED BY dbo.tblworkerconfig.workerconfigid;


--
-- Name: tbldemoconversionjobs democonversionjobid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemoconversionjobs ALTER COLUMN democonversionjobid SET DEFAULT nextval('dbo.tbldemoconversionjobs_democonversionjobid_seq'::regclass);


--
-- Name: tbldemodownloadjobs demodownloadjobid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemodownloadjobs ALTER COLUMN demodownloadjobid SET DEFAULT nextval('dbo.tbldemodownloadjobs_demodownloadjobid_seq'::regclass);


--
-- Name: tbldemoparquetfiles demoparquetfileid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemoparquetfiles ALTER COLUMN demoparquetfileid SET DEFAULT nextval('dbo.tbldemoparquetfiles_demoparquetfileid_seq'::regclass);


--
-- Name: tbldemopipelinelogs pipelinestagelogid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemopipelinelogs ALTER COLUMN pipelinestagelogid SET DEFAULT nextval('dbo.tbldemopipelinelogs_pipelinestagelogid_seq'::regclass);


--
-- Name: tblevents eventid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblevents ALTER COLUMN eventid SET DEFAULT nextval('dbo.tblevents_eventid_seq'::regclass);


--
-- Name: tbleventteams eventteamid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbleventteams ALTER COLUMN eventteamid SET DEFAULT nextval('dbo.tbleventteams_eventteamid_seq'::regclass);


--
-- Name: tbleventtypes eventtypeid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbleventtypes ALTER COLUMN eventtypeid SET DEFAULT nextval('dbo.tbleventtypes_eventtypeid_seq'::regclass);


--
-- Name: tblhltvplayerstats hltvplayerstatsid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblhltvplayerstats ALTER COLUMN hltvplayerstatsid SET DEFAULT nextval('dbo.tblhltvplayerstats_hltvplayerstatsid_seq'::regclass);


--
-- Name: tbllocations locationid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbllocations ALTER COLUMN locationid SET DEFAULT nextval('dbo.tbllocations_locationid_seq'::regclass);


--
-- Name: tblmaps mapid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmaps ALTER COLUMN mapid SET DEFAULT nextval('dbo.tblmaps_mapid_seq'::regclass);


--
-- Name: tblmatches matchid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatches ALTER COLUMN matchid SET DEFAULT nextval('dbo.tblmatches_matchid_seq'::regclass);


--
-- Name: tblmatchmaps matchmapid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatchmaps ALTER COLUMN matchmapid SET DEFAULT nextval('dbo.tblmatchmaps_matchmapid_seq'::regclass);


--
-- Name: tblmatchveto matchvetoid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatchveto ALTER COLUMN matchvetoid SET DEFAULT nextval('dbo.tblmatchveto_matchvetoid_seq'::regclass);


--
-- Name: tblplayers playerid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblplayers ALTER COLUMN playerid SET DEFAULT nextval('dbo.tblplayers_playerid_seq'::regclass);


--
-- Name: tblteamrankings teamrankingid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblteamrankings ALTER COLUMN teamrankingid SET DEFAULT nextval('dbo.tblteamrankings_teamrankingid_seq'::regclass);


--
-- Name: tblteams teamid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblteams ALTER COLUMN teamid SET DEFAULT nextval('dbo.tblteams_teamid_seq'::regclass);


--
-- Name: tblvetoactions vetoactionid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblvetoactions ALTER COLUMN vetoactionid SET DEFAULT nextval('dbo.tblvetoactions_vetoactionid_seq'::regclass);


--
-- Name: tblworkerconfig workerconfigid; Type: DEFAULT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblworkerconfig ALTER COLUMN workerconfigid SET DEFAULT nextval('dbo.tblworkerconfig_workerconfigid_seq'::regclass);


--
-- Name: tbldemoconversionjobs tbldemoconversionjobs_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemoconversionjobs
    ADD CONSTRAINT tbldemoconversionjobs_pkey PRIMARY KEY (democonversionjobid);


--
-- Name: tbldemodownloadjobs tbldemodownloadjobs_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemodownloadjobs
    ADD CONSTRAINT tbldemodownloadjobs_pkey PRIMARY KEY (demodownloadjobid);


--
-- Name: tbldemoparquetfiles tbldemoparquetfiles_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemoparquetfiles
    ADD CONSTRAINT tbldemoparquetfiles_pkey PRIMARY KEY (demoparquetfileid);


--
-- Name: tbldemopipelinelogs tbldemopipelinelogs_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbldemopipelinelogs
    ADD CONSTRAINT tbldemopipelinelogs_pkey PRIMARY KEY (pipelinestagelogid);


--
-- Name: tblevents tblevents_hltvurl_key; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_hltvurl_key UNIQUE (hltvurl);


--
-- Name: tblevents tblevents_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_pkey PRIMARY KEY (eventid);


--
-- Name: tbleventteams tbleventteams_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbleventteams
    ADD CONSTRAINT tbleventteams_pkey PRIMARY KEY (eventteamid);


--
-- Name: tbleventtypes tbleventtypes_eventtypename_key; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbleventtypes
    ADD CONSTRAINT tbleventtypes_eventtypename_key UNIQUE (eventtypename);


--
-- Name: tbleventtypes tbleventtypes_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbleventtypes
    ADD CONSTRAINT tbleventtypes_pkey PRIMARY KEY (eventtypeid);


--
-- Name: tblhltvplayerstats tblhltvplayerstats_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblhltvplayerstats
    ADD CONSTRAINT tblhltvplayerstats_pkey PRIMARY KEY (hltvplayerstatsid);


--
-- Name: tbllocations tbllocations_locationname_key; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbllocations
    ADD CONSTRAINT tbllocations_locationname_key UNIQUE (locationname);


--
-- Name: tbllocations tbllocations_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tbllocations
    ADD CONSTRAINT tbllocations_pkey PRIMARY KEY (locationid);


--
-- Name: tblmaps tblmaps_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmaps
    ADD CONSTRAINT tblmaps_pkey PRIMARY KEY (mapid);


--
-- Name: tblmatches tblmatches_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatches
    ADD CONSTRAINT tblmatches_pkey PRIMARY KEY (matchid);


--
-- Name: tblmatchmaps tblmatchmaps_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatchmaps
    ADD CONSTRAINT tblmatchmaps_pkey PRIMARY KEY (matchmapid);


--
-- Name: tblmatchveto tblmatchveto_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatchveto
    ADD CONSTRAINT tblmatchveto_pkey PRIMARY KEY (matchvetoid);


--
-- Name: tblplayers tblplayers_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblplayers
    ADD CONSTRAINT tblplayers_pkey PRIMARY KEY (playerid);


--
-- Name: tblteamrankings tblteamrankings_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblteamrankings
    ADD CONSTRAINT tblteamrankings_pkey PRIMARY KEY (teamrankingid);


--
-- Name: tblteams tblteams_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblteams
    ADD CONSTRAINT tblteams_pkey PRIMARY KEY (teamid);


--
-- Name: tblteams tblteams_teamname_key; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblteams
    ADD CONSTRAINT tblteams_teamname_key UNIQUE (teamname);


--
-- Name: tblvetoactions tblvetoactions_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblvetoactions
    ADD CONSTRAINT tblvetoactions_pkey PRIMARY KEY (vetoactionid);


--
-- Name: tblworkerconfig tblworkerconfig_pkey; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblworkerconfig
    ADD CONSTRAINT tblworkerconfig_pkey PRIMARY KEY (workerconfigid);


--
-- Name: tblmatchmaps uq_matchmaps_matchid_mapid; Type: CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblmatchmaps
    ADD CONSTRAINT uq_matchmaps_matchid_mapid UNIQUE (matchid, mapid);


--
-- Name: tblevents tblevents_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES dbo.tbleventtypes(eventtypeid);


--
-- Name: tblevents tblevents_locationid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: -
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_locationid_fkey FOREIGN KEY (locationid) REFERENCES dbo.tbllocations(locationid);


--
-- PostgreSQL database dump complete
--

\unrestrict ZG80D4TWDsL9EZuyoknZFybJnhz2jmvhxL5YsZ3aOmW2ebCy3RFORpsO0MVVi9v

