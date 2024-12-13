import re
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field


# Pydantic model to hold job data
class JobInfo(BaseModel):
    job_id: int
    job_name: str
    user: str
    status: str
    max_mem: Optional[float] = None  # MAX MEM in GB (Optional)
    avg_mem: Optional[float] = None  # AVG MEM in GB (Optional)
    cpu_peak: Optional[float] = None  # CPU PEAK usage (Optional)
    cpu_avg_efficiency: Optional[float] = None  # CPU AVERAGE EFFICIENCY (Optional)

    class Config:
        # This ensures compatibility with attributes coming from dict-like objects
        from_attributes = True


# Function to parse bjobs -l output and extract relevant fields for multiple jobs
def parse_bjobs_output(stdout):
    # Regex patterns to match desired information
    job_id_pattern_with_capture = r"Job\s<(\d+)>"
    job_id_pattern_without_capture = r"Job\s<\d+>"

    splitting_pattern = fr'{job_id_pattern_with_capture}(.*?)(?=(?:{job_id_pattern_without_capture}|$))'

    job_name_pattern = r"Job Name\s<(?P<job_name>.*?)>"
    user_pattern = r"User\s<(?P<user>.*?)>"
    status_pattern = r"Status\s<(?P<status>.*?)>"

    # Adjust the memory patterns to match both Mbytes and Gbytes
    max_mem_pattern = r"MAX MEM:\s(?P<max_mem>\d+(\.\d+)?)\s(Mbytes|Gbytes)"
    avg_mem_pattern = r"AVG MEM:\s(?P<avg_mem>\d+(\.\d+)?)\s(Mbytes|Gbytes)"

    cpu_peak_pattern = r"CPU PEAK:\s(?P<cpu_peak>\d+(\.\d+)?)"
    cpu_efficiency_pattern = (
        r"CPU AVERAGE EFFICIENCY:\s(?P<cpu_avg_efficiency>\d+(\.\d+)?)%"
    )

    # Combine all the patterns
    patterns = {
        # "job_id": job_id_pattern,
        "job_name": job_name_pattern,
        "user": user_pattern,
        "status": status_pattern,
        "max_mem": max_mem_pattern,
        "avg_mem": avg_mem_pattern,
        "cpu_peak": cpu_peak_pattern,
        "cpu_avg_efficiency": cpu_efficiency_pattern,
    }

    jobs = []
    job_data = {}

    # Split stdout by job block (jobs are separated by a blank line or multiple lines)
    job_id_blocks = re.findall(splitting_pattern, stdout, re.DOTALL)

    # Iterate through each job block and parse the information
    for job_id_block in job_id_blocks:

        # print(block)
        job_data.clear()

        job_id, block = job_id_block
        job_data['job_id'] = job_id

        for field, pattern in patterns.items():
            m = re.search(pattern, block)
            if m:
                value = m.group(field)

                match field:

                    case "max_mem":
                        unit = m.group(3)
                        if unit == "Mbytes":
                            job_data["max_mem"] = float(value) / 1024  # Convert MB to GB
                        else:
                            job_data["max_mem"] = float(value)  # Already in GB

                    case "avg_mem":
                        unit = m.group(3)
                        if unit == "Mbytes":
                            job_data["avg_mem"] = float(value) / 1024  # Convert MB to GB
                        else:
                            job_data["avg_mem"] = float(value)  # Already in GB

                    # Convert CPU fields to float (if present)
                    case "cpu_peak":
                        job_data["cpu_peak"] = float(value)

                    case "cpu_avg_efficiency":
                        job_data["cpu_avg_efficiency"] = float(value)

                    case _:
                        job_data[field] = value

            # Create JobInfo instance and append it to the list
        jobs.append(JobInfo(**job_data))

    return jobs


# Function to fetch and parse bjobs -l output for all jobs
def get_all_jobs_info():
    try:
        # Run the bjobs -l command to get detailed information about all jobs
        result = subprocess.run(
            ["bjobs", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode == 0:
            # Parse the output for all jobs
            jobs = parse_bjobs_output(result.stdout)

            # Return the list of job info objects
            return jobs
        else:
            print(f"Error while fetching jobs: {result.stderr}")
            return []

    except Exception as e:
        print(f"Error running bjobs command: {e}")
        return []


# Example usage:
if __name__ == "__main__":

    sample_text = """
    
Job <121002>, Job Name <hfss_job>, User <goldblau>, Project <default>, User Gro
                     up <serger-wx-grp-lsf>, Status <RUN>, Queue <short>, Job P
                     riority <50>, Command </home/projects/serger/goldblau/play
                     ground/test_5/simulation_script.sh>, Share group charged <
                     /goldblau>, Esub <mem nonre group gpu outerr queuemirror>
Thu Dec 12 16:31:03: Submitted from host <login1>, CWD <$HOME/playground>, Spec
                     ified CWD <$HOME/playground/test_5>, Output File (overwrit
                     e) <lsf_output_121002.log>, Error File (overwrite) <lsf_er
                     ror_121002.err>, Re-runnable, 6 Task(s), Requested Resourc
                     es < rusage[mem=50000] span[hosts=1]>;
Thu Dec 12 16:31:05: Started 6 Task(s) on Host(s) <6*cn809>, Allocated 6 Slot(s
                     ) on Host(s) <6*cn809>, Execution Home </home/projects/ser
                     ger/goldblau>, Execution CWD </home/projects/serger/goldbl
                     au/playground/test_5>;
Thu Dec 12 16:41:33: Resource usage collected.
                     The CPU time used is 1498 seconds.
                     MEM: 1.2 Gbytes;  SWAP: 0 Mbytes;  NTHREAD: 276
                     PGID: 1487356;  PIDs: 1487356 1487374 1487376 1488015
                     1488467 1489700 1495193 1495492 1496263 1496363 1498573
                     1498847
                     PGID: 1498850;  PIDs: 1498850 1498962

 RUNLIMIT
 480.0 min

 MEMLIMIT
   48.8 G

 MEMORY USAGE:
 MAX MEM: 13.7 Gbytes;  AVG MEM: 4.5 Gbytes; MEM Efficiency: 4.70%

 CPU USAGE:
 CPU PEAK: 4.78 ;  CPU PEAK DURATION: 63 second(s)
 CPU AVERAGE EFFICIENCY: 38.10% ;  CPU PEAK EFFICIENCY: 79.63%

 PENDING TIME DETAILS:
 Eligible pending time (seconds):       2
 Ineligible pending time (seconds):     0

 SCHEDULING PARAMETERS:
           r15s   r1m  r15m   ut      pg    io   ls    it    tmp    swp    mem
 loadSched 10.0    -     -     -       -     -    -     -     -      -     15G
 loadStop  15.0    -     -     -       -     -    -     -     -      -      -

 RESOURCE REQUIREMENT DETAILS:
 Combined: select[(type = any &&mem>15360.00) && (type == any)] order[-slots:-m
                     axslots:-mem] rusage[mem=50000.00] span[hosts=1] affinity[
                     thread(1)*1]
 Effective: select[((type = any &&mem>15360.00) && (type == any))] order[-slots
                     :-maxslots:-mem] rusage[mem=50000.00] span[hosts=1] affini
                     ty[thread(1)*1]

    
    """

    jobs = parse_bjobs_output(sample_text)

    for job in jobs:
        print(job)
