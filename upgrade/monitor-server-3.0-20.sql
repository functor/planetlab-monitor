-- If there's an existing database, these commands will upgrade it to the
-- current version
ALTER TABLE actionrecord ADD COLUMN log_path varchar DEFAULT NULL;

ALTER TABLE findbadnoderecord ADD COLUMN iptables_status varchar DEFAULT NULL;
ALTER TABLE findbadnoderecord_history ADD COLUMN iptables_status varchar DEFAULT NULL;
