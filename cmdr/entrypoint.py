import argparse
from argparse import HelpFormatter, ArgumentDefaultsHelpFormatter
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from rich.pretty import pprint
import sys

from cmdr.check import check
from cmdr.tether import tether_constructor
from cmdr.file_utils import run_command


NOW = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


# https://stackoverflow.com/questions/
# 12268602/sort-argparse-help-alphabetically
class SortingHelpFormatter(ArgumentDefaultsHelpFormatter, HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter("option_strings"))
        super(SortingHelpFormatter, self).add_arguments(actions)


def global_parser(sys_argv):
    ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter)

    ap.add_argument(
        "--debug",
        dest="debug",
        default=False,
        action="store_true",
        help="If specified, enables the DEBUG stream to stdout. This also "
        "changes the logging format to make it better for detecting issues.",
    )

    # --- Global options ---

    subparsers = ap.add_subparsers(help="Global options", dest="runtype")

    # WRANGLE

    wrangle_subparser = subparsers.add_parser(
        "wrangle",
        formatter_class=SortingHelpFormatter,
        description="...",   
    )

    wrangle_subparser.add_argument(
        "--directory",
        dest="directory",
        help="Directory to search for the file name",
        required=True,
    )

    wrangle_subparser.add_argument(
        "--user",
        dest="user",
        help="SLURM username",
        required=True,
    )

    wrangle_subparser.add_argument(
        "--maxjobs",
        dest="maxjobs",
        help="Max number of jobs to run concurrently",
        default=20,
        type=int
    )

    wrangle_subparser.add_argument(
        "--other",
        dest="other_args",
        help="A string of other arguments verbatim",
        default=None,
        type=str,
    )

    # TETHER

    tether_subparser = subparsers.add_parser(
        "tether",
        formatter_class=SortingHelpFormatter,
        description="Allows for tethering multiple jobs into a single job. "
        "See the documentation for more details.",
    )

    tether_subparser.add_argument(
        "--filename",
        dest="filename",
        help="File to search for, which is an indicator that is a directory "
        "in which you want to run a job",
        required=True,
    )

    tether_subparser.add_argument(
        "--directory",
        dest="search_directory",
        help="Directory to search for the file name",
        required=True,
    )

    tether_subparser.add_argument(
        "--tether-directory",
        dest="tether_directory",
        help="Directory to save the tether submit files in (if not provided, "
        "defaults to the search directory name with a _tether suffix)",
        default=None,
    )

    tether_subparser.add_argument(
        "-c",
        "--calculations-per-staged-job",
        dest="calculations_per_staged_job",
        help="Number of calculations per staged job",
        default=36,
        type=int,
    )

    tether_subparser.add_argument(
        "-l",
        "--exe-line",
        dest="executable_lines",
        action="append",
        help="Executable line to be run in every directory found",
        required=True,
    )

    tether_subparser.add_argument(
        "-p",
        "--post-slurm-line",
        dest="post_slurm_lines",
        action="append",
        help="Lines which are not SLURM commands but are rune once before "
        "other parts of the script are executed (such as export or module "
        "loading)",
        default=[],
    )

    tether_subparser.add_argument(
        "-s",
        "--slurm-line",
        dest="slurm_lines",
        action="append",
        help="Slurm parameter",
        required=True,
    )

    # CHECK

    check_subparser = subparsers.add_parser(
        "check",
        formatter_class=SortingHelpFormatter,
        description="Allows for quickly testing the status of output files."
        " Can be used to figure out quickly if jobs have completed "
        "successfully or not",
    )

    check_subparser.add_argument(
        "--filename",
        dest="filename",
        help="File to search for",
        required=True,
    )

    check_subparser.add_argument(
        "--directory",
        dest="search_directory",
        help="Directory to recursively search for the file name",
        required=True,
    )

    check_subparser.add_argument(
        "--require",
        dest="require_text",
        help="Requires that this text be found in the specified file",
        required=True,
    )

    check_subparser.add_argument(
        "--report-path",
        dest="report_path",
        help="Path to the report text file that will be saved",
        default="report.txt"
    )

    return ap.parse_args(sys_argv)


def entrypoint(args=sys.argv[1:]):
    """Point of entry from the command line interface.

    Raises
    ------
    RuntimeError
        If unknown runtime types are provided.
    """

    args = global_parser(args)
    pprint(args)
    print("-" * 80)

    if args.runtype == "wrangle":
        script_path = Path(__file__).parent / "scripts" / "slurm_wrangler.sh"
        s = f"{script_path} --user={args.user} --directory={args.directory} " \
            f"--maxjobs={args.maxjobs}"
        if args.other_args is not None:
            s += f" {args.other_args}"
        out = run_command(s)
        if out["exitcode"] != 0:
            pprint(out)
            raise RuntimeError("Error with slurm_wrangler")
        pprint(out["stdout"])

    elif args.runtype == "tether":
        slurm_lines = [xx.split("=") for xx in args.slurm_lines]
        slurm_lines = {key: value for (key, value) in slurm_lines}
        if args.tether_directory is None:
            tether_directory = f"{args.search_directory}_tether"
        else:
            tether_directory = args.tether_directory
        tether_constructor(
            args.search_directory,
            args.filename,
            tether_directory,
            args.calculations_per_staged_job,
            slurm_lines,
            args.post_slurm_lines,
            args.executable_lines,
        )

    elif args.runtype == "check":
        check(args.search_directory, args.filename, args.require_text, args.report_path)

    else:
        raise RuntimeError(f"Unknown runtime type {args.runtype}")
