import os
import requests
import subprocess
import time
import datetime
from requests.auth import HTTPBasicAuth

# ==========================================
# CONFIGURATION 
# ==========================================
CAMERA_IP = "10.34.0.16"
USERNAME = "your_username"
PASSWORD = "your_password"

# The EXACT PTZ control URL we found in your network logs!
PTZ_API_URL = f"http://{CAMERA_IP}/cgi-bin/ptzctrl.cgi"
RTSP_URL = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/stream1"

OUTPUT_DIR = "Recording" 
os.makedirs(OUTPUT_DIR, exist_ok=True) 
# ==========================================

def call_preset(preset_number):
    """Sends a command to the camera to move to a specific preset."""
    print(f"[*] Moving camera to Preset {preset_number}...")
    
    # Constructing the exact URL format your camera expects
    target_url = f"{PTZ_API_URL}?ptzcmd&poscall&{preset_number}"
    
    try:
        response = requests.get(target_url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=5)
        if response.status_code == 200:
            print(f"[+] Successfully triggered Preset {preset_number}.")
        else:
            print(f"[-] Failed to trigger preset. Camera returned status: {response.status_code}")
    except Exception as e:
        print(f"[-] Error connecting to camera PTZ control: {e}")

def record_stream(duration_seconds, preset_name):
    """Captures the RTSP stream and saves it to an MP4 file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Classroom_{preset_name}_{timestamp}.mp4"
    output_filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"[*] Starting recording for {duration_seconds} seconds. Saving to {output_filepath}...")
    
    command = [
        'ffmpeg',
        '-y',                        
        '-rtsp_transport', 'tcp',    
        '-i', RTSP_URL,              
        '-t', str(duration_seconds), 
        '-c', 'copy',                
        output_filepath              
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] Recording saved successfully: {output_filepath}")
    except subprocess.CalledProcessError:
        print("[-] FFmpeg failed to record the stream. Check your RTSP URL.")

# ==========================================
# MAIN EXECUTION ROUTINE
# ==========================================
if __name__ == "__main__":
    print("Starting Camera Automation Script...\n")
    
    call_preset(1)
    print("Waiting 5 seconds for camera to pan and focus...")
    time.sleep(5) 
    record_stream(duration_seconds=30, preset_name="Preset1_Whiteboard")
    
    print("\n----------------------------------------\n")
    
    call_preset(2)
    print("Waiting 5 seconds for camera to pan and focus...")
    time.sleep(5)
    record_stream(duration_seconds=30, preset_name="Preset2_Desks")
    
    print("\nAutomation complete.")