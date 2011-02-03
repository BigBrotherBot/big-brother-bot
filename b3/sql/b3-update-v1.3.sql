-- phpMyAdmin SQL Dump
-- Generation Time: Apr 7, 2010
-- 

-- --------------------------------------------------------

-- Existing pre v1.3 client table needs to be updated: 
ALTER TABLE `clients` CHANGE `guid` `guid` VARCHAR( 36 );
        