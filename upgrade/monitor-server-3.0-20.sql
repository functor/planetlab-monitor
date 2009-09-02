-- If there's an existing database, these commands will upgrade it to the
-- current version
ALTER TABLE actionrecord ADD COLUMN log_path varchar DEFAULT NULL;
