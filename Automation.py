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

CAM1_PRESETS = [1, 2, 3, 4, 5, 6, 7, 8]  # Left Corner (10.34.0.17)
CAM2_PRESETS = [1, 2, 3, 4, 5, 6]        # Center (10.34.0.16)

os.makedirs(os.path.join(BASE_OUTPUT_DIR, "Camera_1"), exist_ok=True)
os.makedirs(os.path.join(BASE_OUTPUT_DIR, "Camera_2"), exist_ok=True)

# ==========================================
# CAMERA CONTROLS
# ==========================================

def call_preset(ip, preset_number):
    url = f"http://{ip}/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{preset_number}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=5)
        if response.status_code != 200:
            print(f"    [-] {ip}: Failed to trigger preset {preset_number}. Status {response.status_code}")
    except Exception as e:
        print(f"    [-] {ip}: Error connecting - {e}")

def record_stream(ip, folder, duration_seconds, preset_number):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}:554/stream1"
    
    # Adding a leading zero to single digits (e.g., Preset01 instead of Preset1) 
    # ensures they sort in perfect alphabetical/chronological order later.
    filename = f"Preset{preset_number:02d}_{timestamp}.mp4"
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
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] {ip} finished Preset {preset_number} -> {filename}")
    except Exception as e:
        print(f"[-] {ip} failed to record Preset {preset_number}: {e}")

# ==========================================
# THREADS
# ==========================================

def run_camera_1():
    ip = "10.34.0.17"
    for preset in CAM1_PRESETS:
        print(f"[*] Camera 1 moving to Preset {preset}...")
        call_preset(ip, preset)
        time.sleep(5) 
        record_stream(ip, "Camera_1", duration_seconds=32, preset_number=preset)

def run_camera_2():
    ip = "10.34.0.16"
    for preset in CAM2_PRESETS:
        print(f"[*] Camera 2 moving to Preset {preset}...")
        call_preset(ip, preset)
        time.sleep(5) 
        record_stream(ip, "Camera_2", duration_seconds=45, preset_number=preset)

# ==========================================
# VIDEO MERGER
# ==========================================

def merge_videos(folder_name, output_filename):
    """Stitches all MP4 files in a specific folder into one continuous video."""
    print(f"\n[*] Merging clips for {folder_name}...")
    folder_path = os.path.join(BASE_OUTPUT_DIR, folder_name)
    
    # Get all MP4 files and sort them (the timestamp in the name naturally orders them)
    video_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
    
    if not video_files:
        print(f"[-] No videos found in {folder_name} to merge.")
        return

    # FFmpeg concat requires a text file listing the videos in order
    list_file_path = os.path.join(folder_path, "concat_list.txt")
    with open(list_file_path, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")
            
    final_video_path = os.path.join(BASE_OUTPUT_DIR, output_filename)
    
    # FFmpeg concat command
    command = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file_path,
        '-c', 'copy',          # Copy codec (lightning fast, no quality loss)
        final_video_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] Successfully merged! Final video saved as: {final_video_path}")
    except Exception as e:
        print(f"[-] Failed to merge videos for {folder_name}: {e}")
    finally:
        # Clean up the temporary text file
        if os.path.exists(list_file_path):
            os.remove(list_file_path)

# ==========================================
# MAIN EXECUTION ROUTINE
# ==========================================
if __name__ == "__main__":
    print("Starting Independent 5-Minute Camera Sweeps...\n")
    
    thread_cam1 = threading.Thread(target=run_camera_1)
    thread_cam2 = threading.Thread(target=run_camera_2)
    
    thread_cam1.start()
    thread_cam2.start()
    
    # Wait for the sweeps to completely finish
    thread_cam1.join()
    thread_cam2.join()
    
    print("\n[+] Sweeps complete. Beginning video merge process...")
    
    # Generate timestamp for the master files
    master_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    # Merge Camera 1 videos
    merge_videos("Camera_1", f"Camera_1_MasterSweep_{master_timestamp}.mp4")
    
    # Merge Camera 2 videos
    merge_videos("Camera_2", f"Camera_2_MasterSweep_{master_timestamp}.mp4")
    
    print("\n[+] All automation and merging completely finished.")