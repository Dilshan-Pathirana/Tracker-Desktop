import os
import sys
import concurrent.futures
from datetime import datetime
from tracker_wrapper import process_video
from distance_calculator import calculate_summary

BATCH_SIZE = 10  # Same as in GUI

def run_tracking(video_folder, output_folder):
    if not os.path.isdir(video_folder):
        print(f"❌ Input folder not found: {video_folder}")
        sys.exit(1)
    if not os.path.isdir(output_folder):
        print(f"❌ Output folder not found: {output_folder}")
        sys.exit(1)

    video_files = sorted([
        os.path.join(video_folder, f)
        for f in os.listdir(video_folder)
        if f.lower().endswith((".mp4", ".avi", ".mov"))
    ])

    if not video_files:
        print("❌ No video files found in input folder.")
        sys.exit(1)

    print(f"🔍 Found {len(video_files)} videos:")
    for v in video_files:
        print(f"  • {os.path.basename(v)}")

    log_filename = os.path.join(output_folder, f"batch_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

    with open(log_filename, 'w', encoding="utf-8") as logfile:
        total = len(video_files)
        with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            for batch_start in range(0, total, BATCH_SIZE):
                batch = video_files[batch_start:batch_start + BATCH_SIZE]
                batch_names = [os.path.basename(v) for v in batch]

                print(f"\n▶️ Starting batch: {', '.join(batch_names)}")
                logfile.write(f"\n▶️ Starting batch: {', '.join(batch_names)}\n")

                futures = {executor.submit(process_video, video, output_folder): video for video in batch}

                for future in concurrent.futures.as_completed(futures):
                    video = futures[future]
                    video_name = os.path.basename(video)
                    try:
                        result = future.result()
                        msg = f"✅ Completed {video_name}: {result}"
                    except Exception as e:
                        msg = f"❌ Error with {video_name}: {e}"
                    print(msg)
                    logfile.write(msg + "\n")

                print(f"✔️ Finished batch: {', '.join(batch_names)}")
                logfile.write(f"✔️ Finished batch: {', '.join(batch_names)}\n")

    print(f"\n🎯 Tracking complete! Log saved to:\n{log_filename}")
    return log_filename


def run_distance_summary(output_folder):
    print("\n📏 Calculating distance summary...")
    summary_path = calculate_summary(output_folder)
    if summary_path:
        print(f"✅ Distance summary saved to:\n{summary_path}")
    else:
        print("❌ Could not calculate distance summary.")


if __name__ == "__main__":
    # Set these manually or pass via command-line arguments
    if len(sys.argv) >= 3:
        video_dir = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # Hardcode here for testing
        video_dir = r"D:\Thisari\Fish_tracking\videos"
        output_dir = r"D:\Thisari\Fish_tracking\outputs\Run2\data"

    log_file = run_tracking(video_dir, output_dir)

    # Optional: run distance summary
    run_distance_summary(output_dir)
