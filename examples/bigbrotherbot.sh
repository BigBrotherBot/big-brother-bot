#!/bin/bash

########### SETTINGS  ############

## the user that must be used to run the bot
USER=melvyn

## the big brother bot main config file
B3_CONFIGFILE="/home/melvyn/james/b3source/ff/b3/conf/b3-obj.xml"

## where b3_run_obj.py is located
B3_BIN="/home/melvyn/james/b3source/ff/b3_run_obj.py"

## where the python binary is located
PYTHON_BIN=/usr/bin/python

########### SETTINGS END ############

set -e
DEBUG=off
B3_OPTS="--config $B3_CONFIGFILE"
B3_PID_FILE="${HOME}/.b3-$(echo $B3_CONFIGFILE | tr '/' '_').pid"

if [ ! -f "$B3_CONFIGFILE" ]; then
  echo "ERROR: config file not found ($B3_CONFIGFILE)"
  exit 1
fi


if [ ! -f "$B3_BIN" ]; then
  echo "ERROR: file not found : '$B3_BIN'"
  exit 1
fi
if [ ! -x "$B3_BIN" ]; then
  echo "ERROR: cannot execute '$B3_BIN'"
  exit 1
fi
if [ ! -f "$PYTHON_BIN" ]; then
  echo "ERROR: file not found : '$PYTHON_BIN'"
  exit 1
fi
if [ ! -x "$PYTHON_BIN" ]; then
  echo "ERROR: cannot execute '$PYTHON_BIN'"
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
	cd $(dirname $B3_BIN)
	$PYTHON_BIN $B3_BIN $B3_OPTS &
	echo $! > $B3_PID_FILE
}

function do_stop {
	NB_PROCESS=`ps ax | grep b3_run_obj | grep "$B3_CONFIGFILE" | grep -v grep | wc -l`
	if [ $NB_PROCESS -gt 1 ]; then
		echo "ERROR: multiple b3 processes found, you'd better kill thoses processes by hand."
	elif [ $NB_PROCESS -eq 1 ]; then
		if [ -f $B3_PID_FILE ]; then
			PID=$(cat $B3_PID_FILE)
			NB_PROCESS=`ps hax $PID | grep b3_run_obj | grep "$B3_CONFIGFILE" | grep -v grep | wc -l`
			if [ $NB_PROCESS -eq 1 ]; then
				kill -15 $PID
			else
				echo "ERROR: process N° $PID does not seem to be b3"
				echo "kill b3 by hand"
			fi
		fi
	else
		echo "WARNING: are you sure b3 is running ?"
	fi
}


kill_programme() {
        PID=`ps hax | grep "b3_run_obj" | grep "$B3_CONFIGFILE" | grep -v grep | cut -d' ' -f1 | head -n1`
        echo "killing process [$PID]"
        kill -9 $PID
}


case "$1" in
  start)
		echo "Starting Big Brother Bot"
		NB_PROCESS=`ps ax | grep b3_run_obj | grep "$B3_CONFIGFILE" | grep -v grep | wc -l`
		if [ $NB_PROCESS -eq 0 ]; then
			do_start
		else
			echo "ERROR: b3 is already running"
		fi
	;;
  stop)
		echo -n "Stopping Big Brother Bot"
		do_stop
		echo "."
	;;

  restart)
        echo -n "Restarting Big Brother Bot"
		do_stop
		sleep 1
		do_start
	;;
	
	status)
		debug "status:"
		NB_PROCESS=`ps ax | grep b3_run_obj | grep "$B3_CONFIGFILE" | grep -v grep | wc -l`
		debug "NB_PROCESS: $NB_PROCESS"
		if [ $NB_PROCESS -gt 1 ]; then
			echo "WARNING: multiple b3 processes found !"
		elif [ $NB_PROCESS -eq 1 ]; then
			echo "running :)"
		else
			echo "not running :("
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

