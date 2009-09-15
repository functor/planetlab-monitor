-- If there's an existing database, these commands will upgrade it to the
-- current version

-- ALTER TABLE historysiterecord ADD COLUMN message_last_reply timestamp without time zone DEFAULT NULL;
-- ALTER TABLE historysiterecord_history ADD COLUMN message_last_reply timestamp without time zone DEFAULT NULL;

ALTER TABLE historysiterecord ADD COLUMN penalty_pause boolean DEFAULT False;
ALTER TABLE historysiterecord_history ADD COLUMN penalty_pause boolean DEFAULT False;

ALTER TABLE historysiterecord ADD COLUMN penalty_pause_time timestamp without time zone DEFAULT NULL;
ALTER TABLE historysiterecord_history ADD COLUMN penalty_pause_time timestamp without time zone DEFAULT NULL;
