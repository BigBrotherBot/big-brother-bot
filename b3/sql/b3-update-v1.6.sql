#ALTER DATABASE  `b3` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci

ALTER TABLE aliases CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE clients CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE groups CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE penalties CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;

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
