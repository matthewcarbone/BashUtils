#!/bin/bash -l

# Put in /usr/local/bin or somewhere else in your path!
# This script must be accessible via `which`.

# Example to add to crontab
# crontab -l > mycron
# echo "00 09 * * 1-5 echo hello" >> mycron
# crontab mycron
# rm mycron


NOW=$(date)
CRON="* * * * *"
MAXJOBS=0
USER="USER_UNSET"
DIRECTORY="DIRECTORY_UNSET"
TARGET_FILE="submit.sbatch"
MODE="SETUP"
QUEUED="QUEUED"

optspec=":hc-:"
while getopts "$optspec" optchar; do
    case "${optchar}" in
        -)
            case "${OPTARG}" in
                user=*)
                    USER=${OPTARG#*=}
                    ;;
                directory=*)
                    DIRECTORY=${OPTARG#*=}
                    DIRECTORY=$(readlink -f "$DIRECTORY")
                    ;;
                maxjobs=*)
                    MAXJOBS=${OPTARG#*=}
                    ;;
                cron=*)
                    CRON=${OPTARG#*=}
                    ;;
                *)
                    if [ "$OPTERR" = 1 ] && [ "${optspec:0:1}" != ":" ]; then
                        echo "Unknown option --${OPTARG}"
                    fi
                    ;;
            esac;;
        c)
            echo "Running cronjob $NOW"
            MODE="CRON"
            ;;
        h)
            echo "usage: $0 [-v] [--loglevel[=]<value>]"
            exit 2
            ;;
        *)
            if [ "$OPTERR" != 1 ] || [ "${optspec:0:1}" = ":" ]; then
                echo "Non-option argument: '-${OPTARG}'"
            fi
            ;;
    esac
done


function assert_args {
    exitcode=0
    if [ "$USER" = "USER_UNSET" ]; then
        echo "error: user argument is required (--user=your_username)"
        exitcode=1
    fi
    if [ "$DIRECTORY" = "DIRECTORY_UNSET" ]; then
        echo "error: directory argument is required (--directory=your_directory)"
        exitcode=1
    fi
    if [ "$exitcode" -eq 1 ]; then
        exit 1
    fi
}

function print_args {
    echo "// SETTING PARAMETERS //"
    echo "USER         $USER"
    echo "DIRECTORY    $DIRECTORY"
    echo "MAXJOBS      $MAXJOBS"
    echo "TARGET FILE  $TARGET_FILE"
    echo "CRON         $CRON"
}


function write_payload_to_crontab {
    crontab -l > mycron
    full_script_path=$(readlink -f "$0")
    echo "$CRON bash $full_script_path -c --user=$USER --directory=$DIRECTORY --maxjobs=$MAXJOBS --targetfile=$TARGET_FILE >> $DIRECTORY/cronlog.log" >> mycron
    crontab mycron
    rm mycron
}


function remove_payload_from_crontab {
    crontab -l > mycron
    script_name=$(basename "$0")
    sed -i "/$script_name/d" mycron
    crontab mycron
    rm mycron
}


# Takes the file list as input
function dryrun {
    echo "DRYRUN - will attempt to submit the following $TARGET_FILE files"
    for directory in $1; do
        echo "$directory"
    done
}


function get_available_jobs_via_SLURM {
    queued_or_running_jobs=$(squeue -u "$USER" | awk 'NR!=1' | wc -l)
    echo $((MAXJOBS - queued_or_running_jobs))
}


function get_jobs_unqueued {
    cctot=0
    cc=0
    for file in $1; do
        parent="$(dirname "$file")"
        cd "$parent" || exit
        cctot=$((cctot+1))
        if [ -e "$QUEUED" ]; then
            cc=$((cc+1))
        fi
    done
    remaining=$((cctot-cc))
    echo "$remaining"
}


# Should be run every time on the cronjob
# This searches for all target files and runs them if they haven't
# been previously executed
function execute {

    file_list=$(find "$DIRECTORY" -name "$TARGET_FILE" -exec echo {} \;)
    
    # Dryrun does not submit anything, just prints the directories
    # This is run by default. The user has to set --maxjobs=<INT>
    if [ "$MAXJOBS" == 0 ]; then
        dryrun "$file_list"
        remove_payload_from_crontab
        exit 0
    fi

    # Get the remaining jobs
    number_of_jobs_unqueued=$(get_jobs_unqueued "$file_list")
    echo "jobs remaining before submission: $number_of_jobs_unqueued"

    # If no jobs remain, stop
    if [ "$number_of_jobs_unqueued" -lt 1 ]; then
        echo "!!! Finished !!!"
        remove_payload_from_crontab
        exit 0
    fi

    # Get the current job list
    currently_available_jobs=$(get_available_jobs_via_SLURM)

    # If no jobs remain, stop
    if [ "$currently_available_jobs" -lt 1 ]; then
        echo "No queue space available"
        exit 0
    fi

    # Actually execute
    for file in $file_list; do

        parent="$(dirname "$file")"
        cd "$parent" || exit

        # Break if we're done
        if [ "$currently_available_jobs" -lt 1 ]; then
            break
        fi

        # If we already queued the job, we write that flag to the directory; we
        # should check for this and if the QUEUED file exists, we continue since
        # we don't want to submit the job multiple times
        if [ -e "$QUEUED" ]; then
            continue
        fi

        # Submit the job
        if [ -e "$TARGET_FILE" ]; then
            slurm_out=$(sbatch "$TARGET_FILE")
            if [[ "$slurm_out" =~ .*"Submitted batch job".* ]]; then
                job_id=${slurm_out##* }
                echo "submitted job id $job_id: $parent"
                currently_available_jobs="$(get_available_jobs_via_SLURM)"
            else
                echo "submit error: $slurm_out"
                continue
            fi
        elif [ -e "submit.sh" ]; then
            bash submit.sh
        else
            echo "Unknown error"
            exit 1
        fi

        # Add the QUEUED marker so that the script knows to skip that
        # directory later
        touch "$QUEUED"

    done

    
    echo
}

# main
if [ "$MODE" = "CRON" ]; then
    execute
elif [ "$MODE" = "SETUP" ]; then
    assert_args
    print_args
    write_payload_to_crontab
else
    exit 1
fi
