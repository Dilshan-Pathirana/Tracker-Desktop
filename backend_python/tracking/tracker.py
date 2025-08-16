import cv2
import numpy as np
import time
import os
import csv

class FishTracker:
    def __init__(self, video_path, output_dir, show_window=False):
        self.video_path = video_path
        self.output_dir = output_dir
        self.cap = cv2.VideoCapture(video_path)
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

        self.last_bbox = None
        self.no_movement_frames = 0
        self.max_no_movement_frames = 10

        self.centroid_data = []
        self.positions = []
        self.valid_frame = None
        self.start_time = self.current_time_ms()

        self.show_window = show_window

        os.makedirs(os.path.join(output_dir, 'data'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'heatmaps'), exist_ok=True)

    def current_time_ms(self):
        return int(round(time.time() * 1000))

    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        hours = minutes // 60
        milliseconds = ms % 1000
        return f'{hours:02}:{minutes % 60:02}:{seconds % 60:02}:{milliseconds:03}'

    def log_centroid(self, cx, cy):
        t_ms = self.current_time_ms() - self.start_time
        timestamp = self.format_time(t_ms)
        self.centroid_data.append([timestamp, cx, cy])
        self.positions.append((cx, cy))

        # Print every 30 frames only to reduce flooding
        #if len(self.centroid_data) % 30 == 0:
            #print(f"Time: {timestamp}, Centroid: ({cx}, {cy})")

    def process_frame(self, frame):
        fgmask = self.fgbg.apply(frame)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = False
        for cnt in contours:
            if cv2.contourArea(cnt) < 500:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + h // 2
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.log_centroid(cx, cy)
            self.last_bbox = (x, y, w, h)
            detected = True
            break

        if not detected and self.last_bbox and self.no_movement_frames <= self.max_no_movement_frames:
            x, y, w, h = self.last_bbox
            cx, cy = x + w // 2, y + h // 2
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.log_centroid(cx, cy)
            self.no_movement_frames += 1
        elif detected:
            self.no_movement_frames = 0

        return frame

    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            self.valid_frame = frame
            processed = self.process_frame(frame)

            if self.show_window:
                cv2.imshow("Fish Tracking", processed)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        self.cap.release()
        if self.show_window:
            cv2.destroyAllWindows()

    def save_results(self):
        if self.valid_frame is None:
            print("No valid frame captured.")
            return

        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        csv_path = os.path.join(self.output_dir, 'data', f"{video_name}.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time_hh:mm:ss:ms', 'Centroid_X', 'Centroid_Y'])
            writer.writerows(self.centroid_data)

        heatmap = np.zeros((self.valid_frame.shape[0], self.valid_frame.shape[1]), dtype=np.float32)
        for x, y in self.positions:
            if 0 <= y < heatmap.shape[0] and 0 <= x < heatmap.shape[1]:
                cv2.circle(heatmap, (x, y), radius=3, color=(1,), thickness=-1)

        heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
        heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = np.uint8(heatmap)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        overlay = cv2.addWeighted(self.valid_frame, 0.6, heatmap_colored, 0.4, 0)

        heatmap_path = os.path.join(self.output_dir, 'heatmaps', f"{video_name}.png")
        cv2.imwrite(heatmap_path, overlay)
        print(f"Results saved:\n  CSV: {csv_path}\n  Heatmap: {heatmap_path}")

        if self.show_window:
            cv2.imshow("Fish Heatmap Overlay", overlay)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
