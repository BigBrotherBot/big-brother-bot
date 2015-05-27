CREATE TABLE IF NOT EXISTS `%s` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `bodypart_id` TINYINT(3) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `kills` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `deaths` MEDIUMINT(8) NOT NULL DEFAULT '0',
  `teamkills` SMALLINT(5) NOT NULL DEFAULT '0',
  `teamdeaths` SMALLINT(5) NOT NULL DEFAULT '0',
  `suicides` SMALLINT(5) NOT NULL DEFAULT '0',
  FOREIGN KEY(`bodypart_id`) REFERENCES xlr_bodyparts(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);