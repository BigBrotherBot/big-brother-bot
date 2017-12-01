#!/bin/bash

# Big Brother Bot (B3) Management - http://www.bigbrotherbot.net
# Maintainer: Daniele Pantaleone <fenix@bigbrotherbot.net>
# App Version: 0.14
# Last Edit: 26/07/2015

### BEGIN INIT INFO
# Provides:          b3
# Required-Start:    $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Manage Big Brother Bot (B3) - http://www.bigbrotherbot.net
# Description:       Manage Big Brother Bot (B3) - http://www.bigbrotherbot.net
### END INIT INFO

########################################################################################################################
#
#  CHANGELOG
#
# ----------------------------------------------------------------------------------------------------------------------
#
#  2014-11-09 - 0.1  - Fenix         - initial version
#  2014-11-30 - 0.2  - Fenix         - changed some file paths used for PID storage and B3 autodiscover
#  2014-12-13 - 0.3  - Fenix         - added support for auto-restart mode
#  2014-12-14 - 0.4  - Fenix         - correctly match number of subprocess in b3_is_running when auto-restart mode is
#                                      being used auto-restart mode uses 4 processes (the screen, the main loop in
#                                      b3/run.py, a new shell used by subprocess, and the command to actually start the
#                                      B3 instance inside this new shell), while a normal B3 startup uses only 2
#                                      processes (screen and B3 process running inside the screen)
#  2014-12-20 - 0.5  - Fenix         - fixed b3_clean not restarting all previously running B3 instances
#  2015-02-08 - 0.6  - Fenix         - fixed change to current directory not working when using an alias to execute b3.sh
#  2015-02-09 - 0.7  - Fenix         - fixed logging not being written to disk
#  2015-02-09 - 0.8  - Fenix         - set ${SCRIPT_DIR} variable upon execution
#                                    - set ${B3_DIR} variable upon execution
#                                    - remove all the readlink commands in favor of ${SCRIPT_DIR} and ${B3_DIR}
#  2015-02-10 - 0.9  - Thomas LEVEIL - fixed infinite loop between p_out and p_log
#                                    - simplify colors stripping
#                                    - temporarily activate logging using B3_LOG environment variable
#                                    - fix log failure detection and in case of errors, display the reason why it failed
#  2015-03-06 - 0.10 - Fenix         - removed python 2.6 support
#  2015-03-17 - 0.11 - Fenix         - added developer mode, temporarily activable with B3_DEV environment variable
#  2015-05-16 - 0.12 - Fenix         - use the --console parameter when starting B3 (otherwise GUI startup is triggered)
#  2015-07-04 - 0.13 - Fenix         - renamed B3_LOG_ENABLED into B3_LOG
#                                    - removed some LOG_EXT and PID_EXT variables: they are not needed
#                                    - activate/deactivate autorestart mode using B3_AUTORESTART env variable
#                                    - fixed b3_list matching also non configuration files while retrieving instances
#  2015-07-26 - 0.14 - Fenix         - do not allow to use root at all when using this very script
#                                    - create b3 home directory if it has not been created already


### SETUP
AUTO_RESTART="${B3_AUTORESTART:-1}" # will run b3 in auto-restart mode if set to 1
DATE_FORMAT="%a, %b %d %Y - %r"     # data format to be used when logging console output
LOG_ENABLED="${B3_LOG:-0}"          # if set to 1, will log console output to file
DEVELOPER="${B3_DEV:-0}"            # if set to 1, will activate developer mode
USE_COLORS="1"                      # if set to 1, will make use of bash color codes in the console output

### DO NOT MODIFY!!!
B3_DIR=""                   # will be set to the directory containing b3 source code (where we can find b3_run.py)
B3_RUN="b3_run.py"          # python executable which starts b3
B3_HOME=".b3"               # the name of the B3 home directory (located inside $HOME)
COMMON_PREFIX="b3_"         # a common prefix b3 configuration files must have to beparsed by this script
CONFIG_DIR="b3/conf"        # directory containing b3 configuration files (will be appended to ${B3_DIR}
CONFIG_EXT=(".ini" ".xml")  # list of b3 configuration file extensions
LOG_DIR="log"               # the name of the directory containing the log file (will be appended to ${SCRIPT_DIR})
PID_DIR="pid"               # the name of the directory containing the b3 pid file (will be appended to ${SCRIPT_DIR})
SCRIPT_DIR=""               # will be set to the directory containing this very script

