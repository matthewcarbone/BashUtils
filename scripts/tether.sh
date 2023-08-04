#!/bin/bash

# Put in /usr/local/bin or somewhere else in your path!
# This script must be accessible via `which`.

# Example to add to crontab
# crontab -l > mycron
# echo "00 09 * * 1-5 echo hello" >> mycron
# crontab mycron
# rm mycron

source array_slice.sh


NOW=$(date)
SLURM_HEADER="#!/bin/bash"

SLURM_LINES=()
EXECUTABLE_LINES=()
DIRECTORY="DIRECTORY_UNSET"
TETHER_DIRECTORY="TETHER_DIRECTORY_UNSET"
FILE="FILE_UNSET"
N_TETHER=36


optspec=":hc-:"
while getopts "$optspec" optchar; do
    case "${optchar}" in
        -)
            case "${OPTARG}" in
                directory=*)
                    DIRECTORY=${OPTARG#*=}
                    DIRECTORY=$(readlink -f "$DIRECTORY")
                    ;;
                tetherDirectory=*)
                    
                    TETHER_DIRECTORY=${OPTARG#*=}
                    mkdir "$TETHER_DIRECTORY"
                    TETHER_DIRECTORY=$(readlink -f "$TETHER_DIRECTORY")
                    ;;
                nTether=*)
                    N_TETHER=${OPTARG#*=}
                    ;;
                file=*)
                    FILE=${OPTARG#*=}
                    ;;
                line=*)
                    EXECUTABLE_LINES+=( "${OPTARG#*=}" )
                    ;;
                slurm.*=*)
                    # remove slurm prefix
                    cmd=${OPTARG#*.}
                    slurm_flag=${cmd%=*}
                    slurm_value=${cmd#*=}
                    slurm_line="#SBATCH --$slurm_flag=$slurm_value"
                    SLURM_LINES+=( "$slurm_line" )
                    ;;
                *)
                    if [ "$OPTERR" = 1 ] && [ "${optspec:0:1}" != ":" ]; then
                        echo "Unknown option --${OPTARG}"
                    fi
                    ;;
            esac;;
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
    if [ "$FILE" = "FILE_UNSET" ]; then
        echo "error: file argument is required (--file=indicator_file)"
        exitcode=1
    fi
    if [ "$DIRECTORY" = "DIRECTORY_UNSET" ]; then
        echo "error: directory argument is required (--directory=your_directory)"
        exitcode=1
    fi
    if [ "$TETHER_DIRECTORY" = "TETHER_DIRECTORY_UNSET" ]; then
        echo "error: directory argument is required (--tetherDirectory=your_tether_directory)"
        exitcode=1
    fi
    if [ "$exitcode" -eq 1 ]; then
        exit 1
    fi
}

function example_slurm_script() {
    echo
    echo "SLURM script will look something like this:"
    echo
    echo "| $SLURM_HEADER"
    for t in "${SLURM_LINES[@]}"; do
        echo "| $t"
    done
    echo "|"
    echo "| cd first/directory"
    for t in "${EXECUTABLE_LINES[@]}"; do
        echo "| $t"
    done
    echo "|"
    echo "| cd second/directory"
    for t in "${EXECUTABLE_LINES[@]}"; do
        echo "| $t"
    done
    echo "|"
    echo "| ..."
    echo "|"
    echo "| wait"
    echo
}


function write_slurm_script() {
    tether_index="$1"
    d="$TETHER_DIRECTORY/$tether_index"
    mkdir -p "$d"
    slurm_script_path="$d/submit.sbatch"
    echo "$SLURM_HEADER" >> "$slurm_script_path"
}

assert_args

echo
echo "directory <$DIRECTORY>" 
echo "will be searched for files <$FILE>"
echo "and tethered into <$TETHER_DIRECTORY>"

example_slurm_script



# shopt -s globstar
# files=$(find "$DIRECTORY" -name "$FILE")
# for i in "$DIRECTORY"*"$FILE"; do # Whitespace-safe and recursive
#     echo "$i"
# done
FILE_NAMES=$(find "$DIRECTORY" -name "*$FILE" -exec echo {} \;)

# This is basically a hack to split FILE_NAMES into an array via the \n 
# delimiter.
SAVEIFS=$IFS
IFS=$'\n'
#shellcheck disable=SC2206
FILE_NAMES=($FILE_NAMES)
IFS=$SAVEIFS

N_FILES=${#FILE_NAMES[@]}

echo "$N_FILES total"
echo "$N_TETHER files/tether"

total_tethers=$((N_FILES/N_TETHER))
extra_tethers=$((N_FILES%N_TETHER))
if [ $extra_tethers -gt 0 ]; then
    total_tethers=$((total_tethers+1))
fi
echo "$total_tethers total tethers"

# # Indicates which tether directory to use
# # Increments every time the local_counter exceeds N_TETHER
# tether_counter=0

# # The current number in a given tether
# local_counter=0

# # Total jobs written, just a sanity check
# total_jobs_written=0

# for t in "${FILE_NAMES[@]}"; do
#     directory_name="$(dirname "$(readlink -f "$t")")"
#     write_slurm_script "$tether_counter"  # Dummy

#     tether_counter=$((tether_counter+1))
# done


# for ((i = 0; i < ${#FILE_NAMES[@]}; i++))
# do
#     echo "${FILE_NAMES[$i]}"
# done

# echo "$files"
# for t in "${files[@]}"; do
#     # parent="$(dirname "$t")"
#     echo "$t"
#     exit 0
# done

