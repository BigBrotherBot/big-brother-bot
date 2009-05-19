#!/bin/bash

########### SETTINGS  ############

## the user that must be used to run the bot
USER=melvyn

FTPTAIL_OPT=" -s 1 -f -p passwd -n 400"
FTPTAIL_SOURCE="731439@8.12.22.225/codww/main/games_mp.log"
##Ftptail name. Must be named individually for each instance of ftptail that is running.


## where b3_run.py is located
FTPTAIL_BIN="/home/melvyn/james/b3source/ff/b3/gamelog/ftptail-obj.pl"
FTPTAIL_DEST="/home/melvyn/james/b3source/ff/b3/gamelog/games_mp_obj.log"
## where the python binary is located
PERL_BIN=/usr/bin/perl

########### SETTINGS END ############

set -e
DEBUG=off
FTPTAIL_PID_FILE="${HOME}/.ftptail-$(echo $FTPTAIL_SOURCE | tr '/' '_').pid"


if [ ! -f "$FTPTAIL_BIN" ]; then
  echo "ERROR: file not found : '$FTPTAIL_BIN'"
  exit 1
fi
if [ ! -x "$FTPTAIL_BIN" ]; then
  echo "ERROR: cannot execute '$FTPTAIL_BIN'"
  exit 1
fi
if [ ! -f "$PERL_BIN" ]; then
  echo "ERROR: file not found : '$PERL_BIN'"
  exit 1
fi
if [ ! -x "$PERL_BIN" ]; then
  echo "ERROR: cannot execute '$PERL_BIN'"
  exit 1
fi

if [ "$(whoami)" != "$USER" ]; then
	echo "ERROR: you have to run that script as $USER"
	exit 1
fi


function debug() {
	if [ "$DEBUG" = "on" ]; then
		echo DEBUG: $@
	fi
}


function do_start {
	$PERL_BIN $FTPTAIL_BIN $FTPTAIL_OPT $FTPTAIL_SOURCE > $FTPTAIL_DEST 2>> /dev/null &
	echo $! > $FTPTAIL_PID_FILE
}

function do_stop {
	NB_PROCESS=`ps ax | grep $(basename $FTPTAIL_BIN) | grep "$FTPTAIL_SOURCE" | grep -v grep | wc -l`
	if [ $NB_PROCESS -gt 1 ]; then
		echo "ERROR: multiple processes found, you'd better kill thoses processes by hand."
	elif [ $NB_PROCESS -eq 1 ]; then
		if [ -f $FTPTAIL_PID_FILE ]; then
			PID=$(cat $FTPTAIL_PID_FILE)
			NB_PROCESS=`ps hax $PID | grep $(basename $FTPTAIL_BIN) | grep "$FTPTAIL_SOURCE" | grep -v grep | wc -l`
			if [ $NB_PROCESS -eq 1 ]; then
				kill -15 $PID
			else
				echo "ERROR: process N° $PID does not seem to be ftptail"
				echo "kill ftptail by hand"
			fi
		fi
	else
		echo "WARNING: are you sure ftptail is running ?"
	fi
}


kill_programme() {
        PID=`ps hax | grep $(basename $FTPTAIL_BIN) | grep "$FTPTAIL_SOURCE" | grep -v grep | cut -d' ' -f1 | head -n1`
        echo "killing process [$PID]"
        kill -9 $PID
}


case "$1" in
  start)
		echo "Starting ftptail"
		NB_PROCESS=`ps ax | grep $(basename $FTPTAIL_BIN) | grep "$FTPTAIL_SOURCE" | grep -v grep | wc -l`
		if [ $NB_PROCESS -eq 0 ]; then
			do_start
		else
			echo "ERROR: ftptail is already running"
		fi
	;;
  stop)
		echo -n "Stopping ftptail"
		do_stop
		echo "."
	;;

  restart)
		echo -n "Restarting ftptail"
		do_stop
		sleep 1
		do_start
	;;
	
	status)
		debug "status:"
		NB_PROCESS=`ps ax | grep $(basename $FTPTAIL_BIN) | grep "$B3_CONFIGFILE" | grep -v grep | wc -l`
		debug "NB_PROCESS: $NB_PROCESS"
		if [ $NB_PROCESS -gt 1 ]; then
			echo "WARNING: multiple processes found !"
      exit 2
		elif [ $NB_PROCESS -eq 1 ]; then
			echo "running :)"
      exit 0
		else
			echo "not running :("
      exit 1
		fi
	;;

	kill)
		kill_programme
	;;
  *)
	PROG_NAME=`basename $0`
	echo "Usage: $PROG_NAME {start|stop|restart|status}"
	exit 1
esac

exit 0

