from pathlib import Path

from cmdr.file_utils import exhaustive_directory_search, run_command, save_json


def check(
    search_directory,
    search_filename,
    require_filename,
    require_text,
    report_path,
):
    """Summary
    
    Parameters
    ----------
    search_directory : TYPE
        Description
    search_filename : TYPE
        Description
    require_filename : TYPE
        Description
    require_text : TYPE
        Description
    report_path : TYPE
        Description
    """

    dirs = sorted(
        exhaustive_directory_search(search_directory, search_filename)
    )
    dirs = [str(d) for d in dirs]
    print(f"Found a total of {len(dirs)} corresponding to {search_filename}")

    failed_no_file = [
        str(d) for d in dirs if not (Path(d) / require_filename).exists()
    ]

    dirs = list(set(dirs) - set(failed_no_file))

    grepped = [
        run_command(f"grep '{require_text}' {Path(d) / require_filename}")["exitcode"]
        for d in dirs
    ]

    failed_no_line = [d for d, g in zip(dirs, grepped) if int(g) == 1]

    if len(failed_no_file) > 0 or len(failed_no_line) > 0:
        print(f"Failed (no file): {len(failed_no_file)}")
        print(f"Failed (no line): {len(failed_no_line)}")
        d = {"failed_no_file": failed_no_file, "failed_no_line": failed_no_line}
        save_json(d, report_path)
    else:
        print("No jobs failed, no report to write")
