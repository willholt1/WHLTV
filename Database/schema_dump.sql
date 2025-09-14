--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Debian 16.9-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: dbo; Type: SCHEMA; Schema: -; Owner: whltv
--

CREATE SCHEMA dbo;


ALTER SCHEMA dbo OWNER TO whltv;

--
-- Name: udf_get_high_value_events(); Type: FUNCTION; Schema: dbo; Owner: whltv
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


ALTER FUNCTION dbo.udf_get_high_value_events() OWNER TO whltv;

--
-- Name: udf_get_match_pages(); Type: FUNCTION; Schema: dbo; Owner: whltv
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


ALTER FUNCTION dbo.udf_get_match_pages() OWNER TO whltv;

--
-- Name: udf_get_results_pages(); Type: FUNCTION; Schema: dbo; Owner: whltv
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
    FROM tblevents te
    WHERE te.downloadevent = true
    AND NOT exists(SELECT 1 FROM tblmatches tm WHERE tm.eventid = te.eventid);
END;
$_$;


ALTER FUNCTION dbo.udf_get_results_pages() OWNER TO whltv;

--
-- Name: udf_insert_match_playerdata(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: whltv
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


ALTER FUNCTION dbo.udf_insert_match_playerdata(p_payload jsonb, p_matchid integer) OWNER TO whltv;

--
-- Name: udf_insert_match_veto(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: whltv
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


ALTER FUNCTION dbo.udf_insert_match_veto(p_payload jsonb, p_matchid integer) OWNER TO whltv;

--
-- Name: udf_insert_matchpage_match_data(jsonb, integer); Type: FUNCTION; Schema: dbo; Owner: whltv
--

CREATE FUNCTION dbo.udf_insert_matchpage_match_data(p_payload jsonb, p_matchid integer) RETURNS void
    LANGUAGE sql
    AS $$
    UPDATE dbo.tblMatches AS m
    SET matchdate = NULLIF(p_payload->>'matchDate','')::timestamptz,
        matchnotes = p_payload->>'matchNotes',
        demolink = p_payload->>'demoLink'
    WHERE m.matchid = p_matchID;
$$;


ALTER FUNCTION dbo.udf_insert_matchpage_match_data(p_payload jsonb, p_matchid integer) OWNER TO whltv;

--
-- Name: usp_insert_event(text, text, timestamp with time zone, timestamp with time zone, text, text, text); Type: PROCEDURE; Schema: dbo; Owner: whltv
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


ALTER PROCEDURE dbo.usp_insert_event(IN p_eventname text, IN p_prizepool text, IN p_startdate timestamp with time zone, IN p_enddate timestamp with time zone, IN p_eventtypename text, IN p_locationname text, IN p_hltvurl text) OWNER TO whltv;

--
-- Name: usp_insert_event_teams(integer, text[]); Type: PROCEDURE; Schema: dbo; Owner: whltv
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


ALTER PROCEDURE dbo.usp_insert_event_teams(IN p_eventid integer, IN p_teams text[]) OWNER TO whltv;

--
-- Name: usp_insert_match(integer, text, text, text, integer); Type: PROCEDURE; Schema: dbo; Owner: whltv
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


ALTER PROCEDURE dbo.usp_insert_match(IN p_eventid integer, IN p_team1name text, IN p_team2name text, IN p_hltmatchurl text, IN p_bestof integer) OWNER TO whltv;

--
-- Name: usp_insert_matchpage_data_from_json(jsonb); Type: PROCEDURE; Schema: dbo; Owner: whltv
--

CREATE PROCEDURE dbo.usp_insert_matchpage_data_from_json(IN p_payload jsonb)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_match_id int := (p_payload->>'matchID')::int;
BEGIN

    PERFORM dbo.udf_insert_matchpage_match_data(p_payload, v_match_id);  
    PERFORM dbo.udf_insert_match_veto(p_payload, v_match_id);    
    PERFORM dbo.udf_insert_match_playerdata(p_payload, v_match_id);

EXCEPTION WHEN OTHERS THEN
    RAISE;
END $$;


ALTER PROCEDURE dbo.usp_insert_matchpage_data_from_json(IN p_payload jsonb) OWNER TO whltv;

--
-- Name: usp_insert_team_ranking(text, integer, integer, integer, integer, timestamp without time zone); Type: PROCEDURE; Schema: dbo; Owner: whltv
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


ALTER PROCEDURE dbo.usp_insert_team_ranking(IN p_teamname text, IN p_hltvpoints integer, IN p_hltvrank integer, IN p_vrspoints integer, IN p_vrsrank integer, IN p_rankingdate timestamp without time zone) OWNER TO whltv;

--
-- Name: usp_mark_events_for_download(); Type: PROCEDURE; Schema: dbo; Owner: whltv
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


ALTER PROCEDURE dbo.usp_mark_events_for_download() OWNER TO whltv;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: tbldemos; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tbldemos (
    demoid integer NOT NULL,
    filepath text NOT NULL
);


ALTER TABLE dbo.tbldemos OWNER TO whltv;

--
-- Name: tbldemos_demoid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tbldemos_demoid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tbldemos_demoid_seq OWNER TO whltv;

--
-- Name: tbldemos_demoid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tbldemos_demoid_seq OWNED BY dbo.tbldemos.demoid;


--
-- Name: tblevents; Type: TABLE; Schema: dbo; Owner: whltv
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


ALTER TABLE dbo.tblevents OWNER TO whltv;

--
-- Name: tblevents_eventid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblevents_eventid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblevents_eventid_seq OWNER TO whltv;

--
-- Name: tblevents_eventid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblevents_eventid_seq OWNED BY dbo.tblevents.eventid;


--
-- Name: tbleventteams; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tbleventteams (
    eventteamid integer NOT NULL,
    eventid integer NOT NULL,
    teamid integer NOT NULL
);


ALTER TABLE dbo.tbleventteams OWNER TO whltv;

--
-- Name: tbleventteams_eventteamid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tbleventteams_eventteamid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tbleventteams_eventteamid_seq OWNER TO whltv;

--
-- Name: tbleventteams_eventteamid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tbleventteams_eventteamid_seq OWNED BY dbo.tbleventteams.eventteamid;


--
-- Name: tbleventtypes; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tbleventtypes (
    eventtypeid integer NOT NULL,
    eventtypename text NOT NULL
);


ALTER TABLE dbo.tbleventtypes OWNER TO whltv;

--
-- Name: tbleventtypes_eventtypeid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tbleventtypes_eventtypeid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tbleventtypes_eventtypeid_seq OWNER TO whltv;

--
-- Name: tbleventtypes_eventtypeid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tbleventtypes_eventtypeid_seq OWNED BY dbo.tbleventtypes.eventtypeid;


--
-- Name: tblhltvplayerstats; Type: TABLE; Schema: dbo; Owner: whltv
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


ALTER TABLE dbo.tblhltvplayerstats OWNER TO whltv;

--
-- Name: tblhltvplayerstats_hltvplayerstatsid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblhltvplayerstats_hltvplayerstatsid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblhltvplayerstats_hltvplayerstatsid_seq OWNER TO whltv;

--
-- Name: tblhltvplayerstats_hltvplayerstatsid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblhltvplayerstats_hltvplayerstatsid_seq OWNED BY dbo.tblhltvplayerstats.hltvplayerstatsid;


--
-- Name: tbllocations; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tbllocations (
    locationid integer NOT NULL,
    locationname text NOT NULL
);


ALTER TABLE dbo.tbllocations OWNER TO whltv;

--
-- Name: tbllocations_locationid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tbllocations_locationid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tbllocations_locationid_seq OWNER TO whltv;

--
-- Name: tbllocations_locationid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tbllocations_locationid_seq OWNED BY dbo.tbllocations.locationid;


--
-- Name: tblmaps; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblmaps (
    mapid integer NOT NULL,
    mapname text
);


ALTER TABLE dbo.tblmaps OWNER TO whltv;

--
-- Name: tblmaps_mapid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblmaps_mapid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblmaps_mapid_seq OWNER TO whltv;

--
-- Name: tblmaps_mapid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblmaps_mapid_seq OWNED BY dbo.tblmaps.mapid;


--
-- Name: tblmatches; Type: TABLE; Schema: dbo; Owner: whltv
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


ALTER TABLE dbo.tblmatches OWNER TO whltv;

--
-- Name: tblmatches_matchid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblmatches_matchid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblmatches_matchid_seq OWNER TO whltv;

--
-- Name: tblmatches_matchid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblmatches_matchid_seq OWNED BY dbo.tblmatches.matchid;


--
-- Name: tblmatchmapdemos; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblmatchmapdemos (
    matchmapid integer,
    demoid integer
);


ALTER TABLE dbo.tblmatchmapdemos OWNER TO whltv;

--
-- Name: tblmatchmaps; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblmatchmaps (
    matchmapid integer NOT NULL,
    matchid integer,
    mapid integer,
    team1score integer,
    team2score integer
);


ALTER TABLE dbo.tblmatchmaps OWNER TO whltv;

--
-- Name: tblmatchmaps_matchmapid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblmatchmaps_matchmapid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblmatchmaps_matchmapid_seq OWNER TO whltv;

--
-- Name: tblmatchmaps_matchmapid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblmatchmaps_matchmapid_seq OWNED BY dbo.tblmatchmaps.matchmapid;


--
-- Name: tblmatchplayers; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblmatchplayers (
    matchid integer,
    teamid integer,
    playerid integer
);


ALTER TABLE dbo.tblmatchplayers OWNER TO whltv;

--
-- Name: tblmatchveto; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblmatchveto (
    matchvetoid integer NOT NULL,
    matchid integer,
    stepnumber integer,
    teamid integer,
    vetoactionid integer,
    mapid integer
);


ALTER TABLE dbo.tblmatchveto OWNER TO whltv;

--
-- Name: tblmatchveto_matchvetoid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblmatchveto_matchvetoid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblmatchveto_matchvetoid_seq OWNER TO whltv;

--
-- Name: tblmatchveto_matchvetoid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblmatchveto_matchvetoid_seq OWNED BY dbo.tblmatchveto.matchvetoid;


--
-- Name: tblplayers; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblplayers (
    playerid integer NOT NULL,
    alias text,
    steamid text,
    fullname text
);


ALTER TABLE dbo.tblplayers OWNER TO whltv;

--
-- Name: tblplayers_playerid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblplayers_playerid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblplayers_playerid_seq OWNER TO whltv;

--
-- Name: tblplayers_playerid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblplayers_playerid_seq OWNED BY dbo.tblplayers.playerid;


--
-- Name: tblteamrankings; Type: TABLE; Schema: dbo; Owner: whltv
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


ALTER TABLE dbo.tblteamrankings OWNER TO whltv;

--
-- Name: tblteamrankings_teamrankingid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblteamrankings_teamrankingid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblteamrankings_teamrankingid_seq OWNER TO whltv;

--
-- Name: tblteamrankings_teamrankingid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblteamrankings_teamrankingid_seq OWNED BY dbo.tblteamrankings.teamrankingid;


--
-- Name: tblteams; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblteams (
    teamid integer NOT NULL,
    teamname text NOT NULL
);


ALTER TABLE dbo.tblteams OWNER TO whltv;

--
-- Name: tblteams_teamid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblteams_teamid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblteams_teamid_seq OWNER TO whltv;

--
-- Name: tblteams_teamid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblteams_teamid_seq OWNED BY dbo.tblteams.teamid;


--
-- Name: tblvetoactions; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tblvetoactions (
    vetoactionid integer NOT NULL,
    vetoaction text
);


ALTER TABLE dbo.tblvetoactions OWNER TO whltv;

--
-- Name: tblvetoactions_vetoactionid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tblvetoactions_vetoactionid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tblvetoactions_vetoactionid_seq OWNER TO whltv;

--
-- Name: tblvetoactions_vetoactionid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tblvetoactions_vetoactionid_seq OWNED BY dbo.tblvetoactions.vetoactionid;


--
-- Name: tbldemos demoid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbldemos ALTER COLUMN demoid SET DEFAULT nextval('dbo.tbldemos_demoid_seq'::regclass);


--
-- Name: tblevents eventid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents ALTER COLUMN eventid SET DEFAULT nextval('dbo.tblevents_eventid_seq'::regclass);


--
-- Name: tbleventteams eventteamid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventteams ALTER COLUMN eventteamid SET DEFAULT nextval('dbo.tbleventteams_eventteamid_seq'::regclass);


--
-- Name: tbleventtypes eventtypeid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventtypes ALTER COLUMN eventtypeid SET DEFAULT nextval('dbo.tbleventtypes_eventtypeid_seq'::regclass);


--
-- Name: tblhltvplayerstats hltvplayerstatsid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblhltvplayerstats ALTER COLUMN hltvplayerstatsid SET DEFAULT nextval('dbo.tblhltvplayerstats_hltvplayerstatsid_seq'::regclass);


--
-- Name: tbllocations locationid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbllocations ALTER COLUMN locationid SET DEFAULT nextval('dbo.tbllocations_locationid_seq'::regclass);


--
-- Name: tblmaps mapid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmaps ALTER COLUMN mapid SET DEFAULT nextval('dbo.tblmaps_mapid_seq'::regclass);


--
-- Name: tblmatches matchid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatches ALTER COLUMN matchid SET DEFAULT nextval('dbo.tblmatches_matchid_seq'::regclass);


--
-- Name: tblmatchmaps matchmapid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatchmaps ALTER COLUMN matchmapid SET DEFAULT nextval('dbo.tblmatchmaps_matchmapid_seq'::regclass);


--
-- Name: tblmatchveto matchvetoid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatchveto ALTER COLUMN matchvetoid SET DEFAULT nextval('dbo.tblmatchveto_matchvetoid_seq'::regclass);


--
-- Name: tblplayers playerid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblplayers ALTER COLUMN playerid SET DEFAULT nextval('dbo.tblplayers_playerid_seq'::regclass);


--
-- Name: tblteamrankings teamrankingid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteamrankings ALTER COLUMN teamrankingid SET DEFAULT nextval('dbo.tblteamrankings_teamrankingid_seq'::regclass);


--
-- Name: tblteams teamid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteams ALTER COLUMN teamid SET DEFAULT nextval('dbo.tblteams_teamid_seq'::regclass);


--
-- Name: tblvetoactions vetoactionid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblvetoactions ALTER COLUMN vetoactionid SET DEFAULT nextval('dbo.tblvetoactions_vetoactionid_seq'::regclass);


--
-- Name: tbldemos tbldemos_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbldemos
    ADD CONSTRAINT tbldemos_pkey PRIMARY KEY (demoid);


--
-- Name: tblevents tblevents_hltvurl_key; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_hltvurl_key UNIQUE (hltvurl);


--
-- Name: tblevents tblevents_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_pkey PRIMARY KEY (eventid);


--
-- Name: tbleventteams tbleventteams_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventteams
    ADD CONSTRAINT tbleventteams_pkey PRIMARY KEY (eventteamid);


--
-- Name: tbleventtypes tbleventtypes_eventtypename_key; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventtypes
    ADD CONSTRAINT tbleventtypes_eventtypename_key UNIQUE (eventtypename);


--
-- Name: tbleventtypes tbleventtypes_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventtypes
    ADD CONSTRAINT tbleventtypes_pkey PRIMARY KEY (eventtypeid);


--
-- Name: tblhltvplayerstats tblhltvplayerstats_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblhltvplayerstats
    ADD CONSTRAINT tblhltvplayerstats_pkey PRIMARY KEY (hltvplayerstatsid);


--
-- Name: tbllocations tbllocations_locationname_key; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbllocations
    ADD CONSTRAINT tbllocations_locationname_key UNIQUE (locationname);


--
-- Name: tbllocations tbllocations_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbllocations
    ADD CONSTRAINT tbllocations_pkey PRIMARY KEY (locationid);


--
-- Name: tblmaps tblmaps_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmaps
    ADD CONSTRAINT tblmaps_pkey PRIMARY KEY (mapid);


--
-- Name: tblmatches tblmatches_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatches
    ADD CONSTRAINT tblmatches_pkey PRIMARY KEY (matchid);


--
-- Name: tblmatchmaps tblmatchmaps_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatchmaps
    ADD CONSTRAINT tblmatchmaps_pkey PRIMARY KEY (matchmapid);


--
-- Name: tblmatchveto tblmatchveto_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatchveto
    ADD CONSTRAINT tblmatchveto_pkey PRIMARY KEY (matchvetoid);


--
-- Name: tblplayers tblplayers_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblplayers
    ADD CONSTRAINT tblplayers_pkey PRIMARY KEY (playerid);


--
-- Name: tblteamrankings tblteamrankings_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteamrankings
    ADD CONSTRAINT tblteamrankings_pkey PRIMARY KEY (teamrankingid);


--
-- Name: tblteams tblteams_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteams
    ADD CONSTRAINT tblteams_pkey PRIMARY KEY (teamid);


--
-- Name: tblteams tblteams_teamname_key; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteams
    ADD CONSTRAINT tblteams_teamname_key UNIQUE (teamname);


--
-- Name: tblvetoactions tblvetoactions_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblvetoactions
    ADD CONSTRAINT tblvetoactions_pkey PRIMARY KEY (vetoactionid);


--
-- Name: tblmatchmaps uq_matchmaps_matchid_mapid; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblmatchmaps
    ADD CONSTRAINT uq_matchmaps_matchid_mapid UNIQUE (matchid, mapid);


--
-- Name: tblevents tblevents_eventtypeid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_eventtypeid_fkey FOREIGN KEY (eventtypeid) REFERENCES dbo.tbleventtypes(eventtypeid);


--
-- Name: tblevents tblevents_locationid_fkey; Type: FK CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents
    ADD CONSTRAINT tblevents_locationid_fkey FOREIGN KEY (locationid) REFERENCES dbo.tbllocations(locationid);


--
-- PostgreSQL database dump complete
--

