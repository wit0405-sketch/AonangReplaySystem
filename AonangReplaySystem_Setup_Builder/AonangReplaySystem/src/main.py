import sys, os, time, threading, subprocess, shutil
from collections import deque
from pathlib import Path

import cv2
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QMessageBox,
    QFileDialog, QSpinBox, QInputDialog
)
import obsws_python as obsws

APP_NAME = "AONANG LANDMARK REPLAY SYSTEM"
APP_VERSION = "0.2.0"

class FrameBus(QObject):
    frame_ready = Signal(object)

class ReplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 800)
        self.setMinimumSize(960, 640)
        self.cap = None
        self.running = False
        self.capture_thread = None
        self.frames = deque()
        self.lock = threading.Lock()
        self.last_frame = None
        self.replay_path = None
        self.obs_client = None
        self.obs_host = "127.0.0.1"
        self.obs_port = 4455
        self.obs_password = ""
        self.obs_live_scene = "LIVE"
        self.obs_replay_scene = "REPLAY"
        self.obs_media_source = "Aonang Replay"
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
        self.save_btn = QPushButton("SAVE REPLAY")
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

        obs_box = QGroupBox("OBS STUDIO CONTROL")
        obs_layout = QVBoxLayout(obs_box)
        obs_buttons = QGridLayout()
        self.obs_connect_btn = QPushButton("Connect OBS")
        self.obs_connect_btn.clicked.connect(self.connect_obs)
        self.obs_play_btn = QPushButton("PLAY REPLAY")
        self.obs_play_btn.clicked.connect(self.play_replay_obs)
        self.obs_stop_btn = QPushButton("STOP REPLAY")
        self.obs_stop_btn.clicked.connect(self.stop_replay_obs)
        self.obs_live_btn = QPushButton("BACK TO LIVE")
        self.obs_live_btn.clicked.connect(self.back_to_live_obs)
        obs_buttons.addWidget(self.obs_connect_btn, 0, 0)
        obs_buttons.addWidget(self.obs_play_btn, 0, 1)
        obs_buttons.addWidget(self.obs_stop_btn, 0, 2)
        obs_buttons.addWidget(self.obs_live_btn, 0, 3)
        obs_layout.addLayout(obs_buttons)
        self.obs_status = QLabel("Connection Status: DISCONNECTED")
        self.obs_status.setObjectName("obsStatus")
        obs_layout.addWidget(self.obs_status)
        main.addWidget(obs_box)

        info = QLabel(
            "OBS Studio 28+: enable Tools > WebSocket Server Settings (default port 4455). "
            "Create scenes named LIVE and REPLAY. The application updates/creates the "
            "Media Source 'Aonang Replay' in the REPLAY scene when a clip is played."
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
            QLabel#obsStatus { background: #182635; padding: 8px; color: #ffcc66; font-weight: bold; }
        """)

    def toggle_camera(self):
        if self.running:
            self.stop_camera()
            return
        idx = int(self.device.currentData())
        self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(idx)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            QMessageBox.warning(self, "Camera not found",
                "Could not open this device. Check USB connection and close other applications using the capture card.")
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.running = True
        self.connect_btn.setText("DISCONNECT CAMERA")
        self.status.setText("CAMERA CONNECTED")
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        self.log.setText(f"Connected to camera device {idx}. Rolling buffer: {self.duration.value()} seconds.")

    def stop_camera(self):
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=3)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.connect_btn.setText("CONNECT CAMERA")
        self.status.setText("CAMERA DISCONNECTED")

    def capture_loop(self):
        while self.running:
            cap = self.cap
            if cap is None:
                break
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            now = time.time()
            with self.lock:
                self.frames.append((now, frame.copy()))
                cutoff = now - self.duration.value()
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

    def _ffmpeg_path(self):
        candidates = []
        bundled = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        candidates.extend([bundled / "ffmpeg.exe", Path(sys.executable).parent / "ffmpeg.exe"])
        from_path = shutil.which("ffmpeg")
        if from_path:
            candidates.append(Path(from_path))
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None

    def save_replay(self):
        with self.lock:
            items = list(self.frames)
        if not items:
            QMessageBox.information(self, "No footage yet", "Connect the camera and wait for footage before saving a replay.")
            return
        seconds = self.duration.value()
        cutoff = time.time() - seconds
        selected = [(t, frame) for t, frame in items if t >= cutoff]
        if len(selected) < 2:
            QMessageBox.information(self, "Buffer filling", "The replay buffer is still filling. Wait a few seconds and try again.")
            return
        out_dir = Path.home() / "Videos" / "AonangReplays"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / time.strftime("Replay_%Y%m%d_%H%M%S.mp4")
        span = max(0.1, selected[-1][0] - selected[0][0])
        fps = max(10.0, min(60.0, (len(selected) - 1) / span))
        ffmpeg = self._ffmpeg_path()
        if ffmpeg:
            height, width = selected[0][1].shape[:2]
            command = [
                ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo",
                "-pix_fmt", "bgr24", "-video_size", f"{width}x{height}",
                "-framerate", f"{fps:.3f}", "-i", "-", "-an",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                str(path)
            ]
            try:
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.PIPE)
                for _, frame in selected:
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
                stderr = process.stderr.read().decode("utf-8", errors="replace")
                code = process.wait()
                if code != 0:
                    raise RuntimeError(stderr or f"FFmpeg exited with code {code}")
            except Exception as exc:
                try:
                    process.kill()
                except Exception:
                    pass
                QMessageBox.critical(self, "Save failed", f"FFmpeg could not create MP4:\n{exc}")
                return
        else:
            height, width = selected[0][1].shape[:2]
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            if not writer.isOpened():
                QMessageBox.critical(self, "Save failed", "FFmpeg and OpenCV MP4 encoders are unavailable.")
                return
            try:
                for _, frame in selected:
                    writer.write(frame)
            finally:
                writer.release()
        if not path.is_file() or path.stat().st_size == 0:
            QMessageBox.critical(self, "Save failed", "The output MP4 file is empty or was not created.")
            return
        self.replay_path = str(path)
        self.play_file_in_preview(self.replay_path)
        self.log.setText(f"Saved {len(selected)} frames ({seconds}s target) to: {path}")

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
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Replay Video", str(Path.home() / "Videos"),
            "Video files (*.mp4 *.mov *.avi *.mkv)"
        )
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
        self.log.setText("Live preview selected. Use BACK TO LIVE to switch the OBS program scene.")

    def connect_obs(self):
        host, ok = QInputDialog.getText(self, "Connect OBS", "OBS WebSocket host:", text=self.obs_host)
        if not ok:
            return
        port, ok = QInputDialog.getInt(self, "Connect OBS", "WebSocket port:", self.obs_port, 1, 65535)
        if not ok:
            return
        password, ok = QInputDialog.getText(
            self, "Connect OBS", "WebSocket password (leave blank if none):", text=self.obs_password
        )
        if not ok:
            return
        try:
            client = obsws.ReqClient(host=host.strip(), port=port, password=password, timeout=3)
            client.get_version()
            response = client.get_scene_list()
            scene_names = [s.get("sceneName") for s in getattr(response, "scenes", [])]
            missing = [name for name in (self.obs_live_scene, self.obs_replay_scene) if name not in scene_names]
            if missing:
                raise RuntimeError("OBS scenes not found: " + ", ".join(missing))
            self.obs_client = client
            self.obs_host, self.obs_port, self.obs_password = host.strip(), port, password
            self.obs_status.setText(f"Connection Status: CONNECTED ({self.obs_host}:{self.obs_port})")
            self.obs_connect_btn.setText("Reconnect OBS")
            self.log.setText("OBS connected. LIVE and REPLAY scenes are ready.")
        except Exception as exc:
            self.obs_client = None
            self.obs_status.setText("Connection Status: DISCONNECTED")
            QMessageBox.warning(self, "OBS connection failed",
                "Could not connect to OBS. Check that OBS is open and its WebSocket server is enabled.\n\n" + str(exc))

    def _require_obs(self):
        if self.obs_client is None:
            QMessageBox.information(self, "OBS not connected", "Press Connect OBS and complete the connection first.")
            return False
        return True

    def _ensure_replay_media_source(self):
        inputs = self.obs_client.get_input_list()
        input_names = [item.get("inputName") for item in getattr(inputs, "inputs", [])]
        settings = {"local_file": self.replay_path, "is_local_file": True, "looping": False}
        if self.obs_media_source not in input_names:
            self.obs_client.create_input(
                self.obs_replay_scene, self.obs_media_source, "ffmpeg_source", settings, True
            )
            return
        self.obs_client.set_input_settings(self.obs_media_source, settings, overlay=True)
        scene_items_response = self.obs_client.get_scene_item_list(self.obs_replay_scene)
        scene_items = getattr(scene_items_response, "scene_items", [])
        if not any(item.get("sourceName") == self.obs_media_source for item in scene_items):
            self.obs_client.create_scene_item(self.obs_replay_scene, self.obs_media_source, True)

    def play_replay_obs(self):
        if not self._require_obs():
            return
        if not self.replay_path or not os.path.isfile(self.replay_path):
            QMessageBox.information(self, "No replay selected", "Save a replay or open a replay video file first.")
            return
        try:
            self._ensure_replay_media_source()
            self.obs_client.set_current_program_scene(self.obs_replay_scene)
            self.obs_client.trigger_media_input_action(
                self.obs_media_source, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            )
            self.obs_status.setText("Connection Status: CONNECTED | REPLAY PLAYING")
            self.log.setText(f"Playing replay in OBS: {self.replay_path}")
        except Exception as exc:
            QMessageBox.warning(self, "OBS replay failed", str(exc))

    def stop_replay_obs(self):
        if not self._require_obs():
            return
        try:
            self.obs_client.trigger_media_input_action(
                self.obs_media_source, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP"
            )
            self.obs_status.setText("Connection Status: CONNECTED | REPLAY STOPPED")
            self.log.setText("OBS replay stopped.")
        except Exception as exc:
            QMessageBox.warning(self, "OBS stop failed", str(exc))

    def back_to_live_obs(self):
        if not self._require_obs():
            return
        try:
            self.obs_client.set_current_program_scene(self.obs_live_scene)
            self.obs_status.setText("Connection Status: CONNECTED | LIVE")
            self.log.setText("Switched OBS program scene to LIVE.")
        except Exception as exc:
            QMessageBox.warning(self, "OBS scene switch failed", str(exc))

    def refresh_status(self):
        if self.running:
            with self.lock:
                span = self.frames[-1][0] - self.frames[0][0] if len(self.frames) > 1 else 0
            self.status.setText(
                f"CAMERA CONNECTED | BUFFER {min(self.duration.value(), int(span))}/{self.duration.value()}s"
            )
        else:
            self.status.setText("CAMERA DISCONNECTED")

    def closeEvent(self, event):
        self.stop_camera()
        self.obs_client = None
        event.accept()

def main():
    app = QApplication(sys.argv)
    win = ReplayWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
