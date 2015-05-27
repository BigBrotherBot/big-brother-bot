CREATE TABLE IF NOT EXISTS `%s` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `action_id` TINYINT(3) NOT NULL DEFAULT '0',
  `player_id` SMALLINT(5) NOT NULL DEFAULT '0',
  `count` MEDIUMINT(8) NOT NULL DEFAULT '0',
  FOREIGN KEY(`action_id`) REFERENCES xlr_actionstats(`id`),
  FOREIGN KEY(`player_id`) REFERENCES clients(`id`)
);