########################################################################################################################
# OUTPUT FUNCTIONS

# @name p_out
# @description Parse Q3 alike color codes and translates them into BASH output colors.
#              All given strings are being hand over to p_log after stripping them from color codes.
function p_out() { 
    if [ "${USE_COLORS}" == "0" ]; then
        echo -e "${@//^[0-9]}"
    else
        echo -e $(echo "$@" | sed "s/\^\([0-9]\)/\\\\033[3\1m/g; s/\\\\033\[30m/\\\\033[0m/g") "\033[0m"
    fi
    # write console output to main log
    p_log "${@//^[0-9]}"
    return 0
}

# @name p_log
# @description Log messages in the log file.
function p_log()  {
    if [ ! "${LOG_ENABLED}" -eq 0 ]; then
        # make sure to have a valid directory for the logfile
        if [ ! -d "${SCRIPT_DIR}/${LOG_DIR}" ]; then
            mkdir "${SCRIPT_DIR}/${LOG_DIR}"
        fi
        LOG_FILE="${SCRIPT_DIR}/${LOG_DIR}/app.log"
        if [ ! -f "${LOG_FILE}" ]; then
            if ! STDERR=$(touch "${LOG_FILE}" 2>&1 > /dev/null); then
                LOG_ENABLED=0  # prevent infinite loop between p_out and p_log
                p_out "^1ERROR^0: could not create log file: no log will be written! ^3($STDERR)^0"
                return 1
            fi
        fi
        DATE=$(date +"${DATE_FORMAT}")
        echo "[${DATE}]  >  ${@}" 1>> "${LOG_FILE}" 2> /dev/null
    fi
    return 0
}

########################################################################################################################
# UTILITIES

# @name join
# @description Join array elements into a string using the given separator.
# @example      join , a "b c" d        # a,b c,d
#               join / var local tmp    # var/local/tmp
#               join , "${FOO[@]}"      # a,b,c
function join() { 
    local IFS="${1}";
    shift; 
    echo "${*}";
}

# @name b3_conf_path
# @description Will output the absolute path of the B3 instance configuration file: stdout 
#              redirection needs to be handled properly when using this function.
#              If no configuration file is found it outputs nothing (check using if [ -z $VAR ]).
function b3_conf_path() {
    local B3="${1}"
    for i in ${CONFIG_EXT[@]}; do
        local HOME_CONFIG="${HOME}/${B3_HOME}/${COMMON_PREFIX}${B3}${i}"
        local B3_CONFIG="${B3_DIR}/${CONFIG_DIR}/${COMMON_PREFIX}${B3}${i}"
        if [ -f "${HOME_CONFIG}" ]; then
            echo "${HOME_CONFIG}"
            break
        elif [ -f "${B3_CONFIG}" ]; then
            echo "${B3_CONFIG}"
            break
        fi
    done
}

# @name b3_pid_path
# @description Will output the absolute path of the B3 instance PID file: stdout redirection 
#              needs to be handled properly when using this function.
#              If no configuration file is found it outputs nothing check using if [ -z $VAR ]).
function b3_pid_path() {
    local B3="${1}"
    local PID_FILE="${SCRIPT_DIR}/${PID_DIR}/${COMMON_PREFIX}${B3}.pid"
    if [ -f "${PID_FILE}" ]; then
        echo "${PID_FILE}"
    fi
}

# @name b3_is_running
# @description Retrieve the status of a B3 instance given its name and configuration file path.
# @return 0 if the B3 daemon is running
#         1 if the B3 daemon is not running
#         2 if the B3 daemon was running but recently crashed
function b3_is_running() {
    local B3="${1}"
    local CONFIG="${2}"
    local SCREEN="${COMMON_PREFIX}${B3}"
    local PROCESS="${B3_DIR}/${B3_RUN}"
    local NUMPROC=$(ps ax | grep ${SCREEN} | grep ${PROCESS} | grep ${CONFIG} | grep -v grep | wc -l)

    if ([ ${AUTO_RESTART} -eq 1 ] && [ ${NUMPROC} -eq 4 ]); then
        # screen is running with B3 process inside and auto-restart mode (using subprocess)
        return 0
    elif ([ ! ${AUTO_RESTART} -eq 1 ] && [ ${NUMPROC} -eq 2 ]); then
        # both screen and process running => B3 running
        return 0
    else
        if [ -z "$(b3_pid_path ${B3})" ]; then
            # no PID file found => not running
            return 1
        else
            # PID file found but process not running => CRASH
            return 2
        fi
    fi
}

