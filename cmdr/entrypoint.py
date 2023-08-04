import argparse
from argparse import HelpFormatter, ArgumentDefaultsHelpFormatter
from datetime import datetime
from operator import attrgetter
from pathlib import Path
import sys

from autojob import logger
from autojob.report import generate_report
from autojob.tether import tether_constructor
from autojob.file_utils import save_json, read_json


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

    ap.add_argument(
        "--autojob-root",
        dest="autojob_root",
        default=Path.home() / Path(".autojob"),
    )

    # --- Global options ---

    subparsers = ap.add_subparsers(help="Global options", dest="runtype")

    report_subparser = subparsers.add_parser(
        "report",
        formatter_class=SortingHelpFormatter,
        description="Generates a report based on a recursive search of a "
        "directory. Different types of scientific calculations are supported, "
        "and are tabulated in the documentation. At the simplest level, a "
        "job is marked as successfully completed, failed or unknown.",
    )

    report_subparser.add_argument("root", help="Path to the directory to analyze.")

    report_subparser.add_argument(
        "-f",
        "--filename",
        dest="filename",
        default="submit.sbatch",
        help="Filename to search for.",
    )

    tether_subparser = subparsers.add_parser(
        "tether",
        formatter_class=SortingHelpFormatter,
        description="Allows for tethering multiple jobs into a single job. "
        "See the documentation for more details.",
    )

    tether_subparser.add_argument("root", help="Path to the directory to tether.")

    tether_subparser.add_argument(
        "--config",
        dest="config",
        default="feff",
        help="Reference to the configuration contained in "
        "$HOME/.autojob/tether. The .json suffix is omitted.",
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
    logger.debug(f"Command line args: {args}")

    if args.runtype == "report":
        d = generate_report(args.root, args.filename)
        save_json(d, Path(args.root) / Path("report.json"))

    elif args.runtype == "submit":
        pass

    elif args.runtype == "tether":
        config_root = args.autojob_root / Path("tether")
        config = read_json(config_root / Path(f"{args.config}.json"))
        staging_name = config["staging_directory"]
        if staging_name is None:
            staging_name = f"tether-staged-{NOW}"
        target_directory = Path.cwd() / Path(staging_name)
        tether_constructor(
            args.root,
            config["filename"],
            target_directory,
            config["calculations_per_staged_job"],
            config["slurm_header_lines"],
            config["executable"],
        )

    else:
        raise RuntimeError(f"Unknown runtime type {args.runtype}")
