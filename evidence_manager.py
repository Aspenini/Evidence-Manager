#!/usr/bin/env python3
"""
Evidence Manager - PyQt6 (Refactored)
Fast, robust evidence manager for people with images, audio, videos and info.
Key improvements:
- Non-blocking import/export and file copy operations
- Safer, atomic JSON writes and resilient IO
- Thumbnail generation and caching for images
- Deduplicated logic for media types; fewer code paths, fewer bugs
- Better error handling; defensive checks throughout
"""

from __future__ import annotations

import sys
import os
import json
import shutil
import zipfile
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QTabWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
    QSplitter,
    QHeaderView,
    QAbstractItemView,
    QProgressDialog,
)
from PyQt6.QtCore import Qt, QThreadPool, QRunnable, QObject, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PIL import Image


# ---------------------------
# Data models and persistence
# ---------------------------

MEDIA_IMAGES = "images"
MEDIA_AUDIO = "audio"
MEDIA_VIDEOS = "videos"


@dataclass
class MediaEntry:
    display_name: str
    filename: str


@dataclass
class PersonRecord:
    name: str
    created: str
    info: Dict[str, List[str]]
    images: List[MediaEntry]
    audio: List[MediaEntry]
    videos: List[MediaEntry]

    @staticmethod
    def new(name: str) -> "PersonRecord":
        return PersonRecord(
            name=name,
            created=datetime.now().isoformat(),
            info={},
            images=[],
            audio=[],
            videos=[],
        )

    @staticmethod
    def from_dict(data: dict) -> "PersonRecord":
        def _deserialize_list(items):
            result: List[MediaEntry] = []
            for it in items:
                if isinstance(it, dict):
                    result.append(MediaEntry(it.get("display_name", ""), it.get("filename", "")))
                elif isinstance(it, str):
                    result.append(MediaEntry(Path(it).stem, it))
            return result

        return PersonRecord(
            name=data.get("name", ""),
            created=data.get("created", datetime.now().isoformat()),
            info=data.get("info", {}),
            images=_deserialize_list(data.get("images", [])),
            audio=_deserialize_list(data.get("audio", [])),
            videos=_deserialize_list(data.get("videos", [])),
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        # Convert MediaEntry dataclasses to dict
        data["images"] = [asdict(m) for m in self.images]
        data["audio"] = [asdict(m) for m in self.audio]
        data["videos"] = [asdict(m) for m in self.videos]
        return data


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def person_dir(self, person_name: str) -> Path:
        return self.root / person_name.replace(" ", "_")

    def ensure_person_dirs(self, person_name: str) -> None:
        pdir = self.person_dir(person_name)
        (pdir / MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)
        (pdir / MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
        (pdir / MEDIA_VIDEOS).mkdir(parents=True, exist_ok=True)
        (pdir / MEDIA_IMAGES / "_thumbnails").mkdir(parents=True, exist_ok=True)

    def data_path(self, person_name: str) -> Path:
        return self.person_dir(person_name) / "person_data.json"

    def load_all(self) -> Dict[str, PersonRecord]:
        people: Dict[str, PersonRecord] = {}
        if not self.root.exists():
            return people
        for entry in sorted(self.root.iterdir()):
            if entry.is_dir():
                person_name = entry.name.replace("_", " ")
                data_file = entry / "person_data.json"
                if data_file.exists():
                    try:
                        with data_file.open("r", encoding="utf-8") as f:
                            raw = json.load(f)
                        people[person_name] = PersonRecord.from_dict(raw)
                    except Exception:
                        people[person_name] = PersonRecord.new(person_name)
                else:
                    people[person_name] = PersonRecord.new(person_name)
        return people

    def save_person(self, person: PersonRecord) -> None:
        self.ensure_person_dirs(person.name)
        path = self.data_path(person.name)
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="person_", suffix=".json", dir=str(path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(person.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def unique_destination(self, directory: Path, filename: str) -> Path:
        dest = directory / filename
        if not dest.exists():
            return dest
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        idx = 1
        while True:
            candidate = directory / f"{stem}_{idx}{suffix}"
            if not candidate.exists():
                return candidate
            idx += 1

    def add_media_file(self, person: PersonRecord, kind: str, src_path: Path) -> MediaEntry:
        self.ensure_person_dirs(person.name)
        subdir = {
            MEDIA_IMAGES: MEDIA_IMAGES,
            MEDIA_AUDIO: MEDIA_AUDIO,
            MEDIA_VIDEOS: MEDIA_VIDEOS,
        }[kind]
        target_dir = self.person_dir(person.name) / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = self.unique_destination(target_dir, src_path.name)
        shutil.copy2(src_path, dest)
        entry = MediaEntry(display_name=dest.stem, filename=dest.name)
        getattr(person, kind).append(entry)
        self.save_person(person)
        return entry

    def delete_media_file(self, person: PersonRecord, kind: str, filename: str) -> None:
        subdir = self.person_dir(person.name) / kind
        file_path = subdir / filename
        # Remove from model
        items: List[MediaEntry] = getattr(person, kind)
        items[:] = [m for m in items if m.filename != filename]
        # Delete file and thumbnail if any
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        if kind == MEDIA_IMAGES:
            thumb = subdir / "_thumbnails" / filename
            if thumb.exists():
                try:
                    thumb.unlink()
                except Exception:
                    pass
        self.save_person(person)

    def rename_media_display(self, person: PersonRecord, kind: str, filename: str, new_display: str) -> None:
        items: List[MediaEntry] = getattr(person, kind)
        for m in items:
            if m.filename == filename:
                m.display_name = new_display.strip()
                break
        self.save_person(person)

    def open_path(self, path: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform.startswith("darwin"):
                import subprocess
                subprocess.Popen(["open", str(path)])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass

    def image_thumbnail(self, person: PersonRecord, filename: str, size: Tuple[int, int] = (64, 64)) -> Optional[Path]:
        img_dir = self.person_dir(person.name) / MEDIA_IMAGES
        src = img_dir / filename
        if not src.exists():
            return None
        thumb_dir = img_dir / "_thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / filename
        try:
            if not thumb_path.exists() or thumb_path.stat().st_mtime < src.stat().st_mtime:
                with Image.open(src) as im:
                    im.thumbnail(size)
                    im.save(thumb_path)
            return thumb_path
        except Exception:
            return None


# ---------------------------
# Background worker utilities
# ---------------------------

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)


class CallableWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))


# ---------------------------
# Main Window and UI logic
# ---------------------------

class EvidenceManagerPyQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evidence Manager - PyQt6")
        self.setGeometry(100, 100, 1200, 800)

        self.settings_file = Path("settings.json")
        self.dark_mode = False
        self.load_settings()

        self.store = EvidenceStore(Path("Evidence"))
        self.people: Dict[str, PersonRecord] = self.store.load_all()
        self.current_person_name: Optional[str] = None

        self.thread_pool = QThreadPool.globalInstance()

        self._people_filter = ""

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Search and header controls
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search people…")
        self.search_edit.textChanged.connect(self.filter_people)
        left_layout.addWidget(self.search_edit)

        header_layout = QHBoxLayout()
        title = QLabel("People")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)

        add_btn = QPushButton("+ Add Person")
        add_btn.clicked.connect(self.on_add_person)
        import_btn = QPushButton("Import .ema")
        import_btn.clicked.connect(self.on_import)
        export_all_btn = QPushButton("Export All")
        export_all_btn.clicked.connect(self.on_export_all)
        self.dark_mode_btn = QPushButton("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)

        header_layout.addWidget(add_btn)
        header_layout.addWidget(import_btn)
        header_layout.addWidget(export_all_btn)
        header_layout.addWidget(self.dark_mode_btn)
        left_layout.addLayout(header_layout)

        self.person_list = QListWidget()
        self.person_list.setUniformItemSizes(True)
        self.person_list.itemClicked.connect(self.on_select_person)
        left_layout.addWidget(self.person_list)

        splitter.addWidget(left_panel)

        # Right panel
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        welcome = QLabel("Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Arial", 12))
        self.right_layout.addWidget(welcome)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 900])

        self.apply_theme()
        self.refresh_person_list()

    # ----- Settings / Theme -----
    def load_settings(self):
        try:
            if self.settings_file.exists():
                data = json.loads(self.settings_file.read_text(encoding="utf-8"))
                self.dark_mode = bool(data.get("dark_mode", False))
        except Exception:
            self.dark_mode = False

    def save_settings(self):
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix="settings_",
                suffix=".json",
                dir=str(self.settings_file.parent)
            )
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump({"dark_mode": self.dark_mode}, f, indent=2)
            os.replace(tmp_path, self.settings_file)
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def apply_theme(self):
        accent = "#3daee9" if not self.dark_mode else "#4cc2ff"
        if self.dark_mode:
            self.setStyleSheet(
                f"""
                QMainWindow {{ background-color: #151515; color: #e6e6e6; }}
                QWidget {{ background-color: #1f1f1f; color: #e6e6e6; }}
                QSplitter::handle {{ background: #2a2a2a; }}
                QListWidget {{ background-color: #1c1c1c; color: #e6e6e6; border: 1px solid #333; border-radius: 8px; }}
                QListWidget::item {{ padding: 8px 10px; border-radius: 6px; }}
                QListWidget::item:selected {{ background-color: {accent}; color: #0b0b0b; }}
                QLineEdit {{ background-color: #1c1c1c; color: #e6e6e6; border: 1px solid #333; padding: 6px 8px; border-radius: 6px; }}
                QPushButton {{ background-color: #2a2a2a; color: #e6e6e6; border: 1px solid #3a3a3a; padding: 8px 12px; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #333; }}
                QPushButton:pressed {{ background-color: #3a3a3a; }}
                QTabWidget::pane {{ border: 1px solid #333; border-radius: 8px; top: -1px; }}
                QTabBar::tab {{ background: #222; color: #ddd; padding: 8px 14px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }}
                QTabBar::tab:selected {{ background: #2a2a2a; color: #fff; }}
                QHeaderView::section {{ background-color: #222; color: #e6e6e6; border: none; border-bottom: 1px solid #333; padding: 10px; }}
                QTableWidget {{ background-color: #1c1c1c; color: #e6e6e6; border: 1px solid #333; border-radius: 8px; }}
                QTableWidget::item {{ padding: 8px 10px; }}
                QTableWidget::item:selected {{ background-color: {accent}; color: #0b0b0b; }}
                QScrollBar:vertical {{ background: #1e1e1e; width: 10px; margin: 0; }}
                QScrollBar::handle:vertical {{ background: #3a3a3a; border-radius: 5px; }}
                QScrollBar::handle:vertical:hover {{ background: #4a4a4a; }}
                QScrollBar:horizontal {{ background: #1e1e1e; height: 10px; }}
                QScrollBar::handle:horizontal {{ background: #3a3a3a; border-radius: 5px; }}
                """
            )
        else:
            self.setStyleSheet(
                f"""
                QMainWindow {{ background-color: #f4f6f8; color: #111; }}
                QWidget {{ background-color: #ffffff; color: #111; }}
                QSplitter::handle {{ background: #e6e9ec; }}
                QListWidget {{ background-color: #ffffff; color: #111; border: 1px solid #dfe3e7; border-radius: 8px; }}
                QListWidget::item {{ padding: 8px 10px; border-radius: 6px; }}
                QListWidget::item:selected {{ background-color: {accent}; color: #fff; }}
                QLineEdit {{ background-color: #ffffff; color: #111; border: 1px solid #dfe3e7; padding: 6px 8px; border-radius: 6px; }}
                QPushButton {{ background-color: #f3f5f7; color: #111; border: 1px solid #d7dce1; padding: 8px 12px; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #e8ebee; }}
                QPushButton:pressed {{ background-color: #e1e5ea; }}
                QTabWidget::pane {{ border: 1px solid #dfe3e7; border-radius: 8px; top: -1px; }}
                QTabBar::tab {{ background: #f3f5f7; color: #222; padding: 8px 14px; border: 1px solid #dfe3e7; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }}
                QTabBar::tab:selected {{ background: #ffffff; color: #111; }}
                QHeaderView::section {{ background-color: #f8f9fb; color: #222; border: none; border-bottom: 1px solid #e6e9ec; padding: 10px; }}
                QTableWidget {{ background-color: #ffffff; color: #111; border: 1px solid #dfe3e7; border-radius: 8px; }}
                QTableWidget::item {{ padding: 8px 10px; }}
                QTableWidget::item:selected {{ background-color: {accent}; color: #fff; }}
                QScrollBar:vertical {{ background: #f0f2f4; width: 10px; margin: 0; }}
                QScrollBar::handle:vertical {{ background: #cfd6dd; border-radius: 5px; }}
                QScrollBar::handle:vertical:hover {{ background: #c2cbd5; }}
                QScrollBar:horizontal {{ background: #f0f2f4; height: 10px; }}
                QScrollBar::handle:horizontal {{ background: #cfd6dd; border-radius: 5px; }}
                """
            )
        if hasattr(self, "dark_mode_btn"):
            self.dark_mode_btn.setText("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.apply_theme()

    # ----- People list -----
    def refresh_person_list(self):
        self.person_list.clear()
        filter_text = self._people_filter.lower().strip()
        for name in sorted(self.people.keys()):
            if filter_text and filter_text not in name.lower():
                continue
            self.person_list.addItem(name)

    def filter_people(self, text: str):
        self._people_filter = text
        self.refresh_person_list()

    def on_add_person(self):
        name, ok = QInputDialog.getText(self, "Add Person", "Enter person's name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        if name in self.people:
            QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")
            return
        self.store.ensure_person_dirs(name)
        person = PersonRecord.new(name)
        self.store.save_person(person)
        self.people[name] = person
        self.refresh_person_list()

    def on_select_person(self, item):
        person_name = item.text()
        self.current_person_name = person_name
        self.render_person_detail(person_name)

    def clear_right_panel(self):
        layout = self.right_layout
        while layout.count():
            child = layout.takeAt(0)
            w = child.widget()
            if w is not None:
                w.deleteLater()

    def render_person_detail(self, person_name: str):
        person = self.people.get(person_name)
        if not person:
            return
        self.clear_right_panel()

        header_layout = QHBoxLayout()
        title = QLabel(f"Evidence for: {person_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        export_btn = QPushButton("Export Evidence")
        export_btn.clicked.connect(lambda: self.on_export_single(person_name))
        delete_btn = QPushButton("Delete Person")
        delete_btn.clicked.connect(lambda: self.on_delete_person(person_name))
        header_layout.addWidget(export_btn)
        header_layout.addWidget(delete_btn)

        self.right_layout.addLayout(header_layout)

        tabs = QTabWidget()
        tabs.addTab(self.build_info_tab(person), "Information")
        tabs.addTab(self.build_media_tab(person, MEDIA_IMAGES, "Add Image", "Image files (*.png *.jpg *.jpeg *.gif *.bmp)"), "Images")
        tabs.addTab(self.build_media_tab(person, MEDIA_AUDIO, "Add Audio", "Audio files (*.mp3 *.wav *.m4a *.aac *.ogg)"), "Audio")
        tabs.addTab(self.build_media_tab(person, MEDIA_VIDEOS, "Add Video", "Video files (*.mp4 *.avi *.mov *.wmv *.flv *.mkv *.webm)"), "Videos")
        self.right_layout.addWidget(tabs)

    # ----- Info Tab -----
    def build_info_tab(self, person: PersonRecord) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Info Type:"))
        self.info_type_edit = QLineEdit()
        self.info_type_edit.setFixedWidth(150)
        add_layout.addWidget(self.info_type_edit)

        add_layout.addWidget(QLabel("Value:"))
        self.info_value_edit = QLineEdit()
        self.info_value_edit.setFixedWidth(250)
        add_layout.addWidget(self.info_value_edit)

        add_info_btn = QPushButton("Add Info")
        add_info_btn.clicked.connect(lambda: self.on_add_info(person))
        add_layout.addWidget(add_info_btn)
        layout.addLayout(add_layout)

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(3)
        self.info_table.setHorizontalHeaderLabels(["Type", "Value", "Actions"])
        self.info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.info_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.info_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.info_table.customContextMenuRequested.connect(lambda pos: self.on_info_context_menu(pos, person))
        self.info_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.info_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.info_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.setShowGrid(False)
        layout.addWidget(self.info_table)

        self.reload_info_table(person)
        return widget

    def reload_info_table(self, person: PersonRecord):
        self.info_table.setRowCount(0)
        for info_type, values in sorted(person.info.items()):
            for value in values:
                row = self.info_table.rowCount()
                self.info_table.insertRow(row)
                self.info_table.setItem(row, 0, QTableWidgetItem(info_type))
                self.info_table.setItem(row, 1, QTableWidgetItem(value))
                self.info_table.setItem(row, 2, QTableWidgetItem("Delete"))
                self.info_table.item(row, 2).setFlags(self.info_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)

    def on_add_info(self, person: PersonRecord):
        info_type = self.info_type_edit.text().strip()
        info_value = self.info_value_edit.text().strip()
        if not info_type or not info_value:
            return
        person.info.setdefault(info_type, []).append(info_value)
        self.store.save_person(person)
        self.info_type_edit.clear()
        self.info_value_edit.clear()
        self.reload_info_table(person)

    def on_info_context_menu(self, pos, person: PersonRecord):
        item = self.info_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        info_type = self.info_table.item(row, 0).text()
        info_value = self.info_table.item(row, 1).text()
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.info_table.mapToGlobal(pos))
        if action == delete_action:
            values = person.info.get(info_type, [])
            if info_value in values:
                values.remove(info_value)
                if not values:
                    person.info.pop(info_type, None)
                self.store.save_person(person)
                self.reload_info_table(person)
        elif action == edit_action:
            new_value, ok = QInputDialog.getText(self, f"Edit {info_type}", "Enter new value:", text=info_value)
            if ok:
                new_value = new_value.strip()
                if new_value and new_value != info_value:
                    values = person.info.get(info_type, [])
                    if info_value in values:
                        values.remove(info_value)
                    values.append(new_value)
                    self.store.save_person(person)
                    self.reload_info_table(person)

    # ----- Media Tabs -----
    def build_media_tab(self, person: PersonRecord, kind: str, add_label: str, file_filter: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        add_btn = QPushButton(add_label)
        add_btn.clicked.connect(lambda: self.on_add_media(person, kind, file_filter))
        layout.addWidget(add_btn)

        table = QTableWidget()
        table.setObjectName(f"table_{kind}")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Display Name", "Filename", "Actions"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.customContextMenuRequested.connect(lambda pos, t=table, k=kind: self.on_media_menu(person, k, t, pos))
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setIconSize(QSize(48, 48))
        layout.addWidget(table)

        self.reload_media_table(person, kind, table)
        return widget

    def reload_media_table(self, person: PersonRecord, kind: str, table: QTableWidget):
        table.setRowCount(0)
        items: List[MediaEntry] = getattr(person, kind)
        for entry in items:
            row = table.rowCount()
            table.insertRow(row)
            name_item = QTableWidgetItem(entry.display_name)
            if kind == MEDIA_IMAGES:
                thumb = self.store.image_thumbnail(person, entry.filename)
                if thumb and thumb.exists():
                    pix = QPixmap(str(thumb))
                    name_item.setIcon(QIcon(pix))
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(entry.filename))
            table.setItem(row, 2, QTableWidgetItem(self._actions_label(kind)))
            table.item(row, 2).setFlags(table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _actions_label(self, kind: str) -> str:
        if kind == MEDIA_IMAGES:
            return "Open | Rename | Delete"
        return "Play | Rename | Delete"

    def on_add_media(self, person: PersonRecord, kind: str, file_filter: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", f"{file_filter};;All files (*)")
        if not path:
            return
        src = Path(path)

        def do_copy():
            self.store.add_media_file(person, kind, src)

        pd = QProgressDialog("Copying file...", None, 0, 0, self)
        pd.setWindowModality(Qt.WindowModality.ApplicationModal)
        pd.setMinimumDuration(0)
        worker = CallableWorker(do_copy)
        worker.signals.finished.connect(pd.close)
        worker.signals.error.connect(lambda e: QMessageBox.critical(self, "Copy Error", e))
        worker.signals.finished.connect(lambda: self._after_media_added(person, kind))
        self.thread_pool.start(worker)
        pd.show()

    def _after_media_added(self, person: PersonRecord, kind: str):
        table = self.findChild(QTableWidget, f"table_{kind}")
        if table:
            self.reload_media_table(person, kind, table)

    def on_media_menu(self, person: PersonRecord, kind: str, table: QTableWidget, pos):
        item = table.itemAt(pos)
        if not item:
            return
        row = item.row()
        display_name = table.item(row, 0).text()
        filename = table.item(row, 1).text()
        menu = QMenu(self)
        open_or_play = menu.addAction("Open" if kind == MEDIA_IMAGES else "Play")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec(table.mapToGlobal(pos))
        if action == open_or_play:
            fpath = self.store.person_dir(person.name) / kind / filename
            self.store.open_path(fpath)
        elif action == rename_action:
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new display name:", text=display_name)
            if ok:
                new_name = new_name.strip()
                if new_name and new_name != display_name:
                    self.store.rename_media_display(person, kind, filename, new_name)
                    self.reload_media_table(person, kind, table)
        elif action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete", f"Delete '{filename}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.store.delete_media_file(person, kind, filename)
                self.reload_media_table(person, kind, table)

    # ----- Export / Import -----
    def on_export_single(self, person_name: str):
        person_dir = self.store.person_dir(person_name)
        if not person_dir.exists():
            QMessageBox.critical(self, "Export Error", f"No evidence folder found for {person_name}")
            return
        safe = person_name.lower().replace(" ", "-")
        default = f"{safe}.ema"
        out, _ = QFileDialog.getSaveFileName(self, f"Export evidence for {person_name}", default, "Evidence Manager Archive (*.ema)")
        if not out:
            return
        if not out.endswith(".ema"):
            out += ".ema"

        def do_zip():
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                meta = {"export_type": "single_person", "person_name": person_name, "export_date": datetime.now().isoformat()}
                z.writestr("metadata.json", json.dumps(meta, indent=2))
                for root, _, files in os.walk(person_dir):
                    for f in files:
                        fp = Path(root) / f
                        rel = fp.relative_to(person_dir)
                        arc = Path("Evidence") / person_dir.name / rel
                        z.write(fp, arcname=str(arc))

        pd = QProgressDialog("Exporting...", None, 0, 0, self)
        pd.setWindowModality(Qt.WindowModality.ApplicationModal)
        pd.setMinimumDuration(0)
        worker = CallableWorker(do_zip)
        worker.signals.finished.connect(pd.close)
        worker.signals.error.connect(lambda e: QMessageBox.critical(self, "Export Error", e))
        worker.signals.finished.connect(lambda: QMessageBox.information(self, "Export Complete", f"Exported to:\n{out}"))
        self.thread_pool.start(worker)
        pd.show()

    def on_export_all(self):
        if not self.store.root.exists():
            QMessageBox.critical(self, "Export Error", "No Evidence folder found to export.")
            return
        out, _ = QFileDialog.getSaveFileName(self, "Export all evidence", "", "Evidence Manager Archive (*.ema)")
        if not out:
            return
        if not out.endswith(".ema"):
            out += ".ema"

        def do_zip():
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                meta = {"export_type": "all_evidence", "export_date": datetime.now().isoformat(), "person_count": len(self.people)}
                z.writestr("metadata.json", json.dumps(meta, indent=2))
                for root, _, files in os.walk(self.store.root):
                    for f in files:
                        fp = Path(root) / f
                        arc = fp.relative_to(self.store.root.parent)
                        z.write(fp, arcname=str(arc))

        pd = QProgressDialog("Exporting...", None, 0, 0, self)
        pd.setWindowModality(Qt.WindowModality.ApplicationModal)
        pd.setMinimumDuration(0)
        worker = CallableWorker(do_zip)
        worker.signals.finished.connect(pd.close)
        worker.signals.error.connect(lambda e: QMessageBox.critical(self, "Export Error", e))
        worker.signals.finished.connect(lambda: QMessageBox.information(self, "Export Complete", f"Exported to:\n{out}"))
        self.thread_pool.start(worker)
        pd.show()

    def on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import evidence", "", "Evidence Manager Archive (*.ema)")
        if not path:
            return

        def do_import():
            with zipfile.ZipFile(path, "r") as z:
                if "metadata.json" not in z.namelist():
                    raise RuntimeError("Invalid .ema file: No metadata found.")
                meta = json.loads(z.read("metadata.json").decode("utf-8"))
                export_type = meta.get("export_type")
                with tempfile.TemporaryDirectory() as tmp:
                    z.extractall(tmp)
                    evidence_src = Path(tmp) / "Evidence"
                    if not evidence_src.exists():
                        raise RuntimeError("Invalid .ema file: Could not find Evidence folder.")
                    if export_type == "single_person":
                        # Expect exactly one subdir
                        subs = [p for p in evidence_src.iterdir() if p.is_dir()]
                        if len(subs) != 1:
                            raise RuntimeError("Invalid .ema file: Could not find person folder in Evidence directory.")
                        src = subs[0]
                        dest = self.store.root / src.name
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(src, dest)
                        # load person
                        pname = src.name.replace("_", " ")
                        data_file = dest / "person_data.json"
                        person = PersonRecord.new(pname)
                        if data_file.exists():
                            person = PersonRecord.from_dict(json.loads(data_file.read_text(encoding="utf-8")))
                        self.people[pname] = person
                    elif export_type == "all_evidence":
                        for src in evidence_src.iterdir():
                            if not src.is_dir():
                                continue
                            dest = self.store.root / src.name
                            pname = src.name.replace("_", " ")
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(src, dest)
                            data_file = dest / "person_data.json"
                            person = PersonRecord.new(pname)
                            if data_file.exists():
                                person = PersonRecord.from_dict(json.loads(data_file.read_text(encoding="utf-8")))
                            self.people[pname] = person
                    else:
                        raise RuntimeError("Unknown export type in .ema file.")

        pd = QProgressDialog("Importing...", None, 0, 0, self)
        pd.setWindowModality(Qt.WindowModality.ApplicationModal)
        pd.setMinimumDuration(0)
        worker = CallableWorker(do_import)
        worker.signals.error.connect(lambda e: QMessageBox.critical(self, "Import Error", e))
        worker.signals.finished.connect(pd.close)
        worker.signals.finished.connect(self.refresh_person_list)
        self.thread_pool.start(worker)
        pd.show()

    def on_delete_person(self, person_name: str):
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete person '{person_name}' and all their evidence?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        # Remove from memory and disk
        self.people.pop(person_name, None)
        pdir = self.store.person_dir(person_name)
        if pdir.exists():
            try:
                shutil.rmtree(pdir)
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", str(e))
                return
        self.current_person_name = None
        self.refresh_person_list()
        self.clear_right_panel()
        welcome = QLabel("Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Arial", 12))
        self.right_layout.addWidget(welcome)


def main():
    app = QApplication(sys.argv)
    window = EvidenceManagerPyQt()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