# @name b3_uptime
# @description Will output the  the uptime of a B3 instance given its PID file path: stdout 
#              redirection needs to be handled properly when using this function.
function b3_uptime() {
    local PID_FILE="${1}"
    local NOW="$(date +"%s")"
    local MOD="$(stat --printf="%Y" "${PID_FILE}")"
    local SECDIFF=$(( ${NOW} - ${MOD} ))
    if [ ${SECDIFF} -lt 60 ]; then
        echo "${SECDIFF}s"
    elif ([ ${SECDIFF} -ge 60 ] && [ ${SECDIFF} -lt 3600 ]); then
        echo "$(echo "$(( ${SECDIFF} /  60 ))" | bc -l)m"
    else
        echo "$(echo "$(( ${SECDIFF} /  3600 ))" | bc -l)h"
    fi
}

# @name b3_list
# @description Will output a list of available B3 instances by checking available configuration 
#              files: stdout redirection needs to be handled properly when using this function.
#              The function is "duplicate-safe", so if a B3 instance has multiple configuration 
#              files specified (one for each supported configuration file extension), only the one 
#              with highest importance will be considered (according to the order extensions are 
#              specified in the configuration value ${CONFIG_EXT[@]})
function b3_list() {
    local B3_LIST=()
    local B3_CONF_PATH="${B3_DIR}/${CONFIG_DIR}"
    local B3_HOME_PATH="${HOME}/${B3_HOME}"
    local B3_CONFIG_LIST=$(find "${B3_HOME_PATH}" "${B3_CONF_PATH}" -maxdepth 1 -type f  \( -name "b3_*.ini" -o -name "b3_*.xml" \) -print | sort)
    for i in ${B3_CONFIG_LIST}; do
        local B3_NAME="$(basename ${i})"
        local B3_NAME="${B3_NAME:${#COMMON_PREFIX}}"
        for i in ${CONFIG_EXT[@]}; do
            local B3_NAME="${B3_NAME%${i}}"
        done
        IN=0
        for i in ${B3_LIST[@]}; do
            if [ "${i}" == "${B3_NAME}" ]; then
                IN=1
                break
            fi
        done
        if [ ${IN} -eq 0 ]; then
            B3_LIST+=("${B3_NAME}")
        fi
    done
    echo $(join ' ' "${B3_LIST[@]}")
}

########################################################################################################################
# MAIN FUNCTIONS

# @name b3_start
# @description Main B3 instance startup function.
function b3_start() {

    local B3="${1}"
    local CONFIG_FILE="$(b3_conf_path ${B3})"

    # check if already running
    b3_is_running "${B3}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b3_pid_path ${B3})"
    if [ ${RTN} -eq 0 ]; then
        local PID="$(cat ${PID_FILE})"
        local UPTIME="$(b3_uptime ${PID_FILE})"
        p_out "B3[${B3}] is already running [PID : ^2${PID}^0 - UPTIME : ^2${UPTIME}^0]"
        return 1
    elif [ ${RTN} -eq 2 ]; then
        p_out "^3WARNING^0: B3[${B3}] recently crashed..."
        rm "${PID_FILE}"
        sleep 1
    fi

    # start the B3 instance and sleep a bit: give it time to crash (if that's the case).
    # recompute also the PID file path because $(b3_pid_path) may output an empty string 
    # if the B3 was not running (and thus no PID file could be found in previous call)
    local SCREEN="${COMMON_PREFIX}${B3}"
    local PROCESS="${B3_DIR}/${B3_RUN}"
    local PID_FILE="${SCRIPT_DIR}/${PID_DIR}/${COMMON_PREFIX}${B3}.pid"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        screen -DmS "${SCREEN}" python "${PROCESS}" --restart --console --config "${CONFIG_FILE}" &
    else
        screen -DmS "${SCREEN}" python "${PROCESS}" --console --config "${CONFIG_FILE}" &
    fi

    echo "${!}" > "${PID_FILE}"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        sleep 6
    else
        sleep 1
    fi

    # check for proper B3 startup
    b3_is_running "${B3}" "${CONFIG_FILE}"

    local RTN="${?}"
    if [ ${RTN} -eq 0 ]; then
        local PID=$(cat ${PID_FILE})
        p_out "B3[${B3}] started [PID : ^2${PID}^0]"
        return 0
    else
        if [ ${RTN} -eq 2 ]; then
            rm "${PID_FILE}"
        fi
        p_out "^1ERROR^0: could not start B3[${B3}]"
        return 1
    fi
}

