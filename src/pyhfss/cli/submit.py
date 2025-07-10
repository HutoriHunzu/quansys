
def submit_job(results_dir):
    import subprocess
    """
    Submit the job to the cluster using bsub.
    """
    job_script = results_dir / "job_submission.sh"
    if not job_script.exists():
        raise FileNotFoundError(f"{job_script} not found. Did you forget to prepare the job?")

    # Execute the job_submission.sh script
    subprocess.run(["bash", job_script], check=True)
