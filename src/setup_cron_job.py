import os
import subprocess
from pathlib import Path

def setup_cron_job():
    python_path = subprocess.getoutput("which python3")  # Detect Python path
    script_path = Path(__file__).parent / "email_invoice.py"
    cron_job = f"0 0 * * * {python_path} {script_path} >> {script_path.parent}/sendlog.txt 2>&1"

    # Read existing cron jobs
    current_cron = subprocess.getoutput("crontab -l")
    
    if cron_job in current_cron:
        print("Cron job already exists.")
        return

    new_cron = current_cron + "\n" + cron_job if current_cron else cron_job
    subprocess.run(f"(echo '{new_cron}') | crontab -", shell=True)
    print("Cron job added to run send_pdfs.py daily at 12 AM.")

if __name__ == "__main__":
    setup_cron_job()
