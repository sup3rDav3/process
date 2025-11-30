import argparse
import subprocess
import os
import datetime
import sys

# Config
PROGRAM_TO_CHECK = "xxxx"    # Name of the process/program (e.g., 'nginx', 'java', 'gunicorn')
FILE_TO_TRANSFER = "test.txt"           # Local file to archive if the program is NOT running
ARCHIVE_FILENAME = "moveme.zip" # Local name for the encrypted zip archive
REMOTE_USER = "foo"             # SSH user on remote host
REMOTE_HOST = "172.168.1.100"           # IP address or hostname of the remote server
REMOTE_PATH = "/home/me/Desktop/monitor/rec/"      # Destination path on remote host (must end with '/')
SSH_KEY_PATH = "/home/me/.ssh/id_rsa" # Path to the private key file (e.g., ~/.ssh/id_rsa)
ENCRYPTION_PASSWORD = "STRONG_PASSWORD"      # Password for the zip file encryption
# ---------------------

def log_message(message, silent_mode):
    """Prints a message unless silent mode is active."""
    if not silent_mode:
        print(message)

def check_process_running(program_name, silent_mode):
    """
    Checks if a process with the exact name is currently running using pgrep.
    Returns True if running, False otherwise.
    """
    log_message(f"Checking status for program: '{program_name}'...", silent_mode)
    try:
        # Use pgrep -x (exact match) and redirect output to /dev/null
        # If pgrep finds the process, it returns exit code 0.
        result = subprocess.run(
            ['pgrep', '-x', program_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except FileNotFoundError:
        log_message("Error: 'pgrep' utility not found. Cannot check process status.", silent_mode)
        return False
    except Exception as e:
        log_message(f"An unexpected error occurred during process check: {e}", silent_mode)
        return False

def execute_transfer_logic(silent_mode):
    """
    Handles file existence check, zipping, encryption, SCP transfer, and cleanup.
    """
    log_message(f"Status: '{PROGRAM_TO_CHECK}' is NOT running (PID not found). Initiating file transfer check...", silent_mode)

    if not os.path.exists(FILE_TO_TRANSFER):
        log_message(f"WARNING: Local file '{FILE_TO_TRANSFER}' not found. Transfer skipped.", silent_mode)
        return

    log_message(f"Found local file: {FILE_TO_TRANSFER}. Preparing encrypted ZIP archive...", silent_mode)

    # Remote filename with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_filename = f"backup_{timestamp}.zip"
    
    # ZIP and ENCRYPT the file
    # We use the zip command directly as it provides the most compatible encryption method
    try:
        zip_command = [
            'zip', 
            '-e',                      # Enable encryption
            '-P', ENCRYPTION_PASSWORD, # Set password
            ARCHIVE_FILENAME, 
            FILE_TO_TRANSFER
        ]
        
        # Suppress zip output entirely if silent_mode is requested
        stdout_redirect = subprocess.DEVNULL if silent_mode else None

        zip_result = subprocess.run(
            zip_command, 
            check=True, # Raise exception if zip fails
            stdout=stdout_redirect, 
            stderr=stdout_redirect
        )
        
        log_message(f"SUCCESS: File successfully zipped and encrypted locally as {ARCHIVE_FILENAME}.", silent_mode)

    except subprocess.CalledProcessError:
        log_message("FAILURE: Could not create or encrypt the ZIP archive. Check if 'zip' is installed.", silent_mode)
        return
    except FileNotFoundError:
        log_message("Error: 'zip' utility not found. Please install the zip package.", silent_mode)
        return
    
    # SCP transfer of the ENCRYPTED ZIP archive
    try:
        remote_target = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}{remote_filename}"
        log_message(f"Attempting SCP transfer of {ARCHIVE_FILENAME} to {REMOTE_HOST} as {remote_filename}...", silent_mode)

        scp_command = [
            'scp',
            '-i', SSH_KEY_PATH,        # Use specified SSH key
            '-o', 'BatchMode=yes',     # Prevent password prompt (required for automation)
            ARCHIVE_FILENAME,
            remote_target
        ]

        # Use stdout_redirect defined earlier
        scp_result = subprocess.run(
            scp_command,
            check=True, # Raise exception if scp fails
            stdout=stdout_redirect,
            stderr=stdout_redirect
        )
        
        log_message(f"SUCCESS: Encrypted archive transferred successfully and renamed to {remote_filename}.", silent_mode)
        
        # 4. Clean up the local archive file
        os.remove(ARCHIVE_FILENAME)
        log_message(f"Cleanup: Local archive {ARCHIVE_FILENAME} removed.", silent_mode)

    except subprocess.CalledProcessError:
        log_message("FAILURE: SCP transfer failed. Check SSH key path/permissions, remote path, and network connection.", silent_mode)
        log_message("The local archive was kept for manual inspection.", silent_mode)
    except FileNotFoundError:
        log_message("Error: 'scp' utility not found. Please ensure OpenSSH client is installed.", silent_mode)
    except Exception as e:
        log_message(f"An unexpected error occurred during transfer/cleanup: {e}", silent_mode)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Conditional Program Status Check and Encrypted File Transfer Script.")
    parser.add_argument('-s', '--silent', action='store_true', help='Suppress all script output (stdout and stderr).')
    args = parser.parse_args()
    
    silent_mode = args.silent

    log_message("==========================================", silent_mode)
    log_message(f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", silent_mode)
    log_message(f"Hostname: {os.uname().nodename}", silent_mode)
    log_message("------------------------------------------", silent_mode)

    if check_process_running(PROGRAM_TO_CHECK, silent_mode):
        log_message(f"Status: '{PROGRAM_TO_CHECK}' is running. No transfer initiated.", silent_mode)
    else:
        execute_transfer_logic(silent_mode)
        
    log_message("==========================================", silent_mode)
    log_message("Done.", silent_mode)

if __name__ == "__main__":
    main()
