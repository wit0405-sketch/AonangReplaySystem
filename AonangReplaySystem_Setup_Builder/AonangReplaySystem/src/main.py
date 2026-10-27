import sys, os, time, threading, tempfile, subprocess
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QMessageBox,
    QFileDialog, QSlider, QSpinBox
)

APP_NAME = "AONANG LANDMARK REPLAY SYSTEM"
BUFFER_SECONDS = 30

class FrameBus(QObject):
    frame_ready = Signal(object)

class ReplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.setMinimumSize(960, 640)
        self.cap = None
        self.running = False
        self.capture_thread = None
        self.frames = deque()
        self.lock = threading.Lock()
        self.fps = 30.0
        self.frame_size = (1280, 720)
        self.last_frame = None
        self.replay_path = None
        self.bus = FrameBus()
        self.bus.frame_ready.connect(self.update_preview)
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(500)
        self.apply_style()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("AONANG LANDMARK  |  REPLAY SYSTEM")
        title.setObjectName("title")
        header.addWidget(title, 1)
        self.status = QLabel("CAMERA DISCONNECTED")
        self.status.setObjectName("status")
        header.addWidget(self.status)
        main.addLayout(header)

        screens = QGridLayout()
        self.live_view = QLabel("LIVE PREVIEW\n\nConnect your UGREEN capture card")
        self.live_view.setAlignment(Qt.AlignCenter)
        self.live_view.setMinimumHeight(300)
        self.live_view.setObjectName("video")
        self.replay_view = QLabel("REPLAY PREVIEW\n\nSaved replay clips can be opened here")
        self.replay_view.setAlignment(Qt.AlignCenter)
        self.replay_view.setMinimumHeight(300)
        self.replay_view.setObjectName("video")
        screens.addWidget(self._group("LIVE / CAMERA INPUT", self.live_view), 0, 0)
        screens.addWidget(self._group("REPLAY / CLIP PREVIEW", self.replay_view), 0, 1)
        main.addLayout(screens, 1)

        controls = QHBoxLayout()
        self.device = QComboBox()
        for i in range(10):
            self.device.addItem(f"Camera device {i}", i)
        self.device.setCurrentIndex(0)
        self.connect_btn = QPushButton("CONNECT CAMERA")
        self.connect_btn.clicked.connect(self.toggle_camera)
        controls.addWidget(QLabel("Capture device:"))
        controls.addWidget(self.device)
        controls.addWidget(self.connect_btn)
        self.duration = QSpinBox()
        self.duration.setRange(5, 30)
        self.duration.setValue(30)
        self.duration.setSuffix(" sec")
        controls.addWidget(QLabel("Replay length:"))
        controls.addWidget(self.duration)
        main.addLayout(controls)

        actions = QGridLayout()
        self.save_btn = QPushButton("SAVE REPLAY 30s")
        self.save_btn.setObjectName("save")
        self.save_btn.clicked.connect(self.save_replay)
        self.open_btn = QPushButton("OPEN REPLAY FILE")
        self.open_btn.clicked.connect(self.open_replay)
        self.export_btn = QPushButton("SHOW CLIP LOCATION")
        self.export_btn.clicked.connect(self.show_clip_location)
        self.live_btn = QPushButton("RETURN TO LIVE")
        self.live_btn.clicked.connect(self.return_live)
        actions.addWidget(self.save_btn, 0, 0)
        actions.addWidget(self.open_btn, 0, 1)
        actions.addWidget(self.export_btn, 0, 2)
        actions.addWidget(self.live_btn, 0, 3)
        main.addLayout(actions)

        info = QLabel(
            "OBS workflow: Save Replay → OBS Sources (+) → Media Source → select the saved MP4. "
            "Use OBS scene transitions to switch between LIVE and REPLAY."
        )
        info.setWordWrap(True)
        info.setObjectName("info")
        main.addWidget(info)
        self.log = QLabel("Ready. Connect the capture card, then test the preview.")
        self.log.setWordWrap(True)
        main.addWidget(self.log)

    def _group(self, name, child):
        box = QGroupBox(name)
        layout = QVBoxLayout(box)
        layout.addWidget(child)
        return box

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #101923; color: #edf3fa; font-size: 13px; }
            QLabel#title { font-size: 22px; font-weight: bold; color: #f4c15d; padding: 10px; }
            QLabel#status { color: #ffcc66; font-weight: bold; padding: 10px; }
            QLabel#video { background: #05090e; border: 2px solid #32475c; color: #91a7bd; font-size: 16px; }
            QGroupBox { border: 1px solid #32475c; margin-top: 8px; padding-top: 8px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #62b5ff; }
            QPushButton { background: #25394d; border: 1px solid #42627f; padding: 12px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background: #315575; }
            QPushButton#save { background: #a82929; border-color: #e34a4a; }
            QPushButton#save:hover { background: #c23838; }
            QComboBox, QSpinBox { background: #182635; padding: 8px; border: 1px solid #42627f; }
            QLabel#info { background: #182635; padding: 10px; color: #b9d7f0; }
        """)

    def toggle_camera(self):
        if self.running:
            self.stop_camera()
            return
        idx = int(self.device.currentData())
        # CAP_DSHOW is often the most reliable backend for USB capture devices on Windows.
        self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(idx)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Camera not found",
                "Could not open this device. Check USB connection, close OBS or other apps using the card, "
                "and try another device number.")
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.running = True
        self.connect_btn.setText("DISCONNECT CAMERA")
        self.status.setText("CAMERA CONNECTED")
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        self.log.setText(f"Connected to camera device {idx}. Building a rolling {self.duration.value()} second buffer.")

    def stop_camera(self):
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.connect_btn.setText("CONNECT CAMERA")
        self.status.setText("CAMERA DISCONNECTED")
        self.log.setText("Camera disconnected.")

    def capture_loop(self):
        timestamps = deque()
        while self.running and self.cap:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            h, w = frame.shape[:2]
            now = time.time()
            with self.lock:
                self.frames.append((now, frame.copy()))
                cutoff = now - max(30, self.duration.value())
                while self.frames and self.frames[0][0] < cutoff:
                    self.frames.popleft()
            self.last_frame = frame
            self.bus.frame_ready.emit(frame)
            time.sleep(0.001)

    def update_preview(self, frame):
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.live_view.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.live_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.last_frame is not None:
            self.update_preview(self.last_frame)

    def save_replay(self):
        with self.lock:
            items = list(self.frames)
        if not items:
            QMessageBox.information(self, "No footage yet", "Connect the camera and wait for footage before saving a replay.")
            return
        seconds = self.duration.value()
        cutoff = time.time() - seconds
        selected = [f for t, f in items if t >= cutoff]
        if len(selected) < 2:
            QMessageBox.information(self, "Buffer filling", "The replay buffer is still filling. Wait a few seconds and try again.")
            return
        out_dir = Path.home() / "Videos" / "AonangReplays"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / time.strftime("Replay_%Y%m%d_%H%M%S.mp4")
        h, w = selected[0].shape[:2]
        # Derive a stable playback FPS from actual frame count/time span.
        span = max(1.0, items[-1][0] - max(cutoff, items[0][0]))
        fps = max(10.0, min(60.0, len(selected) / span))
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        if not writer.isOpened():
            QMessageBox.critical(self, "Save failed", "Could not create MP4. Check disk space and OpenCV video codec support.")
            return
        for frame in selected:
            writer.write(frame)
        writer.release()
        self.replay_path = str(path)
        self.play_file_in_preview(self.replay_path)
        self.log.setText(f"Saved {len(selected)} frames to: {path}")

    def play_file_in_preview(self, path):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.replay_view.setText(f"Replay saved:\n{path}\n\nOpen the file in OBS Media Source.")
            return
        ok, frame = cap.read()
        cap.release()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.replay_view.setPixmap(QPixmap.fromImage(qimg).scaled(
                self.replay_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.replay_view.setToolTip(path)

    def open_replay(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Replay Video", str(Path.home() / "Videos"), "Video files (*.mp4 *.mov *.avi *.mkv)")
        if path:
            self.replay_path = path
            self.play_file_in_preview(path)
            self.log.setText(f"Selected replay file: {path}")

    def show_clip_location(self):
        if not self.replay_path or not os.path.exists(self.replay_path):
            QMessageBox.information(self, "No replay selected", "Save or open a replay file first.")
            return
        try:
            os.startfile(str(Path(self.replay_path).parent))
        except Exception:
            QMessageBox.information(self, "Replay location", self.replay_path)

    def return_live(self):
        if self.last_frame is not None:
            self.update_preview(self.last_frame)
        self.log.setText("Live preview selected. In OBS, switch back to your LIVE scene/source.")

    def refresh_status(self):
        if self.running:
            with self.lock:
                n = len(self.frames)
                span = self.frames[-1][0] - self.frames[0][0] if n > 1 else 0
            self.status.setText(f"CAMERA CONNECTED  |  BUFFER {min(self.duration.value(), int(span))}/{self.duration.value()}s")
        else:
            self.status.setText("CAMERA DISCONNECTED")

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

def main():
    app = QApplication(sys.argv)
    win = ReplayWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
