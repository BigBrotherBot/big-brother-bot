-- Updating to version 1.3:
ALTER TABLE `clients` CHANGE `guid` `guid` VARCHAR( 36 );

-- Updating to version 1.6:
ALTER TABLE aliases CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE clients CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE groups CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE penalties CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;

-- disable the auto_increment flag and add the Guest group at id 0:
ALTER TABLE  `groups` CHANGE  `id`  `id` INT( 10 ) UNSIGNED NOT NULL;
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (0, 0, 'Guest', 'guest', UNIX_TIMESTAMP(), 0);

-- modify existing xlrstats tables
ALTER TABLE xlr_actionstats CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_bodyparts CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_history_monthly CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_history_weekly CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_mapstats CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_opponents CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_playeractions CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_playerbody CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_playermaps CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_playerstats CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_weaponstats CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE xlr_weaponusage CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
