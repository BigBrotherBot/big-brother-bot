-- SQL code to update default xlrstats database tables to xlrstats plugin version 2.4.0 --

-- modify existing xlrstats tables to support unicode --
ALTER TABLE `xlr_actionstats` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_bodyparts` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_history_monthly` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_history_weekly` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_mapstats` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_opponents` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_playeractions` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_playerbody` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_playermaps` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_playerstats` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_weaponstats` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `xlr_weaponusage` CONVERT TO CHARACTER SET utf8;

-- need to update the weapon-identifier columns in these tables for cod7. This game knows over 255 weapons/variations --
ALTER TABLE `xlr_weaponstats` CHANGE `id` `id` SMALLINT( 5 ) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE `xlr_weaponusage` CHANGE `weapon_id` `weapon_id` SMALLINT( 5 ) UNSIGNED NOT NULL DEFAULT  '0';

