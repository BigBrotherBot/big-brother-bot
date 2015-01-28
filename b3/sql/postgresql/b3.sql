CREATE TABLE IF NOT EXISTS aliases (
  id SERIAL PRIMARY KEY,
  num_used INTEGER NOT NULL DEFAULT '0',
  alias VARCHAR(32) NOT NULL DEFAULT '',
  client_id INTEGER NOT NULL DEFAULT '0',
  time_add INTEGER NOT NULL DEFAULT '0',
  time_edit INTEGER NOT NULL DEFAULT '0',
  CONSTRAINT aliases_alias UNIQUE (alias,client_id)
);

CREATE TABLE IF NOT EXISTS ipaliases (
  id SERIAL PRIMARY KEY,
  num_used INTEGER NOT NULL DEFAULT '0',
  ip VARCHAR(16) NOT NULL,
  client_id INTEGER NOT NULL DEFAULT '0',
  time_add INTEGER NOT NULL DEFAULT '0',
  time_edit INTEGER NOT NULL DEFAULT '0',
  CONSTRAINT ipaliases_ipalias UNIQUE (ip,client_id)
);

CREATE TABLE IF NOT EXISTS clients (
  id SERIAL PRIMARY KEY,
  ip VARCHAR(16) NOT NULL DEFAULT '',
  connections INTEGER NOT NULL DEFAULT '0',
  guid VARCHAR(36) NOT NULL DEFAULT '',
  pbid VARCHAR(32) NOT NULL DEFAULT '',
  name VARCHAR(32) NOT NULL DEFAULT '',
  auto_login SMALLINT NOT NULL DEFAULT '0',
  mask_level SMALLINT NOT NULL DEFAULT '0',
  group_bits INTEGER NOT NULL DEFAULT '0',
  greeting VARCHAR(128) NOT NULL DEFAULT '',
  time_add INTEGER NOT NULL DEFAULT '0',
  time_edit INTEGER NOT NULL DEFAULT '0',
  password VARCHAR(32) DEFAULT NULL,
  login VARCHAR(16) DEFAULT NULL,
  CONSTRAINT clients_guid UNIQUE (guid)
);

CREATE TABLE IF NOT EXISTS cmdgrants (
  id SERIAL PRIMARY KEY,
  commands TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY,
  name VARCHAR(32) NOT NULL DEFAULT '',
  keyword VARCHAR(32) NOT NULL DEFAULT '',
  level INTEGER NOT NULL DEFAULT '0',
  time_edit INTEGER NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  time_add INTEGER NOT NULL DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  CONSTRAINT groups_keyword UNIQUE (keyword)
);

UPDATE groups SET time_edit=0, name='Super Admin', keyword='superadmin', level=100 WHERE id=128;
UPDATE groups SET time_edit=0, name='Senior Admin', keyword='senioradmin', level=80 WHERE id=64;
UPDATE groups SET time_edit=0, name='Full Admin', keyword='fulladmin', level=60 WHERE id=32;
UPDATE groups SET time_edit=0, name='Admin', keyword='admin', level=40 WHERE id=16;
UPDATE groups SET time_edit=0, name='Moderator', keyword='mod', level=20 WHERE id=8;
UPDATE groups SET time_edit=0, name='Regular', keyword='reg', level=2 WHERE id=2;
UPDATE groups SET time_edit=0, name='User', keyword='user', level=1 WHERE id=1;
UPDATE groups SET time_edit=0, name='Guest', keyword='guest', level=0 WHERE id=0;
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 128, 0, 'Super Admin', 'superadmin', 100 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=128);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 64, 0, 'Senior Admin', 'senioradmin', 80 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=64);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 32, 0, 'Full Admin', 'fulladmin', 60 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=32);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 16, 0, 'Admin', 'admin', 40 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=16);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 8, 0, 'Moderator', 'mod', 20 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=8);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 2, 0, 'Regular', 'reg', 2 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=2);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 1, 0, 'User', 'user', 1 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=1);
INSERT INTO groups (id, time_edit, name, keyword, level) SELECT 0, 0, 'Guest', 'guest', 0 WHERE NOT EXISTS (SELECT 1 FROM groups WHERE id=0);

