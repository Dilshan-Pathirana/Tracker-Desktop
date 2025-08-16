import os
import sys
from utils.tracker import FishTracker

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller and normal run """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def process_video(video_path, output_dir):
    try:
        # Convert to absolute resource-safe paths
        video_path = get_resource_path(video_path)
        output_dir = get_resource_path(output_dir)

        tracker = FishTracker(video_path, output_dir, show_window=False)
        tracker.run()
        tracker.save_results()
        return f"✅ Success: {os.path.basename(video_path)}"
    except Exception as e:
        return f"❌ Failed: {os.path.basename(video_path)} with error: {e}"
