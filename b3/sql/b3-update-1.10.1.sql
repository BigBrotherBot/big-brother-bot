-- SQL code to update default B3 database tables to B3 version 1.10.1 --
-- --------------------------------------------------------

-- change mask_level in clients table to mask_group
ALTER TABLE `clients` CHANGE `mask_level` `mask_group_id` mediumint(8) unsigned NOT NULL DEFAULT '0';