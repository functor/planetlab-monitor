-- If there's an existing database, these commands will upgrade it to the
-- current version

ALTER TABLE findbadnoderecord ADD COLUMN boot_server varchar DEFAULT NULL;
ALTER TABLE findbadnoderecord_history ADD COLUMN boot_server varchar DEFAULT NULL;
