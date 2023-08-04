"""The autojob code contains a complete set of default files based on the
developers' primary use cases. These defaults are enumerated in this core
module. The user can override any and all defaults by providing their own
config files in `~/.autojob`. This directory will be created if it does not
exist, and any config files in the defaults that do not exist in the directory
will be created if they do not exist (TODO)."""

from pathlib import Path
import sys

from loguru import logger

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions


def generic_filter(names):
    if names == "all":
        return None

    def f(record):
        return record["level"].name in names

    return f


logger.remove(0)  # Remove the default logger

# Determine the debugging status of the execution. If we're running pytest or
# the debug flag is present, we'll want to run in debugging mode.
DEBUG = False
if "pytest" in sys.argv[0] or any(["--debug" in xx for xx in sys.argv]):
    DEBUG = True


OUT_FMT = "<lvl>{message}</>"
ERR_FMT = "<lvl>{level}:</> <lvl>{message}</>"
FMT2 = (
    "<w>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "<w>{name}</>:<w>{function}</>:<w>{line}</> "
    "[<lvl>{level}</>] <lvl>{message}</>"
)


STDOUT_LOGGER_ID = logger.add(
    sys.stdout,
    colorize=True,
    filter=generic_filter(
        ["DEBUG", "INFO", "SUCCESS"] if DEBUG else ["INFO", "SUCCESS"]
    ),
    format=FMT2 if DEBUG else OUT_FMT,
)

STDERR_LOGGER_ID = logger.add(
    sys.stderr,
    colorize=True,
    filter=generic_filter(["WARNING", "ERROR", "CRITICAL"]),
    format=FMT2 if DEBUG else ERR_FMT,
)

# Don't bother logging the debugging logs if in DEBUG mode
if not DEBUG:
    ROOT = Path.home() / Path(".autojob")
    if not ROOT.exists():
        ROOT.mkdir(exist_ok=False, parents=True)
    LOGFILE_LOGGER_ID = logger.add(
        ROOT / Path("LOGS"),
        filter=generic_filter("all"),
        format=FMT2,
        rotation="100 MB",
    )