# @name process_start
# @description Main B3 instance shutdown function.
function b3_stop() {

    local B3="${1}"
    local CONFIG_FILE="$(b3_conf_path ${B3})"

    # check if already running
    b3_is_running "${B3}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b3_pid_path ${B3})"

    if [ ${RTN} -eq 1 ]; then
        p_out "B3[${B3}] is already stopped"
        return 1
    elif [ ${RTN} -eq 2 ]; then
        p_out "^3WARNING^0: B3[${B3}] recently crashed..."
        rm "${PID_FILE}"
        return 1
    fi

    # close the screen (and thus the process running inside)
    local PID="$(cat ${PID_FILE})"
    local UPTIME="$(b3_uptime ${PID_FILE})"
    local SCREEN="${COMMON_PREFIX}${B3}"
    screen -S "${PID}.${SCREEN}" -X quit &

    sleep 1

    # check for proper B3 shutdown
    b3_is_running "${B3}" "${CONFIG_FILE}"

    local RTN="${?}"
    if [ ${RTN} -eq 0 ]; then
        p_out "^1ERROR^0: could not stop B3[${B3}]"
        return 1
    else
        rm "${PID_FILE}"
        p_out "B3[${B3}] stopped [UPTIME : ^1${UPTIME}^0]"
        return 0
    fi
}

# @name b3_status
# @description Main B3 instance status check function. 
function b3_status() {

    local B3="${1}"
    local CONFIG_FILE="$(b3_conf_path ${B3})"

    # check if already running
    b3_is_running "${B3}" "${CONFIG_FILE}"

    local RTN="${?}"
    local PID_FILE="$(b3_pid_path ${B3})"

    case ${RTN} in
        0)
            local PID="$(cat ${PID_FILE})"
            local UPTIME="$(b3_uptime ${PID_FILE})"
            p_out "B3[${B3}] ^2ALIVE ^0[PID : ^2${PID}^0 - UPTIME : ^2${UPTIME}^0]"
            ;;
        1)
            p_out "B3[${B3}] ^3OFFLINE^0"
            ;;
        2)
            p_out "B3[${B3}] ^1CRASHED^0"
            ;;
        *)
            p_out "^1ERROR^0: invalid code returned: ^3${RTN}^0"
            p_out "Please report this to B3 developers: http://forum.bigbrotherbot.net"
            return 1
            ;;
    esac

    return 0
}

# @name b3_clean
# @description Clean B3 directories by removing all python compiled files. It will stop all 
#              the running B3 instances and restart them after the cleaning has been performed.
function b3_clean() {
    local B3_RUNNING=()
    local B3_LIST=$(b3_list)
    for i in ${B3_LIST}; do
        # check if B3 is running and if so stop it
        b3_is_running "${i}" "$(b3_conf_path ${i})"
        local RTN="${?}"
        if [ ${RTN} -eq 0 ]; then
            b3_stop "${i}"
            B3_RUNNING+=("${i}")
        fi
    done

    local B3_RUNNING_LIST=$(join ' ' "${B3_RUNNING[@]}")
    find "${B3_DIR}" -type f \( -name "*.pyc" -o -name "*.pid" \) \
                                -exec rm {} \; \
                                -exec printf "." \; \

    echo " DONE!"

    # restart all the B3 which were running 
    for i in ${B3_RUNNING_LIST}; do
        b3_start "${i}"
    done

    return 0
}

