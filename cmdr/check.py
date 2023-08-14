from cmdr.file_utils import exhaustive_directory_search, run_command


def check(
    search_directory,
    filename,
    check_for_line,
    report_path,
):
    """Summary
    
    Parameters
    ----------
    search_directory : TYPE
        Description
    filename : TYPE
        Description
    check_for_line : TYPE
        Description
    report_path : TYPE
        Description
    """

    fnames = sorted(
        exhaustive_directory_search(
            search_directory, filename, return_filename=True
        )
    )
    print(f"Found a total of {len(fnames)} corresponding to {filename}")

    grepped = [
        run_command(f"grep '{check_for_line}' {str(f)}")["exitcode"]
        for f in fnames
    ]

    grepped = [f for f, g in zip(fnames, grepped) if int(g) == 1]

    if len(grepped) > 0:
        print(f"Failed jobs: {len(grepped)}")
        with open(report_path, "w") as f:
            f.write("# Failed jobs\n")
            for line in grepped:
                f.write(f"{line}\n")
    else:
        print("No jobs failed, no report to write")
