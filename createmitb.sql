-- This SQL script is written for PostgreSQL.
-- @author: xiaowing
-- @license:   Apache Lincese 2.0 

DROP TABLE IF EXISTS sch_crawler.mail_info;
DROP SCHEMA IF EXISTS sch_crawler;

CREATE SCHEMA sch_crawler AUTHORIZATION wing;
CREATE TABLE sch_crawler.mail_info
(
    mail_sender character varying(64) NOT NULL,
    mail_title text NOT NULL,
    mail_datetime timestamp(0) NOT NULL,
    mail_url text NOT NULL,
    info_inserttime timestamp(3) DEFAULT now(), 
    CONSTRAINT mail_info_pkey PRIMARY KEY (mail_sender, mail_title, mail_datetime),
    CONSTRAINT mail_info_ukey UNIQUE (mail_url)
);
ALTER TABLE sch_crawler.mail_info OWNER TO wing;

