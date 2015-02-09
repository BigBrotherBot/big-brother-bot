#!/bin/bash

# Big Brother Bot (B3) Management - http://www.bigbrotherbot.net
# Maintainer: Daniele Pantaleone <fenix@bigbrotherbot.net>
# App Version: 0.6
# Last Edit: 08/02/2015

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
#                                                                                                                      #
#  CHANGELOG                                                                                                           #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
#  2014-11-09 - 0.1 - initial version                                                                                  #
#  2014-11-30 - 0.2 - changed some file paths used for PID storage and B3 autodiscover                                 #
#  2014-12-13 - 0.3 - added support for auto-restart mode                                                              #
#  2014-12-14 - 0.4 - correctly match number of subprocess in b3_is_running when auto-restart mode is being used       #
#                     auto-restart mode uses 4 processes (the screen, the main loop in b3/run.py, a new shell used     #
#                     by subprocess, and the command to actually start the B3 instance inside this new shell), while   #
#                     a normal B3 startup uses only 2 processes (screen and B3 process running inside the screen)      #
#  2014-12-20 - 0.5 - fixed b3_clean not restarting all previously running B3 instances                                #
#  2015-02-08 - 0.6 - fixed change to working directory not working properly when using an alias to execute the script #
#                                                                                                                      #
########################################################################################################################

### SETUP
AUTO_RESTART="1"
DATE_FORMAT="%a, %b %d %Y - %r"
LOG_ENABLED="0"
LOG_PATH="log/b3_init.log"
USE_COLORS="1"

### DO NOT MODIFY!!!
B3_RUN="../b3_run.py"
COMMON_PREFIX="b3_"
CONFIG_PATH="../b3/conf"
CONFIG_EXT=(".ini" ".xml")
PID_PATH="pid"
PID_EXT=".pid"

########################################################################################################################
# OUTPUT FUNCTIONS

# @name p_out
# @description Parse Q3 alike color codes and translates them into BASH output colors.
#              All given strings are being hand over to p_log after stripping them from color codes.
function p_out() { 
    if [ "${USE_COLORS}" == "0" ]; then
        echo -e $(echo "$@" | sed "s/\^\([0-9]\)//g") 
    else
        echo -e $(echo "$@" | sed "s/\^\([0-9]\)/\\\\033[3\1m/g; s/\\\\033\[30m/\\\\033[0m/g") "\033[0m"
    fi
    # write console output to main log
    p_log $(echo "$@" | sed "s/\^\([0-9]\)//g")
    return 0
}

# @name p_log
# @description Log messages in the log file.
function p_log()  {
    if [ ! "${LOG_ENABLED}" -eq 0 ]; then
        LOG_FILE="$(readlink -f "${LOG_PATH}")"
        if [ -n "${LOG_FILE}" ]; then
            if [ ! -f "${LOG_FILE}" ]; then 
                if ! touch "${LOG_FILE}" 2> /dev/null; then
                    LOG_ENABLED=0  # prevent infinite loop between p_out and p_log
                    p_out "^1ERROR^0: could not create log file: no log will be written!"
                    return 1
                fi
            fi
            DATE=$(date +"${DATE_FORMAT}")
            echo "[${DATE}]  >  ${@}" 1>> "${LOG_FILE}" 2> /dev/null
        fi
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
        local CONFIG_FILE="$(readlink -f "${CONFIG_PATH}/${COMMON_PREFIX}${B3}${i}")"
        if [ -f "${CONFIG_FILE}" ]; then
        echo "${CONFIG_FILE}"
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
    local PID_FILE="$(readlink -f "${PID_PATH}/${COMMON_PREFIX}${B3}${PID_EXT}")"
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
    local PROCESS="$(readlink -f "${B3_RUN}")"
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
    local PATTERN="${COMMON_PREFIX}*[$(join "|" "${CONFIG_EXT[@]}")]"
    local B3_CONFIG_LIST=$(find $(readlink -f ${CONFIG_PATH}) -maxdepth 1 -type f -name "${PATTERN}" -print | sort)
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
        fi;
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
        p_out "^3WARNING^0: B3[${B3}] recently crashed... removing PID file"
        rm "${PID_FILE}"
        sleep 1
    fi

    # start the B3 instance and sleep a bit: give it time to crash (if that's the case).
    # recompute also the PID file path because $(b3_pid_path) may output an empty string 
    # if the B3 was not running (and thus no PID file could be found in previous call)
    local SCREEN="${COMMON_PREFIX}${B3}"
    local PROCESS="$(readlink -f "${B3_RUN}")"
    local PID_FILE="$(readlink -f "${PID_PATH}/${COMMON_PREFIX}${B3}${PID_EXT}")"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        screen -DmS "${SCREEN}" python "${PROCESS}" --restart --config "${CONFIG_FILE}" &
    else
        screen -DmS "${SCREEN}" python "${PROCESS}" --config "${CONFIG_FILE}" &
    fi

    echo "${!}" > "${PID_FILE}"

    if [ ${AUTO_RESTART} -eq 1 ]; then
        sleep 4
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
        p_out "^3WARNING^0: B3[${B3}] recently crashed... removing PID file"
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
    find "$(readlink -f "../")" -type f \( -name "*.pyc" -o -name "*${PID_EXT}" \) \
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
    -usage: b3.sh 
                    start   [<name>] - start B3
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

# change to the directory containing this very script so it can be used
# from outside this working directory (for example using a soflink)
cd $(cd -P -- "$(dirname -- "$0")" && pwd -P)

# check that the script is not executed by super user to avoid permission problems
# we will allow the B3 status check tho since the operation is totally harmless
if ([ ${UID} -eq 0 ] && [ -n "${1}" ] && [ "${1}" != "status" ]); then
  p_out "^1ERROR^0: do not execute B3 as super user [root]"
  exit 1
fi

# check for python to be installed in the system
if [ -z $(which python) ]; then
    p_out "^1ERROR^0: The Python interpreter seems to be missing on your system"
    p_out "You need either Python ^22.7 ^0or Python ^22.6 ^0to run B3"
    exit 1
fi

# check for correct python version to be installed on the system
VERSION=($(python -c 'import sys; print("%s %s" % (sys.version_info.major, sys.version_info.minor));'))
if [ ${VERSION[0]} -eq 3 ]; then
    p_out "^1ERROR^0: B3 is not yet compatible with Python ^33^0"
    p_out "You need either Python ^22.7 ^0or Python ^22.6 ^0to run B3"
    exit 1
fi

if [ ${VERSION[1]} -lt 6 ]; then
    p_out "^1ERROR^0: B3 can't run under Python ^3${VERSION[0]}.${VERSION[1]}^0"
    p_out "You need either Python ^22.7 ^0or Python ^22.6 ^0to run B3"
    exit 1
fi

# check for the PID directory to exists (user may have removed it)
if [ ! -d $(readlink -f "${PID_PATH}") ]; then
    mkdir $(readlink -f "${PID_PATH}")
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