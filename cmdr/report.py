"""Module for generating reports on the results of input files.

.. important::

    While this should work generally, autojob is currently tested on the
    following types of code: FEFF 9.9.1, VASP 6.2.1, and the default CONFIG
    assumes these code versions.
"""

from collections import Counter
from pathlib import Path

from cmdr import logger

from cmdr.file_utils import (
    exhaustive_directory_search,
    run_command,
    check_if_substring_match,
)


CONFIG = {
    "in": {
        "FEFF": ["feff.inp"],
        "VASP": ["INCAR", "POSCAR", "KPOINTS", "POTCAR"],
    },
    "out": {
        "FEFF": [["xmu.dat", None], ["feff.out", "feff ends at"]],
        "VASP": [
            [
                "OUTCAR",
                " General timing and accounting informations for this job:",
            ]
        ],
    },
}


def check_computation_type(root, input_files=CONFIG["in"]):
    """Determines which type of computation has been completed in the directory
    of interest. In the cases when no input file types can be matched, or when
    multiple input file types are found, warnings/errors will be logged and
    None will be returned.

    Parameters
    ----------
    root : os.PathLike
        The directory containing the
    input_files : dict, optional
        A dictionary that contains keys corresponding to computation types
        (e.g. VASP) and values of lists of file names. These file names must
        _all_ be present in a given directory to confirm that the calculation
        is of a certain type.

    Returns
    -------
    str
        The type of calculation that the directory contains. The available
        options are found in DEFAULT_INPUT_FILES.
    """

    contained = {xx.parts[-1] for xx in list(Path(root).iterdir())}
    overlap = {
        key: set(value).issubset(contained)
        for key, value in input_files.items()
    }

    # Check to see if for some reason there are multiple computations' input
    # files in one directory. This obvious is a problem.
    N = sum(list(overlap.values()))
    if N != 1:
        if N < 1:
            logger.warning(f"No matching input files found in {root}")
        elif N > 1:
            logger.error(f"More than one type of calculation found in {root}")
        return None

    # Otherwise, we simply find which one is true
    calc_type = [key for key, value in overlap.items() if value][0]
    logger.debug(f"{root} identified as {calc_type}")
    return calc_type


def check_job_status(root, checks):
    """Checks the status of a job by looking in the directory of interest for
    the appropriate completion status. This function does not check that the
    provided root directory actually corresponds to the type of calculation
    provided will error ungracefully if it does not contain the appropriate
    files. Output files have their last 100 lines checked.

    Parameters
    ----------
    root : os.PathLike
        The directory containing input and output files.
    checks : list of list of str
        A doubly nested list. The outer lists correspond to filename-substring
        pairs. If the substring is None, then this will simply check whether or
        not the file exists and is not empty.

    Returns
    -------
    bool
        True if the job has completed successfully, False otherwise.
    """

    for filename, substring in checks:
        path = Path(root) / Path(filename)
        logger.debug(f"Running checks {checks} on {path}")

        # Check for existence and that the file size is > 0
        if substring is None:
            if not path.exists():
                logger.debug(f"{path} does not exist - status FALSE")
                return False
            if path.stat().st_size == 0:
                logger.debug(f"{path} is empty - status FALSE")
                return False
        else:
            command = f"tail -n 100 {str(path)}"
            res = run_command(command)
            lines = res["stdout"].split("\n")
            cond = check_if_substring_match(lines, str(substring))

            if not cond:
                logger.debug(f"{path} missing {substring} - status FALSE")
                return False

    logger.debug(f"{path} - status TRUE")
    return True


def generate_report(root, filename, output_files=CONFIG["out"]):
    """Generates a report of which jobs have finished, which are still ongoing
    and which have failed. Currently, returns True if the job completed with
    seemingly no issues, and False otherwise.

    .. warning::

        If the directories of interest cannot be identified, None will be
        returned. This happens if check_computation_type returns None. Warnings
        are issued in this case, and these directories will be ignored.

    Notes
    -----
    What is checked given some calculation type is detailed below:
    * VASP: If the job completed, the OUTCAR file will contain timing
    information.
    * FEFF: If the job completed, there will be a non-empty xmu.dat file.

    Parameters
    ----------
    root : os.PathLike
        Root location for the exhaustive directory search.
    filename : str
        Looks exhaustively in root for directories containing a file matching
        this name.
    identifiers : dict, optional
        A dictionary containing strings as keys, which identify the computation
        type, and sets as values, which identify input files that all must be
        contained in the directory to identify the directory as corresponding
        to a certain computation type. Default is DEFAULT_INPUT_FILES.

    Returns
    -------
    dict
        A dictionary with keys as the paths to the directories checked and
        boolean values, indicating the success status of the calculation.
    """

    logger.info(f"Generating report at {root} (searching for {filename})")

    # Get the directories matching the filename of the directory search
    directories = exhaustive_directory_search(root, filename)

    # For each directory in the tree, determine the type of calculation that
    # was run.
    calculation_types = {dd: check_computation_type(dd) for dd in directories}
    calculation_types = {
        key: value
        for key, value in calculation_types.items()
        if value is not None
    }
    cc = Counter(list(calculation_types.values()))

    # Get the statuses
    status = dict()
    complete = {ctype: 0 for ctype in cc.keys()}
    report = {ctype: {"success": [], "fail": []} for ctype in cc.keys()}
    for dd, ctype in calculation_types.items():
        checks = output_files[ctype] if ctype is not None else None
        status[dd] = check_job_status(dd, checks=checks)
        complete[ctype] += int(status[dd])

        if status[dd]:
            report[ctype]["success"].append(str(dd))
        else:
            report[ctype]["fail"].append(str(dd))

    for ctype, ncomplete in complete.items():
        if ncomplete == cc[ctype]:
            logger.success(f"{ctype}: all {ncomplete} complete")
        else:
            logger.warning(f"{ctype} incomplete: {ncomplete}/{cc[ctype]}")

    return report
