-- SQL code to update default B3 database tables to B3 version 1.6.0 --

-- support unicode --
ALTER TABLE `aliases` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `clients` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `groups` CONVERT TO CHARACTER SET utf8;
ALTER TABLE `penalties` CONVERT TO CHARACTER SET utf8;

-- disable the auto_increment flag and add the Guest group at id 0:
ALTER TABLE  `groups` CHANGE  `id`  `id` INT( 10 ) UNSIGNED NOT NULL;
INSERT INTO `groups` (id, time_edit, name, keyword, time_add, level) VALUES (0, 0, 'Guest', 'guest', UNIX_TIMESTAMP(), 0);
