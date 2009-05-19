#!/bin/ksh
echo "Starting FTPTail"
echo ""
cd /home/melvyn/james/b3source/ff/b3/gamelog
./ftptail-obj.sh restart
sleep 5
echo "Starting B3Bot"
echo ""
cd /home/melvyn/b3starters
./bigbrotherbot.sh restart

while true
do
echo "Checksum test for logfile 1"
chksum1=`md5sum /home/melvyn/james/b3source/ff/b3/gamelog/games_mp_obj.log`
echo "MD5Sum for logfile 1 = $chksum1"
sleep 60
echo "Checksum test for logfile 2"
chksum2=`md5sum /home/melvyn/james/b3source/ff/b3/gamelog/games_mp_obj.log`
echo "MD5Sum for logfile 2 = $chksum2"
if [ "$chksum1" = "$chksum2" ]
then
echo "Logfiles are identical, restarting bot"
cd /home/melvyn/james/b3source/ff/b3/gamelog
./ftptail-obj.sh restart
sleep 10
cd /home/melvyn/b3starters
./bigbrotherbot.sh restart
fi
done