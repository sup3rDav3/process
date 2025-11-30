#!/bin/bash
#
# Checks if a critical program is running. If not, it attempts to
# locate and transfer a backup file (test.txt) via SCP to a remote host.
#
# REQUIREMENTS:
# - Common utilities: pgrep, scp
# - SCP requires that SSH keys are set up for passwordless transfer,
#   	copy key to server: ssh-copy-id foo@192.168.1.170
#  	
# - silent mode: bash 2.sh &> /dev/null

# Check for -s or --silent flag and suppress all output
for arg in "$@"; do
    if [ "$arg" == "-s" ] || [ "$arg" == "--silent" ]; then
        # Redirect stdout (1) and stderr (2) to /dev/null
        exec 1>/dev/null 2>&1
        break
    fi
done

# Config
PROGRAM_TO_CHECK="aaa"		# Process Name
FILE_TO_TRANSFER="test.txt"	# File to transfer if the program is NOT running
REMOTE_USER="foo"          	# SSH user on remote host
REMOTE_HOST="172.168.1.100"  	# Remote host IP
REMOTE_PATH="/home/me/Desktop/monitor/"   # Destination path on remote host (must end with '/')
REMOTE_FILENAME="backup_$(date +%Y%m%d_%H%M%S).zip" # Remote filename. Uses date/time stamp for uniqueness.
SSH_KEY_PATH="/home/me/.ssh/id_rsa" # Path to the private key file (e.g., ~/.ssh/id_rsa)
ENCRYPTION_PASSWORD="SUPERSTRONGPASS"      # Zip encryption password
ARCHIVE_FILENAME="moveme.zip"   # Local name for the encrypted zip file (will be created/overwritten)

echo "=========================================="
echo "Date/Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Hostname: $(hostname)"
echo "------------------------------------------"

# pgrep -x looks for an exact match of the process name
if pgrep -x "$PROGRAM_TO_CHECK" > /dev/null; then
    echo "Status: '$PROGRAM_TO_CHECK' is running (PID found). No transfer initiated."
else
    echo "Status: '$PROGRAM_TO_CHECK' is NOT running (PID not found). Initiating file transfer check..."

    if [ -f "$FILE_TO_TRANSFER" ]; then
        echo "Found local file: $FILE_TO_TRANSFER. Preparing encrypted ZIP archive..."
        
        # 2. ZIP and ENCRYPT the file with the specified password
        # -e enables encryption, -P sets the password
        if zip -e -P "$ENCRYPTION_PASSWORD" "$ARCHIVE_FILENAME" "$FILE_TO_TRANSFER" > /dev/null; then
            
            echo -e "[!] SUCCESS: File successfully zipped and encrypted locally as $ARCHIVE_FILENAME."
            
            # 3. Perform SCP transfer of the ENCRYPTED ZIP archive
            echo -e "Attempting SCP transfer of $ARCHIVE_FILENAME to ${REMOTE_HOST} as ${REMOTE_FILENAME}..."
            
            if scp -q -i "$SSH_KEY_PATH" -o BatchMode=yes "$ARCHIVE_FILENAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}${REMOTE_FILENAME}"; then
                echo -e "[!] SUCCESS: Encrypted archive transferred successfully."
                
                # 4. Clean up the local archive file
                rm -f "$ARCHIVE_FILENAME"
                echo "Cleanup: Local archive $ARCHIVE_FILENAME removed."

            else
                echo "FAILURE: SCP transfer of $ARCHIVE_FILENAME failed. Check SSH key permissions and network connection."
                # Keep the local archive for manual inspection if transfer fails
            fi
            
        else
            echo "FAILURE: Could not create or encrypt the ZIP archive. Check if 'zip' is installed."
        fi
        
    else
        echo "WARNING: Local file '$FILE_TO_TRANSFER' not found in the current directory. Transfer skipped."
    fi
fi

echo "=========================================="
echo "[Done]"
