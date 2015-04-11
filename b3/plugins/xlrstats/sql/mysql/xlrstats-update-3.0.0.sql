-- Add a table field for the xlr_playerstats table
ALTER TABLE `xlr_playerstats` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';

-- Better scalability of the xlrstats tables.
ALTER TABLE `xlr_playerstats` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE `xlr_history_monthly` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE `xlr_history_weekly` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;