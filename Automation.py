import os
import requests
import subprocess
import time
import datetime
import threading
from requests.auth import HTTPBasicAuth

# ==========================================
# CONFIGURATION 
# ==========================================
USERNAME = "admin"
PASSWORD = "admin"
BASE_OUTPUT_DIR = "Recording"

# Define the preset lists for each camera
CAM1_PRESETS = [1, 2, 3, 4, 5, 6, 7, 8]  # Left Corner (10.34.0.17)
CAM2_PRESETS = [1, 2, 3, 4, 5, 6]        # Center (10.34.0.16)

# Create output folders
os.makedirs(os.path.join(BASE_OUTPUT_DIR, "Camera_1"), exist_ok=True)
os.makedirs(os.path.join(BASE_OUTPUT_DIR, "Camera_2"), exist_ok=True)

# ==========================================

def call_preset(ip, preset_number):
    """Sends the movement command to a specific camera."""
    url = f"http://{ip}/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{preset_number}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=5)
        if response.status_code != 200:
            print(f"    [-] {ip}: Failed to trigger preset {preset_number}. Status {response.status_code}")
    except Exception as e:
        print(f"    [-] {ip}: Error connecting - {e}")

def record_stream(ip, folder, duration_seconds, preset_number):
    """Captures the RTSP stream for a specific camera."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}:554/stream1"
    filename = f"Preset{preset_number}_{timestamp}.mp4"
    output_filepath = os.path.join(BASE_OUTPUT_DIR, folder, filename)
    
    command = [
        'ffmpeg',
        '-y',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-t', str(duration_seconds),
        '-c', 'copy',
        output_filepath
    ]
    
    try:
        # We use subprocess.run here because the thread itself is running in the background.
        # This will pause the specific camera's thread until its recording is done.
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] {ip} finished Preset {preset_number} -> {filename}")
    except Exception as e:
        print(f"[-] {ip} failed to record Preset {preset_number}: {e}")

# ==========================================
# WORKER THREAD FUNCTIONS
# ==========================================

def run_camera_1():
    """Independent loop for Camera 1 (Left Corner) - 8 Cycles, 32s records."""
    ip = "10.34.0.17"
    for preset in CAM1_PRESETS:
        print(f"[*] Camera 1 moving to Preset {preset}...")
        call_preset(ip, preset)
        time.sleep(5) # Wait for movement/focus
        record_stream(ip, "Camera_1", duration_seconds=32, preset_number=preset)

def run_camera_2():
    """Independent loop for Camera 2 (Center) - 6 Cycles, 45s records."""
    ip = "10.34.0.16"
    for preset in CAM2_PRESETS:
        print(f"[*] Camera 2 moving to Preset {preset}...")
        call_preset(ip, preset)
        time.sleep(5) # Wait for movement/focus
        record_stream(ip, "Camera_2", duration_seconds=45, preset_number=preset)

# ==========================================
# MAIN EXECUTION ROUTINE
# ==========================================
if __name__ == "__main__":
    print("Starting Independent 5-Minute Camera Sweeps...\n")
    
    # Define our two independent threads
    thread_cam1 = threading.Thread(target=run_camera_1)
    thread_cam2 = threading.Thread(target=run_camera_2)
    
    # Start both threads at the exact same time
    thread_cam1.start()
    thread_cam2.start()
    
    # Tell the main script to wait until BOTH threads finish before exiting
    thread_cam1.join()
    thread_cam2.join()
    
    print("\n[+] 5-Minute Automation Complete. All cameras finished their independent sweeps.")