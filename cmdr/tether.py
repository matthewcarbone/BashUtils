"""The tether module is designed to perform non-trivial actions to construct
submission scripts. For example, consider a situation where you have many jobs
to submit, but each job is cheap and does not require significant
parallelization. Perhaps each job is even faster than a minute (the minimum
cronjob time)."""

from math import floor, log10, ceil
import numpy as np
from pathlib import Path

from rich.pretty import pprint
from cmdr.file_utils import exhaustive_directory_search


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

    L = len(original_list)
    chunks = ceil(L / chunk_size)
    return np.array_split(original_list, chunks)


def get_file_lines(slurm_config, chunk, executable_lines, post_slurm_lines):
    """Summary

    Parameters
    ----------
    slurm_config : TYPE
        Description
    chunk : TYPE
        Description
    executable_lines : TYPE
        Description
    post_slurm_lines : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """

    lines = ["#!/bin/bash"]
    lines = lines + [
        f"#SBATCH --{key}={value}" for key, value in slurm_config.items()
    ]
    lines[-1] += "\n"
    if len(post_slurm_lines) > 0:
        lines = lines + post_slurm_lines
        lines[-1] += "\n"

    for dd in chunk:
        lines.append(f"cd {dd.absolute()}")
        for exe_line in executable_lines:
            lines.append(exe_line)
    lines.append("\nwait\nexit")
    return lines


def get_dummy_SLURM(slurm_keys):
    lines = (
        ["#!/bin/bash"]
        + [f"#SBATCH --{key}={value}" for key, value in slurm_keys.items()]
        + ["\ncd ...", "echo test\n", "cd ...", "echo test\n"]
    )
    pprint(lines)


def tether_constructor(
    search_directory,
    filename,
    tether_directory,
    calculations_per_staged_job=36,
    slurm_header_lines={"job-name": "test_job"},
    post_slurm_lines=[],
    executable_lines=["echo test"],
):
    """The tether constructor. Writes composite SLURM jobs.

    Parameters
    ----------
    search_directory : os.PathLike
        The path (absolute or relative) to the directory from which to conduct
        the exhaustive search.
    filename : str
        The exact name of the file which identifies a directory as one of
        interest.
    tether_directory : os.PathLike
        The directory to place the submit scripts.
    calculations_per_staged_job : int
        The number of calculations per composite staged job. Usually this
        should be more or less equal to the number of cores on a node.
    slurm_header_lines : dict
        The keys and values for the SLURM file. For example, if the dictionary
        is {"job-name": "test""}, then "#SBATCH --job-name=test" will be
        written to the SLURM file.
    post_slurm_lines : list, optional
        ...
    executable_lines : list
        A list of commands which are executed, in order, after changing
        directory to all directories found matching the provided filename.
    """

    print(
        f"Tethering jobs for {search_directory}, looking for filename {filename}"
    )
    print(f"Staging to {tether_directory}")
    print(f"Calculations per staged job: {calculations_per_staged_job}")

    directories = sorted(
        exhaustive_directory_search(search_directory, filename)
    )
    print(f"Found a total of {len(directories)} corresponding to {filename}")

    chunked_directories = list(
        chunks(directories, calculations_per_staged_job)
    )
    submit_script_lines = []
    for chunk in chunked_directories:
        # For each chunk, we write a single SLURM script which changes
        # directories into the one where the executable should be
        lines = get_file_lines(
            slurm_header_lines, chunk, executable_lines, post_slurm_lines
        )
        submit_script_lines.append(lines)

    # Now save those jobs to the appropriate directory structure
    L = len(submit_script_lines)
    print(f"Saving {L} submit scripts to staging directory")
    oom = floor(log10(L)) + 1
    target_search_directory = Path(tether_directory)
    for ii, submit_script in enumerate(submit_script_lines):
        dd = target_search_directory / Path(str(ii).zfill(oom))
        dd.mkdir(exist_ok=False, parents=True)
        with open(dd / Path("submit.sbatch"), "w") as f:
            for line in submit_script:
                f.write(f"{line}\n")