CREATE TABLE IF NOT EXISTS penalties (
  id SERIAL PRIMARY KEY,
  type VARCHAR(16) NOT NULL DEFAULT 'Ban',
  client_id INTEGER NOT NULL DEFAULT '0',
  admin_id INTEGER NOT NULL DEFAULT '0',
  duration INTEGER NOT NULL DEFAULT '0',
  inactive SMALLINT NOT NULL DEFAULT '0',
  keyword VARCHAR(16) NOT NULL DEFAULT '',
  reason VARCHAR(255) NOT NULL DEFAULT '',
  data VARCHAR(255) NOT NULL DEFAULT '',
  time_add INTEGER NOT NULL DEFAULT '0',
  time_edit INTEGER NOT NULL DEFAULT '0',
  time_expire INTEGER NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS data (
  data_key VARCHAR(255) NOT NULL PRIMARY KEY,
  data_value VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS xlr_bodyparts (
  id SERIAL PRIMARY KEY,
  name VARCHAR(25) NOT NULL DEFAULT '',
  kills INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  CONSTRAINT xlr_bodyparts_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS xlr_mapstats (
  id SERIAL PRIMARY KEY,
  name VARCHAR(25) NOT NULL DEFAULT '',
  kills INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  rounds SMALLINT NOT NULL DEFAULT '0',
  CONSTRAINT xlr_mapstats_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS xlr_opponents (
  id SERIAL PRIMARY KEY,
  target_id SMALLINT NOT NULL DEFAULT '0',
  killer_id SMALLINT NOT NULL DEFAULT '0',
  kills SMALLINT NOT NULL DEFAULT '0',
  retals SMALLINT NOT NULL DEFAULT '0',
  FOREIGN KEY(target_id) REFERENCES clients(id),
  FOREIGN KEY(killer_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_playerbody (
  id SERIAL PRIMARY KEY,
  bodypart_id SMALLINT NOT NULL DEFAULT '0',
  player_id SMALLINT NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  FOREIGN KEY(bodypart_id) REFERENCES xlr_bodyparts(id),
  FOREIGN KEY(player_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_playermaps (
  id SERIAL PRIMARY KEY,
  map_id SMALLINT NOT NULL DEFAULT '0',
  player_id SMALLINT NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills INTEGER NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  rounds SMALLINT NOT NULL DEFAULT '0',
  FOREIGN KEY(map_id) REFERENCES xlr_mapstats(id),
  FOREIGN KEY(player_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_playerstats (
  id SERIAL PRIMARY KEY,
  client_id INTEGER NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  ratio FLOAT NOT NULL DEFAULT '0',
  skill FLOAT NOT NULL DEFAULT '0',
  assists INTEGER NOT NULL DEFAULT '0',
  assistskill FLOAT NOT NULL DEFAULT '0',
  curstreak SMALLINT NOT NULL DEFAULT '0',
  winstreak SMALLINT NOT NULL DEFAULT '0',
  losestreak SMALLINT NOT NULL DEFAULT '0',
  rounds SMALLINT NOT NULL DEFAULT '0',
  hide SMALLINT NOT NULL DEFAULT '0',
  fixed_name VARCHAR(32) NOT NULL DEFAULT '',
  id_token VARCHAR(10) NOT NULL DEFAULT '',
  FOREIGN KEY(client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_weaponstats (
  id SERIAL PRIMARY KEY,
  name VARCHAR(64) NOT NULL DEFAULT '',
  kills INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  CONSTRAINT xlr_weaponstats_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS xlr_weaponusage (
  id SERIAL PRIMARY KEY,
  weapon_id SMALLINT NOT NULL DEFAULT '0',
  player_id SMALLINT NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  FOREIGN KEY(weapon_id) REFERENCES xlr_weaponstats(id),
  FOREIGN KEY(player_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_actionstats (
  id SERIAL PRIMARY KEY,
  name VARCHAR(25) NOT NULL DEFAULT '',
  count INTEGER NOT NULL DEFAULT '0',
  CONSTRAINT xlr_actionstats_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS xlr_playeractions (
  id SERIAL PRIMARY KEY,
  action_id SMALLINT NOT NULL DEFAULT '0',
  player_id SMALLINT NOT NULL DEFAULT '0',
  count INTEGER NOT NULL DEFAULT '0',
  FOREIGN KEY(action_id) REFERENCES xlr_actionstats(id),
  FOREIGN KEY(player_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS xlr_history_monthly (
  id SERIAL PRIMARY KEY,
  client_id INTEGER NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  ratio FLOAT NOT NULL DEFAULT '0',
  skill FLOAT NOT NULL DEFAULT '0',
  assists INTEGER NOT NULL DEFAULT '0',
  assistskill FLOAT NOT NULL DEFAULT '0',
  winstreak SMALLINT NOT NULL DEFAULT '0',
  losestreak SMALLINT NOT NULL DEFAULT '0',
  rounds SMALLINT NOT NULL DEFAULT '0',
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  week INTEGER NOT NULL,
  day INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS xlr_history_weekly (
  id SERIAL PRIMARY KEY,
  client_id INTEGER NOT NULL DEFAULT '0',
  kills INTEGER NOT NULL DEFAULT '0',
  deaths INTEGER NOT NULL DEFAULT '0',
  teamkills SMALLINT NOT NULL DEFAULT '0',
  teamdeaths SMALLINT NOT NULL DEFAULT '0',
  suicides SMALLINT NOT NULL DEFAULT '0',
  ratio FLOAT NOT NULL DEFAULT '0',
  skill FLOAT NOT NULL DEFAULT '0',
  assists INTEGER NOT NULL DEFAULT '0',
  assistskill FLOAT NOT NULL DEFAULT '0',
  winstreak SMALLINT NOT NULL DEFAULT '0',
  losestreak SMALLINT NOT NULL DEFAULT '0',
  rounds SMALLINT NOT NULL DEFAULT '0',
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  week INTEGER NOT NULL,
  day INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ctime (
  id SERIAL PRIMARY KEY,
  guid VARCHAR(36) NOT NULL,
  came VARCHAR(11) DEFAULT NULL,
  gone VARCHAR(11) DEFAULT NULL,
  nick VARCHAR(32) NOT NULL
);