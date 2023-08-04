"""The tether module is designed to perform non-trivial actions to construct
submission scripts. For example, consider a situation where you have many jobs
to submit, but each job is cheap and does not require significant
parallelization. Perhaps each job is even faster than a minute (the minimum
cronjob time)."""

from copy import copy
from math import floor, log10
from pathlib import Path
import sys

from autojob import logger
from autojob.file_utils import exhaustive_directory_search


def chunks(original_list, chunk_size):
    """See https://stackoverflow.com/questions/312443/
    how-do-you-split-a-list-into-evenly-sized-chunks.

    Parameters
    ----------
    original_list : list
    chunk_size : int

    Yields
    ------
    list
    """

    for ii in range(0, len(original_list), chunk_size):
        yield original_list[ii : ii + chunk_size]


def get_file_lines(slurm_header_lines, chunk, executable_line):
    file_lines = copy(slurm_header_lines) + [""]
    for dd in chunk:
        file_lines.append(f"cd {dd.absolute()}")
        file_lines.append(executable_line)
    file_lines.append("\nwait\nexit")
    return file_lines


def tether_constructor(
    root,
    filename,
    staging_directory,
    calculations_per_staged_job,
    slurm_header_lines,
    executable_line,
):
    """The tether constructor. Writes composite SLURM jobs.

    Parameters
    ----------
    root : os.PathLike
        The path (absolute or relative) to the directory from which to conduct
        the exhaustive search.
    filename : str
        The exact name of the file which identifies a directory as one of
        interest.
    staging_directory : os.PathLike
        The directory to place the submit scripts.
    calculations_per_staged_job : int
        The number of calculations per composite staged job. Usually this
        should be more or less equal to the number of cores on a node.
    slurm_header_lines : list of str
        The lines for the SLURM job header.
    executable_line : str
        The executable line. Should end in a & such that multiple jobs can
        be run in parallel.
    """

    if "&" not in executable_line[-2:]:
        logger.critical(
            f"& is not found at the end of executable line {executable_line}. "
            "These are required for the tether_constructor to allow jobs to "
            "run in parallel. Tether has not written anything. Exiting."
        )
        sys.exit(1)

    logger.info(f"Tethering jobs for {root}, looking for filename {filename}")
    logger.info(f"Staging to {staging_directory}")
    logger.info(f"Calculations per staged job: {calculations_per_staged_job}")
    logger.info(f"Executable line: {executable_line}")
    logger.debug(f"Slurm header is {slurm_header_lines}")

    directories = exhaustive_directory_search(root, filename)
    logger.info(f"Found {len(directories)} file matches")

    chunked_directories = list(chunks(directories, calculations_per_staged_job))
    submit_script_lines = []
    for chunk in chunked_directories:
        # For each chunk, we write a single SLURM script which changes
        # directories into the one where the executable should be
        lines = get_file_lines(slurm_header_lines, chunk, executable_line)
        submit_script_lines.append(lines)

    # Now save those jobs to the appropriate directory structure
    L = len(submit_script_lines)
    logger.info(f"Saving {L} submit scripts to staging directory")
    oom = floor(log10(L)) + 1
    target_root = Path(staging_directory)
    for ii, submit_script in enumerate(submit_script_lines):
        dd = target_root / Path(str(ii).zfill(oom))
        dd.mkdir(exist_ok=False, parents=True)
        with open(dd / Path("submit.sbatch"), "w") as f:
            for line in submit_script:
                f.write(f"{line}\n")
