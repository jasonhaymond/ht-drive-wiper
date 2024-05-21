import os
import subprocess
import threading
import time
from flask import Flask, render_template, request, jsonify
from smtp_setup import send_email  # Import the send_email function from smtp_setup

app = Flask(__name__)

# Store the status and subprocess of each wipe process
status = {}
processes = {}

# Function to get USB port information using udevadm
def get_usb_port(device):
    try:
        result = subprocess.run(['udevadm', 'info', '--query=property', '--name', device], capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if 'ID_PATH=' in line:
                return line.split('=')[1]
    except Exception as e:
        print(f"Error getting USB port for {device}: {e}")
    return "Unknown"

# Function to check if a drive is external
def is_external_drive(device):
    try:
        result = subprocess.run(['udevadm', 'info', '--query=property', '--name', device], capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if 'ID_BUS' in line and 'usb' in line:
                return True
    except Exception as e:
        print(f"Error checking if drive is external for {device}: {e}")
    return False

# Function to get connected hard drives information
def get_hard_drives():
    drives = []
    try:
        result = subprocess.run(['lsblk', '-o', 'NAME,SERIAL,MODEL,SIZE,TYPE'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        for line in lines:
            parts = line.split()
            if 'disk' in parts:
                device_name = parts[0]
                device_path = f"/dev/{device_name}"
                if not is_external_drive(device_path):
                    continue
                usb_port = get_usb_port(device_path)
                drive = {
                    'name': device_name,
                    'serial': parts[1] if parts[1] != "-" else "Unknown",
                    'model': parts[2],
                    'size': parts[3],
                    'device_path': device_path,
                    'usb_port': usb_port,
                    'error': ""
                }
                drives.append(drive)
    except Exception as e:
        drives.append({
            'name': 'Unknown',
            'serial': 'Unknown',
            'model': 'Unknown',
            'size': 'Unknown',
            'device_path': 'Unknown',
            'usb_port': 'Unknown',
            'error': f"Error getting drives: {e}"
        })
    return drives

# Simulated function to track progress and add a fingerprint file after wipe
def track_progress_and_fingerprint(device, passes):
    for i in range(passes):
        time.sleep(5)  # Simulate time taken for each pass
        status[device] = f"Pass {i + 1} of {passes} completed"
    status[device] = "Completed"
    try:
        with open(os.path.join(device, 'wipe_fingerprint.txt'), 'w') as f:
            f.write("Drive successfully wiped.")
    except Exception as e:
        status[device] = f"Completed with error writing fingerprint: {e}"

# Function to send email report
def send_wipe_report(device, output, error, exit_code):
    email_message = f"Drive Wipe Report:\nDrive: {device}\nOutput: {output}\nError: {error}\nExit Code: {exit_code}"
    send_email(email_message)  # Call the send_email function to send the email report

# Route to render the main page
@app.route('/')
def index():
    drives = get_hard_drives()
    no_drives_message = "No external drives connected." if not drives else None
    return render_template('index.html', drives=drives, no_drives_message=no_drives_message)

# Route to start the wiping process
@app.route('/wipe', methods=['POST'])
def wipe():
    wipe_requests = request.json
    results = []

    for wipe_request in wipe_requests:
        device = wipe_request['device']
        passes = int(wipe_request['passes'])
        zero_pass = 'yes' if wipe_request['zero_pass'] else 'no'

        command = ['shred', '-v', '-n', str(passes)]
        if zero_pass == 'yes':
            command.append('-z')
        command.append(device)

        status[device] = "Started"
        
        try:
            process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)
            processes[device] = process
            # Start a thread to simulate progress tracking and error logging
            threading.Thread(target=track_progress_and_fingerprint, args=(device, passes)).start()
            threading.Thread(target=log_errors, args=(device, process)).start()
            results.append({'device': device, 'status': 'started'})
        except Exception as e:
            results.append({'device': device, 'status': 'error', 'message': str(e)})

    return jsonify(results)

def log_errors(device, process):
    error_messages = []
    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            error_messages.append(output.strip())
            status[device] = '<br>'.join(error_messages)

            # Check if the process has completed
            if process.poll() is not None:
                output, _ = process.communicate()
                exit_code = process.returncode
                send_wipe_report(device, output, '<br>'.join(error_messages), exit_code)  # Send email report
                break

# Route to stop the wiping process
@app.route('/stop', methods=['POST'])
def stop():
    device = request.json['device']
    if device in processes:
        processes[device].terminate()
        processes[device].wait()
        status[device] = "Stopped"
        del processes[device]
        return jsonify({'device': device, 'status': 'stopped'})
    return jsonify({'device': device, 'status': 'not found'})

# Route to get the status of the wipe process
@app.route('/status')
def get_status():
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)
