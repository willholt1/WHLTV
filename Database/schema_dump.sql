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
-- Name: usp_InsertTeamRanking(text, integer, integer, integer, integer, timestamp without time zone); Type: PROCEDURE; Schema: dbo; Owner: whltv
--

CREATE PROCEDURE dbo."usp_InsertTeamRanking"(IN p_teamname text, IN p_hltvpoints integer, IN p_hltvrank integer, IN p_vrspoints integer, IN p_vrsrank integer, IN p_rankingdate timestamp without time zone DEFAULT NULL::timestamp without time zone)
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


ALTER PROCEDURE dbo."usp_InsertTeamRanking"(IN p_teamname text, IN p_hltvpoints integer, IN p_hltvrank integer, IN p_vrspoints integer, IN p_vrsrank integer, IN p_rankingdate timestamp without time zone) OWNER TO whltv;

--
-- Name: usp_insertevent(text, text, timestamp with time zone, timestamp with time zone, text, text, text); Type: PROCEDURE; Schema: dbo; Owner: whltv
--

CREATE PROCEDURE dbo.usp_insertevent(IN p_eventname text, IN p_prizepool text, IN p_startdate timestamp with time zone, IN p_enddate timestamp with time zone, IN p_eventtypename text, IN p_locationname text, IN p_hltvurl text)
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


ALTER PROCEDURE dbo.usp_insertevent(IN p_eventname text, IN p_prizepool text, IN p_startdate timestamp with time zone, IN p_enddate timestamp with time zone, IN p_eventtypename text, IN p_locationname text, IN p_hltvurl text) OWNER TO whltv;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: tbldemofiles; Type: TABLE; Schema: dbo; Owner: whltv
--

CREATE TABLE dbo.tbldemofiles (
    demofileid integer NOT NULL,
    demourl text NOT NULL,
    downloaded boolean DEFAULT false,
    filepath text,
    downloadattempts integer DEFAULT 0,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updatedat timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    matchid integer NOT NULL
);


ALTER TABLE dbo.tbldemofiles OWNER TO whltv;

--
-- Name: tbldemofiles_demofileid_seq; Type: SEQUENCE; Schema: dbo; Owner: whltv
--

CREATE SEQUENCE dbo.tbldemofiles_demofileid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dbo.tbldemofiles_demofileid_seq OWNER TO whltv;

--
-- Name: tbldemofiles_demofileid_seq; Type: SEQUENCE OWNED BY; Schema: dbo; Owner: whltv
--

ALTER SEQUENCE dbo.tbldemofiles_demofileid_seq OWNED BY dbo.tbldemofiles.demofileid;


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
    hltvurl text
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
-- Name: tbldemofiles demofileid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbldemofiles ALTER COLUMN demofileid SET DEFAULT nextval('dbo.tbldemofiles_demofileid_seq'::regclass);


--
-- Name: tblevents eventid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblevents ALTER COLUMN eventid SET DEFAULT nextval('dbo.tblevents_eventid_seq'::regclass);


--
-- Name: tbleventtypes eventtypeid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbleventtypes ALTER COLUMN eventtypeid SET DEFAULT nextval('dbo.tbleventtypes_eventtypeid_seq'::regclass);


--
-- Name: tbllocations locationid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbllocations ALTER COLUMN locationid SET DEFAULT nextval('dbo.tbllocations_locationid_seq'::regclass);


--
-- Name: tblteamrankings teamrankingid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteamrankings ALTER COLUMN teamrankingid SET DEFAULT nextval('dbo.tblteamrankings_teamrankingid_seq'::regclass);


--
-- Name: tblteams teamid; Type: DEFAULT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tblteams ALTER COLUMN teamid SET DEFAULT nextval('dbo.tblteams_teamid_seq'::regclass);


--
-- Name: tbldemofiles tbldemofiles_pkey; Type: CONSTRAINT; Schema: dbo; Owner: whltv
--

ALTER TABLE ONLY dbo.tbldemofiles
    ADD CONSTRAINT tbldemofiles_pkey PRIMARY KEY (demofileid);


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

