CREATE TABLE IF NOT EXISTS sites
(
    id serial NOT NULL,
    url text,
    constraint sites_pk primary key (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS sites_id_uindex
    ON sites (id);

CREATE UNIQUE INDEX IF NOT EXISTS sites_url_uindex
    ON sites (url);

CREATE TABLE IF NOT EXISTS success
(
    site_id int NOT NULL
        CONSTRAINT success_sites_id_fk
            REFERENCES sites,
    started timestamptz,
    ended timestamptz,
    response_time float4,
    status int,
    pattern text,
    match bool
);

CREATE TABLE IF NOT EXISTS errors
(
    site_id int NOT NULL
        CONSTRAINT errors_sites_id_fk
            REFERENCES sites,
    started timestamptz,
    error_type text,
    message text
);