from pathlib import Path
from tqdm import tqdm

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

    failed_no_file = []
    failed_no_line = []
    for d in tqdm(dirs):
        if not (Path(d) / require_filename).exists():
            failed_no_file.append(d)
            continue
        cmd = f"grep '{require_text}' {Path(d) / require_filename}"
        cmd = run_command(cmd)
        exitcode = cmd["exitcode"]
        if int(exitcode) == 1:
            failed_no_line.append(d)

    if len(failed_no_file) > 0 or len(failed_no_line) > 0:
        print(f"Failed (no file): {len(failed_no_file)}")
        print(f"Failed (no line): {len(failed_no_line)}")
        d = {"failed_no_file": failed_no_file, "failed_no_line": failed_no_line}
        save_json(d, report_path)
    else:
        print("No jobs failed, no report to write")
