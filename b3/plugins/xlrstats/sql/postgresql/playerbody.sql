CREATE TABLE IF NOT EXISTS %s (
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