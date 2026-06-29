import os
import requests
import subprocess
import time
import datetime
from requests.auth import HTTPBasicAuth

# ==========================================
# CONFIGURATION 
# ==========================================
USERNAME = "admin"
PASSWORD = "admin"
BASE_OUTPUT_DIR = "Recording"

# Define our two cameras and their specific sub-folders
CAMERAS = [
    {"ip": "10.34.0.16", "folder": "Camera_1"},
    {"ip": "10.34.0.17", "folder": "Camera_2"}
]

# Create the main Recording folder and the sub-folders for each camera
for cam in CAMERAS:
    folder_path = os.path.join(BASE_OUTPUT_DIR, cam["folder"])
    os.makedirs(folder_path, exist_ok=True) 

# ==========================================

def call_preset_for_all(preset_number):
    """Sends a command to ALL cameras to move to a specific preset simultaneously."""
    print(f"\n[*] Moving all cameras to Preset {preset_number}...")
    
    for cam in CAMERAS:
        ip = cam["ip"]
        target_url = f"http://{ip}/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{preset_number}"
        
        try:
            response = requests.get(target_url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=5)
            if response.status_code == 200:
                print(f"    [+] {ip}: Successfully triggered.")
            else:
                print(f"    [-] {ip}: Failed. Status {response.status_code}")
        except Exception as e:
            print(f"    [-] {ip}: Error connecting - {e}")

def record_all_streams(duration_seconds, preset_name):
    """Starts FFmpeg for all cameras simultaneously and waits for them to finish."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"[*] Starting {duration_seconds}-second recording for all cameras...")
    
    active_processes = []
    
    # Loop through each camera and start an FFmpeg process in the background
    for cam in CAMERAS:
        ip = cam["ip"]
        folder = cam["folder"]
        
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}:554/stream1"
        filename = f"Classroom_{preset_name}_{timestamp}.mp4"
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
            # Popen starts the process in the background and continues the loop
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            active_processes.append((process, output_filepath))
            print(f"    [+] Recording started for {ip} -> {output_filepath}")
        except Exception as e:
            print(f"    [-] Failed to start FFmpeg for {ip}: {e}")

    # Now that all recordings are running simultaneously, we tell Python to wait 
    # until they are all completely finished before moving on.
    for process, filepath in active_processes:
        process.wait()
        
    print("[+] All simultaneous recordings have finished saving.")

# ==========================================
# MAIN EXECUTION ROUTINE
# ==========================================
if __name__ == "__main__":
    print("Starting Multi-Camera Automation Script...")
    
    # --- TASK 1: Record Preset 1 ---
    call_preset_for_all(1)
    print("Waiting 5 seconds for cameras to pan and focus...")
    time.sleep(5) 
    record_all_streams(duration_seconds=30, preset_name="Preset1_Whiteboard")
    
    print("\n----------------------------------------")
    
    # --- TASK 2: Record Preset 2 ---
    call_preset_for_all(2)
    print("Waiting 5 seconds for cameras to pan and focus...")
    time.sleep(5)
    record_all_streams(duration_seconds=30, preset_name="Preset2_Desks")
    
    print("\nAutomation complete.")