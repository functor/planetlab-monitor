-- If there's an existing database, these commands will upgrade it to the
-- current version

ALTER TABLE findbadnoderecord ADD COLUMN firewall boolean DEFAULT False;
ALTER TABLE findbadnoderecord_history ADD COLUMN firewall boolean DEFAULT False;

ALTER TABLE findbadnoderecord ADD COLUMN external_dns_status boolean DEFAULT True;
ALTER TABLE findbadnoderecord_history ADD COLUMN external_dns_status boolean DEFAULT True;

ALTER TABLE findbadnoderecord ADD COLUMN rpms varchar DEFAULT NULL;
ALTER TABLE findbadnoderecord_history ADD COLUMN rpms varchar DEFAULT NULL;

ALTER TABLE findbadnoderecord ADD COLUMN uptime varchar DEFAULT NULL;
ALTER TABLE findbadnoderecord_history ADD COLUMN uptime varchar DEFAULT NULL;

ALTER TABLE findbadnoderecord ADD COLUMN traceroute varchar DEFAULT NULL;
ALTER TABLE findbadnoderecord_history ADD COLUMN traceroute varchar DEFAULT NULL;

ALTER TABLE historynoderecord ADD COLUMN firewall boolean DEFAULT false;
ALTER TABLE historynoderecord_history ADD COLUMN firewall boolean DEFAULT false;

ALTER TABLE historynoderecord ADD COLUMN plc_siteid integer DEFAULT 1;
ALTER TABLE historynoderecord_history ADD COLUMN plc_siteid integer DEFAULT 1;
