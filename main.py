import sys
import os
import json
import vlc
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFrame, QFileDialog, QSlider, QLabel, QListWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent

# مسار ملف التخزين المؤقت لقائمة التشغيل
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist_cache.json")

class ShbeebPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("شبيب - Shbeeb Media Player")
        self.setGeometry(100, 100, 1050, 700)

        # بيانات قائمة التشغيل
        self.playlist = []
        self.current_index = -1

        # الواجهة الأساسية
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # القسم الأيمن: الفيديو وأشرطة التحكم
        left_layout = QVBoxLayout()

        # إطار عرض الفيديو الخاص بـ VLC
        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        left_layout.addWidget(self.video_frame)

        # شريط التقدم (Timeline Slider)
        self.time_slider = QSlider(Qt.Horizontal, self)
        self.time_slider.setRange(0, 1000)
        self.time_slider.sliderMoved.connect(self.set_position)
        left_layout.addWidget(self.time_slider)

        # لوحة أزرار التحكم والتحكم بالصوت
        controls_layout = QHBoxLayout()

        self.btn_open = QPushButton("إضافة ملفات", self)
        self.btn_open.clicked.connect(self.add_files)
        controls_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton("تشغيل", self)
        self.btn_play.clicked.connect(self.play_video)
        controls_layout.addWidget(self.btn_play)

        self.btn_pause = QPushButton("إيقاف مؤقت", self)
        self.btn_pause.clicked.connect(self.pause_video)
        controls_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("إيقاف تام", self)
        self.btn_stop.clicked.connect(self.stop_video)
        controls_layout.addWidget(self.btn_stop)

        self.btn_fullscreen = QPushButton("ملء الشاشة", self)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        controls_layout.addWidget(self.btn_fullscreen)

        # شريط ومستوى الصوت
        self.volume_label = QLabel("الصوت:", self)
        controls_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(90)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.volume_slider)

        left_layout.addLayout(controls_layout)
        main_layout.addLayout(left_layout, stretch=3)

        # القسم الأيسر: حاوية قائمة التشغيل (Playlist Container)
        self.right_container = QWidget(self)
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.playlist_label = QLabel("قائمة التشغيل - شبيب", self)
        right_layout.addWidget(self.playlist_label)

        self.playlist_widget = QListWidget(self)
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: 14px;
                border: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
        """)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_item)
        right_layout.addWidget(self.playlist_widget)

        main_layout.addWidget(self.right_container, stretch=1)

        # إعداد مشغل VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # مؤقت لتحديث شريط التقدم دورياً
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        # استعادة القائمة المخزنة تلقائياً عند الإقلاع
        self.load_playlist_cache()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "اختر ملفات فيديو", "", "Video Files (*.mp4 *.avi *.mkv *.mov)")
        if files:
            for file in files:
                if file not in self.playlist:
                    self.playlist.append(file)
                    self.playlist_widget.addItem(os.path.basename(file))
            self.save_playlist_cache()
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.play_current()

    def play_current(self):
        if 0 <= self.current_index < len(self.playlist):
            file_path = self.playlist[self.current_index]
            if not os.path.exists(file_path):
                return
            if sys.platform == "win32":
                self.player.set_hwnd(int(self.video_frame.winId()))
            
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            self.player.play()
            self.player.audio_set_volume(self.volume_slider.value())
            self.playlist_widget.setCurrentRow(self.current_index)

    def play_selected_item(self, item):
        row = self.playlist_widget.row(item)
        self.current_index = row
        self.play_current()

    def play_video(self):
        if self.player.get_media():
            self.player.play()
        elif self.playlist:
            self.current_index = 0
            self.play_current()

    def pause_video(self):
        self.player.pause()

    def stop_video(self):
        self.player.stop()
        self.time_slider.setValue(0)

    def set_position(self, position):
        length = self.player.get_length()
        if length > 0:
            target_time = int((position / 1000.0) * length)
            self.player.set_time(target_time)

    def set_volume(self, volume):
        self.player.audio_set_volume(volume)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.right_container.show()
        else:
            self.showFullScreen()
            self.right_container.hide()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        # Space: التشغيل والإيقاف المؤقت
        if key == Qt.Key_Space:
            if self.player.is_playing():
                self.player.pause()
            else:
                self.player.play()
            event.accept()
        
        # F: تفعيل أو إلغاء ملء الشاشة
        elif key == Qt.Key_F:
            self.toggle_fullscreen()
            event.accept()
        
        # Esc: الخروج من ملء الشاشة
        elif key == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            self.right_container.show()
            event.accept()
        
        # السهم الأيمن: تقديم 5 ثوانٍ
        elif key == Qt.Key_Right:
            current = self.player.get_time()
            self.player.set_time(current + 5000)
            event.accept()
            
        # السهم الأيسر: ترجيع 5 ثوانٍ
        elif key == Qt.Key_Left:
            current = self.player.get_time()
            self.player.set_time(max(0, current - 5000))
            event.accept()
            
        # السهم الأعلى: زيادة الصوت بنسبة 5%
        elif key == Qt.Key_Up:
            new_vol = min(100, self.volume_slider.value() + 5)
            self.volume_slider.setValue(new_vol)
            event.accept()
            
        # السهم الأسفل: خفض الصوت بنسبة 5%
        elif key == Qt.Key_Down:
            new_vol = max(0, self.volume_slider.value() - 5)
            self.volume_slider.setValue(new_vol)
            event.accept()
            
        else:
            super().keyPressEvent(event)

    def save_playlist_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.playlist, f, ensure_ascii=False)
        except Exception:
            pass

    def load_playlist_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    files = json.load(f)
                    for file in files:
                        if os.path.exists(file):
                            self.playlist.append(file)
                            self.playlist_widget.addItem(os.path.basename(file))
            except Exception:
                pass

    def update_ui(self):
        if self.player.is_playing():
            length = self.player.get_length()
            if length > 0:
                current_time = self.player.get_time()
                progress = int((current_time / length) * 1000)
                self.time_slider.setValue(progress)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = ShbeebPlayer()
    player.show()
    sys.exit(app.exec_())