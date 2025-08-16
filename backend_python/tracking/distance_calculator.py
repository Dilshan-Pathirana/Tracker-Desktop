import os
import csv
import math
import cv2
from typing import Optional

def calculate_total_distance(
    csv_path: str,
    video_path: str,
    real_width_cm: float = 28,
    real_height_cm: float = 14,
    frame_skip: int = 60
) -> Optional[float]:
    """
    Calculate total distance traveled (in cm) based on centroid points from CSV and video resolution.

    Args:
        csv_path: Path to CSV file containing Centroid_X and Centroid_Y columns.
        video_path: Path to the corresponding video file.
        real_width_cm: Real-world width of the tank/view in cm.
        real_height_cm: Real-world height of the tank/view in cm.
        frame_skip: Skip every n frames for distance calculation (default 60).

    Returns:
        Total distance traveled in cm or None on failure.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Warning: Could not open video {video_path}. Skipping.")
        return None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    points = []
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                if idx % frame_skip != 0:
                    continue
                try:
                    x = int(row['Centroid_X'])
                    y = int(row['Centroid_Y'])
                except (KeyError, ValueError):
                    print(f"Skipping invalid row in {csv_path}: {row}")
                    continue
                points.append((x, y))
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}")
        return None

    if len(points) < 2:
        print(f"Not enough points in {csv_path} to calculate distance.")
        return 0

    total_pixel_distance = sum(
        math.sqrt((points[i][0] - points[i-1][0]) ** 2 + (points[i][1] - points[i-1][1]) ** 2)
        for i in range(1, len(points))
    )

    pixel_to_cm_x = real_width_cm / frame_width
    pixel_to_cm_y = real_height_cm / frame_height
    pixel_to_cm = (pixel_to_cm_x + pixel_to_cm_y) / 2

    return total_pixel_distance * pixel_to_cm


def calculate_summary(output_root: str, videos_dir: Optional[str] = None) -> Optional[str]:
    """
    Calculate distance summaries for all CSVs in output_root/data
    and save a summary CSV in output_root.

    Args:
        output_root: Folder where `data` folder with CSVs is located and summary CSV will be saved.
        videos_dir: Optional folder where original videos are stored. Defaults to sibling "videos" folder.

    Returns:
        Path to summary CSV or None on failure.
    """
    data_dir = os.path.join(output_root, 'data')
    if videos_dir is None:
        videos_dir = os.path.join(os.path.dirname(output_root), 'videos')

    summary_csv = os.path.join(output_root, 'distance_summary.csv')

    if not os.path.exists(data_dir) or not os.path.exists(videos_dir):
        print("❌ Required directories not found.")
        return None

    csv_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]
    if not csv_files:
        print("❌ No CSV files found in data directory.")
        return None

    results = []
    for csv_file in csv_files:
        name = os.path.splitext(csv_file)[0]
        video_path = os.path.join(videos_dir, name + ".mp4")
        csv_path = os.path.join(data_dir, csv_file)

        if not os.path.exists(video_path):
            print(f"⚠️ Missing video for: {csv_file}")
            continue

        distance = calculate_total_distance(csv_path, video_path)
        if distance is not None:
            results.append([name, f"{distance:.2f}"])
        else:
            results.append([name, "Error"])

    os.makedirs(output_root, exist_ok=True)
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Video', 'Total Distance (cm)'])
        writer.writerows(results)

    print(f"\n✅ Distance summary saved to: {summary_csv}")
    return summary_csv
