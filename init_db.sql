CREATE TABLE beacon_records (
id SERIAL NOT NULL PRIMARY KEY,
data text NOT NULL,
timestamp timestamp NOT NULL,
imei VARCHAR(15) NOT NULL);

CREATE TABLE beacons (
id SERIAL NOT NULL PRIMARY KEY,
uuid VARCHAR(40) NOT NULL,
record INT NOT NULL REFERENCES beacon_records(id),
beacon_flag VARCHAR(8),
signal_str VARCHAR(8),
batt_v VARCHAR(4),
temp VARCHAR(4),
param_01 VARCHAR(31),
param_02 VARCHAR(31),
param_03 VARCHAR(31),
add_data VARCHAR(31));
