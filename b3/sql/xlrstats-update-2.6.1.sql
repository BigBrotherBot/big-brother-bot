-- SQL code to update default xlrstats database tables to xlrstats plugin version 2.6.1 --
-- This makes usage of weaponnames > 32 characters possible --

ALTER TABLE  `xlr_weaponstats` CHANGE  `name`  `name` VARCHAR( 64 )