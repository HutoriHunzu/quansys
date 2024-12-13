import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
MONITOR_DIR = '/path/to/your/directory'  # Root directory to monitor
STATUS_FILE = 'status'  # File that contains "pending"
SUBMIT_SCRIPT = 'submit.sh'  # Script to execute if condition is met
N = 5  # Threshold for the number of running jobs


# Function to query the number of running jobs for the user
def get_running_jobs(username):
    try:
        # Run bjobs command to get jobs for the given username
        result = subprocess.run(
            ['bjobs', '-u', username],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            # Filter the output to count the number of jobs
            lines = result.stdout.splitlines()
            # Skip the header and count non-header lines (which are jobs)
            job_count = sum(1 for line in lines[1:] if line.strip())
            return job_count
        else:
            print(f"Error while fetching jobs: {result.stderr}")
            return 0
    except Exception as e:
        print(f"Error while running bjobs command: {e}")
        return 0


# Function to submit the job if conditions are met
def submit_job(subdirectory):
    try:
        submit_script_path = os.path.join(subdirectory, SUBMIT_SCRIPT)
        if os.path.exists(submit_script_path):
            print(f"Submitting job in {subdirectory}...")
            subprocess.run(['bash', submit_script_path], check=True)
        else:
            print(f"Submit script not found in {subdirectory}")
    except Exception as e:
        print(f"Error while submitting job: {e}")


# Function to handle directory changes
class DirectoryEventHandler(FileSystemEventHandler):
    def __init__(self, monitored_directory):
        self.monitored_directory = monitored_directory

    def on_modified(self, event):
        if event.is_directory:
            self.check_subdirectory(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            self.check_subdirectory(event.src_path)

    def check_subdirectory(self, subdirectory):
        # Check if the status file exists and contains 'pending'
        status_file_path = os.path.join(subdirectory, STATUS_FILE)
        if os.path.exists(status_file_path):
            with open(status_file_path, 'r') as file:
                status_content = file.read().strip()
                if 'pending' in status_content:
                    # Check the number of running jobs
                    username = os.getenv('USER')  # Get the current user (make sure the environment variable is set)
                    running_jobs = get_running_jobs(username)
                    print(f"User {username} has {running_jobs} running jobs.")

                    if running_jobs < N:
                        # Submit the job if conditions are met
                        submit_job(subdirectory)


# Monitor the directory
def start_monitoring():
    event_handler = DirectoryEventHandler(MONITOR_DIR)
    observer = Observer()
    observer.schedule(event_handler, MONITOR_DIR, recursive=True)
    observer.start()
    print(f"Monitoring directory: {MONITOR_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_monitoring()