# @name do_usage
# @description Print the main help text
function b3_usage() {
    # do not  use p_out here otherwise it gets logged
    echo "
    -usage: b3.sh  start   [<name>] - start B3
                                stop    [<name>] - stop B3
                                restart [<name>] - restart B3
                                status  [<name>] - display current B3 status
                                clean            - clean B3 directory

    Copyright (C) 2014 Daniele Pantaleone <fenix@bigbrotherbot.net>
    Support: http://forum.bigbrotherbot.net
    "
    return 0
}

########################################################################################################################
# MAIN EXECUTION

# set some global variables needed in main execution and functions
SCRIPT_DIR="$(cd -P -- "$(dirname -- "${0}")" && pwd -P)"
B3_DIR="$(dirname ${SCRIPT_DIR})"

# check that the script is not executed by super user to avoid permission problems
# we will allow the B3 status check tho since the operation is totally harmless
if [ ! "${DEVELOPER}" -eq 0 ]; then # allow developers to use root to start b3
    if [ ${UID} -eq 0 ]; then
      p_out "^1ERROR^0: do not execute B3 as super user [root]"
      exit 1
    fi
fi

# check for python to be installed in the system
if [ -z $(which python) ]; then
    p_out "^1ERROR^0: The Python interpreter seems to be missing on your system"
    p_out "You need to install Python ^22.7 ^0to run B3"
    exit 1
fi

# check for correct python version to be installed on the system
VERSION=($(python -c 'import sys; print("%s %s" % (sys.version_info.major, sys.version_info.minor));'))
if [ ${VERSION[0]} -eq 3 ]; then
    p_out "^1ERROR^0: B3 is not yet compatible with Python ^33^0"
    p_out "You need to install Python ^22.7 ^0to run B3"
    exit 1
fi

if [ ${VERSION[1]} -lt 7 ]; then
    p_out "^1ERROR^0: B3 can't run under Python ^3${VERSION[0]}.${VERSION[1]}^0"
    p_out "You need to install Python ^22.7 ^0to run B3"
    exit 1
fi

# check for the PID directory to exists (user may have removed it)
if [ ! -d "${SCRIPT_DIR}/${PID_DIR}" ]; then
    mkdir "${SCRIPT_DIR}/${PID_DIR}"
fi

# check for b3 home directory (maybe b3 didn't started yet so it didn't create it)
if [ ! -d "${HOME}/${B3_HOME}" ]; then
    mkdir "${HOME}/${B3_HOME}"
fi

case "${1}" in

    "start")
        B3_LIST=$(b3_list)
        for i in ${B3_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b3_start "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B3 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B3[${2}]"
            fi
            exit 1
        fi
        ;;
    "stop")
        B3_LIST=$(b3_list)
        for i in ${B3_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b3_stop "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B3 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B3[${2}]"
            fi
            exit 1
        fi
        ;;
    "restart")
        B3_LIST=$(b3_list)
        for i in ${B3_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b3_stop "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B3 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B3[${2}]"
            fi
            exit 1
        fi
        for i in ${B3_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b3_start "${i}"
            fi
        done
        ;;

    "status")
        B3_LIST=$(b3_list)
        for i in ${B3_LIST}; do
            if ([ -z "${2}" ] || [ "${2}" == "${i}" ]); then
                b3_status "${i}"
                RUN=1
            fi
        done
        if [ -z ${RUN+xxx} ]; then
            if [ -z "${2}" ]; then
                p_out "^3WARNING^0: no B3 instance available"
            else
                p_out "^1ERROR^0: could not find configuration file for B3[${2}]"
            fi
            exit 1
        fi
        ;;

    "clean")
        p_out "^3WARNING^0: all running B3 will be restarted"
        echo -n "Do you want to continue [y/N]? "
        read ANSWER
        if ([ "${ANSWER:0:1}" == "y" ] || [ "${ANSWER:0:1}" == "Y" ]); then
            b3_clean
        else
            p_out "... Aborted!"
            exit 1
        fi
        ;;
    *)
        b3_usage
        ;;
esac
exit "${?}"
