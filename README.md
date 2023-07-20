# BashUtils

A collection of bash scripts for making life on HPC just a bit easier. All scripts are contained in the `scripts` directory. They can be run from anywhere on your computer, but it is recommended you install them to your `PATH`.

## Slurm Wrangler

The `slurm_wrangler.sh` script was designed to solve a personal problem of mine. What happens if your SLURM job controller only allows you to submit `MAXJOBS` jobs at a time? For me, this is about 40, and when I have thousands of jobs I need to queue, this can become a problem.

You might ask, but why not modify your code so that you don't need to submit thousands of jobs? I'm lazy, ok?

So, `slurm_wrangler.sh` fixes this problem. It does the following:

1. Installs itself into your `crontab`, such that it will, by default, run once/minute.
2. Every time the cron executes, it checks the directory you specified recursively for jobs that match `submit.sbatch` by default.
3. It checks the SLURM job controller for how many jobs you have queued under your username.
4. It subtracts the provided `MAXJOBS` from the number of jobs you have queued or running, and will attempt to execute only that number of jobs.
5. Every time a job is submitted, a file `QUEUED` is created in the directory where `submit.sbatch` was, such that it will not be resubmitted.
6. Once all jobs are queued, the script will remove itself from your crontab.

Note that in order for this to work, you need to have a `submit.sbatch` in every directory, setup in such a way that you `cd` to that directory, and run `sbatch submit.sbatch`.

### Usage

Using `slurm_wrangler.sh` is easy!

```bash
bash slurm_wrangler.sh
    [--user=<STR>]
    [--directory=<STR>]
    [--maxjobs=<INT>]
    [--cron=<STR>, "* * * * *"]
```

You must set your username, the directory you want to check recursively for `submit.sbatch` files, and the number of maximum jobs you want queued or running at once. Setting `cron` is optional, and defaults to `"* * * * *"` (once/min).
