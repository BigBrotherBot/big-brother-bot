-- SQL code to update default B3 database tables to B3 version 1.3.0 --

-- update guid length
ALTER TABLE `clients` CHANGE `guid` `guid` VARCHAR( 36 );
