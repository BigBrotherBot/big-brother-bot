-- SQL code to update default B3 database tables to B3 version 1.10.0 --
-- --------------------------------------------------------

-- Update time_expire column value for Kick penalties
UPDATE `penalties` SET `time_expire`=-1 WHERE `type` = 'Kick';