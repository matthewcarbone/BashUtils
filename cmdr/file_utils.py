import json
from pathlib import Path
from subprocess import Popen, PIPE
from time import time
from sys import platform


def save_json(d, path, indent=4, sort_keys=False):
    """Saves a json file to the path specified.

    Parameters
    ----------
    d : dict
        Must be json-serializable.
    path : str
        File path to save at.
    indent : int, optional
        The indentation level of the saved json file (in units of spaces).
        Default is 4.
    sort_keys : bool, optional
        If True, sorts the saved json file by keys. Default is False.
    """

    with open(path, "w") as outfile:
        json.dump(d, outfile, indent=indent, sort_keys=sort_keys)


def read_json(path):
    """Reads a json file from the specified path.

    Parameters
    ----------
    path : str

    Returns
    -------
    dict
    """

    with open(path, "r") as infile:
        dat = json.load(infile)
    return dat


def run_command(cmd):
    """Execute the external shell command and get its exitcode, stdout and
    stderr. Also returns the amount of time the command took to execute. The
    command you pass to run_command should be basically the same as using the
    command line shell.

    Parameters
    ----------
    cmd : str
        The command to run.

    Returns
    -------
    dict
        A dictionary with the keys 'exitcode', 'stdout', 'stderr' and 'dt',
        representing the exit code, output from the command piped to stdout,
        error information from the command piped to stderr, and the elapsed
        time in seconds.
    """

    t0 = time()
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = proc.communicate()
    exitcode = proc.returncode
    dt = time() - t0

    return {
        "exitcode": exitcode,
        "stdout": out.decode("utf-8").strip(),
        "stderr": err.decode("utf-8").strip(),
        "dt": dt,
    }


def exhaustive_directory_search(root, filename):
    """Executes an exhaustive, recursive directory search of all downstream
    directories, finding directories which contain a file matching the provided
    file name query string.

    Parameters
    ----------
    root : os.PathLike
        The path (absolute or relative) to the directory from which to conduct
        the exhaustive search.
    filename : str
        The exact name of the file which identifies a directory as one of
        interest.

    Returns
    -------
    list
        A list of of os.PathLike directories containing the filename provided.
    """

    return [xx.parent for xx in Path(root).rglob(filename)]


def check_if_substring_match(lines, substring):
    """Checks the provided lines and determines if a substring is present.

    Parameters
    ----------
    lines : list of str
        The lines to check for a substring match.
    substring : str
        The substring to match

    Returns
    -------
    bool
        True if the substring was found in any of the lines. False otherwise.
    """

    return any([substring in line for line in lines])
