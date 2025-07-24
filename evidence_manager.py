#!/usr/bin/env python3
"""
Evidence Manager - PyQt6 Version
A comprehensive evidence management application built with Python and PyQt6.
"""

import sys
import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QTabWidget, QPushButton, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QInputDialog, QMenu,
                             QSplitter, QFrame, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QAction
from PIL import Image

class EvidenceManagerPyQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.evidence_dir = "Evidence"
        self.current_person = None
        self.person_data = {}
        self.settings_file = "settings.json"
        self.dark_mode = False
        self.load_settings()
        self.ensure_evidence_directory()
        self.load_persons()
        self.init_ui()
        self.apply_theme()
        
    def load_settings(self):
        """Load settings from settings.json"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get('dark_mode', False)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.dark_mode = False
    
    def save_settings(self):
        """Save settings to settings.json"""
        try:
            settings = {
                'dark_mode': self.dark_mode
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def apply_theme(self):
        """Apply the current theme (light or dark mode)"""
        if self.dark_mode:
            # Dark mode colors
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #e6e6e6;
                }
                QWidget {
                    background-color: #2d2d2d;
                    color: #e6e6e6;
                }
                QListWidget {
                    background-color: #282828;
                    color: #e6e6e6;
                    border: 1px solid #404040;
                }
                QListWidget::item {
                    background-color: #282828;
                    color: #e6e6e6;
                    padding: 5px;
                    border: 1px solid transparent;
                }
                QListWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                    border: 1px solid #0078d4;
                }
                QListWidget::item:hover {
                    background-color: #404040;
                    border: 1px solid #404040;
                }
                QTableWidget {
                    background-color: #282828;
                    color: #e6e6e6;
                    gridline-color: #404040;
                    border: 1px solid #404040;
                }
                QTableWidget::item {
                    background-color: #282828;
                    color: #e6e6e6;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #323232;
                    color: #e6e6e6;
                    border: 1px solid #404040;
                    padding: 5px;
                    border-radius: 3px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
                QPushButton:pressed {
                    background-color: #505050;
                    outline: none;
                    border: 1px solid #404040;
                }
                QPushButton:focus {
                    border: 1px solid #404040;
                    outline: none;
                }
                QPushButton:focus:pressed {
                    outline: none;
                    border: 1px solid #404040;
                }
                QLineEdit {
                    background-color: #282828;
                    color: #e6e6e6;
                    border: 1px solid #404040;
                    padding: 3px;
                }
                QTabWidget::pane {
                    border: 1px solid #404040;
                    background-color: #2d2d2d;
                }
                QTabBar::tab {
                    background-color: #323232;
                    color: #e6e6e6;
                    padding: 8px 12px;
                    border: 1px solid #404040;
                }
                QTabBar::tab:selected {
                    background-color: #404040;
                }
                QHeaderView::section {
                    background-color: #323232;
                    color: #e6e6e6;
                    border: 1px solid #404040;
                    padding: 5px;
                }
            """)
        else:
            # Light mode colors
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QListWidget {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QListWidget::item {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid transparent;
                }
                QListWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                    border: 1px solid #0078d4;
                }
                QListWidget::item:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #cccccc;
                }
                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    gridline-color: #cccccc;
                    border: 1px solid #cccccc;
                }
                QTableWidget::item {
                    background-color: #ffffff;
                    color: #000000;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                    outline: none;
                    border: 1px solid #cccccc;
                }
                QPushButton:focus {
                    border: 1px solid #cccccc;
                    outline: none;
                }
                QPushButton:focus:pressed {
                    outline: none;
                    border: 1px solid #cccccc;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 3px;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #000000;
                    padding: 8px 12px;
                    border: 1px solid #cccccc;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 5px;
                }
            """)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.apply_theme()
        # Update button text
        if hasattr(self, 'dark_mode_btn'):
            self.dark_mode_btn.setText("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")
        
    def ensure_evidence_directory(self):
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)
            
    def load_persons(self):
        self.person_data = {}
        if os.path.exists(self.evidence_dir):
            for item in os.listdir(self.evidence_dir):
                item_path = os.path.join(self.evidence_dir, item)
                if os.path.isdir(item_path):
                    person_name = item.replace('_', ' ')
                    data_file = os.path.join(item_path, 'person_data.json')
                    if os.path.exists(data_file):
                        try:
                            with open(data_file, 'r', encoding='utf-8') as f:
                                self.person_data[person_name] = json.load(f)
                                # Ensure backward compatibility
                                if 'videos' not in self.person_data[person_name]:
                                    self.person_data[person_name]['videos'] = []
                                if 'audio' not in self.person_data[person_name]:
                                    self.person_data[person_name]['audio'] = []
                        except:
                            self.person_data[person_name] = {
                                'name': person_name,
                                'created': datetime.now().isoformat(),
                                'info': {},
                                'images': [],
                                'audio': [],
                                'videos': []
                            }
                    else:
                        self.person_data[person_name] = {
                            'name': person_name,
                            'created': datetime.now().isoformat(),
                            'info': {},
                            'images': [],
                            'audio': [],
                            'videos': []
                        }
    
    def init_ui(self):
        self.setWindowTitle("Evidence Manager - PyQt6")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel
        self.right_panel = self.create_right_panel()
        splitter.addWidget(self.right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        self.update_person_list()
        self.center_window()
        
    def create_left_panel(self):
        """Create the left panel with people list and buttons"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("People")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Buttons panel
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Person")
        add_btn.clicked.connect(self.on_add_person)
        
        import_btn = QPushButton("Import .ema")
        import_btn.clicked.connect(self.on_import_evidence)
        
        export_all_btn = QPushButton("Export All")
        export_all_btn.clicked.connect(self.on_export_all_evidence)
        
        self.dark_mode_btn = QPushButton("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(export_all_btn)
        buttons_layout.addWidget(self.dark_mode_btn)
        
        header_layout.addLayout(buttons_layout)
        layout.addLayout(header_layout)
        
        # People list
        self.person_list = QListWidget()
        self.person_list.itemClicked.connect(self.on_person_selected)
        layout.addWidget(self.person_list)
        
        return panel
        
    def create_right_panel(self):
        """Create the right panel with welcome message"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        welcome_text = QLabel("Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.")
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_text.setFont(QFont("Arial", 12))
        layout.addWidget(welcome_text)
        
        return panel
        
    def update_person_list(self):
        """Update the people list"""
        self.person_list.clear()
        for person_name in sorted(self.person_data.keys()):
            self.person_list.addItem(person_name)
            
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def on_add_person(self):
        """Add a new person"""
        name, ok = QInputDialog.getText(self, "Add Person", "Enter person's name:")
        if ok and name.strip():
            name = name.strip()
            folder_name = name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            if not os.path.exists(person_dir):
                os.makedirs(person_dir)
                os.makedirs(os.path.join(person_dir, 'images'))
                os.makedirs(os.path.join(person_dir, 'audio'))
                os.makedirs(os.path.join(person_dir, 'videos'))
            self.person_data[name] = {
                'name': name,
                'created': datetime.now().isoformat(),
                'info': {},
                'images': [],
                'audio': [],
                'videos': []
            }
            self.save_person_data(name)
            self.update_person_list()
            
    def on_person_selected(self, item):
        """Handle person selection"""
        person_name = item.text()
        self.current_person = person_name
        self.show_person_details(person_name)
        
    def show_person_details(self, person_name):
        """Show details for the selected person"""
        # Clear right panel
        for child in self.right_panel.children():
            if isinstance(child, QWidget):
                child.deleteLater()
        
        # Remove existing layout if any
        if self.right_panel.layout():
            QWidget().setLayout(self.right_panel.layout())
        
        # Create new layout
        layout = QVBoxLayout(self.right_panel)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(f"Evidence for: {person_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        export_btn = QPushButton("Export Evidence")
        export_btn.clicked.connect(lambda: self.on_export_evidence(person_name))
        
        delete_btn = QPushButton("Delete Person")
        delete_btn.clicked.connect(lambda: self.on_delete_person(person_name))
        
        header_layout.addWidget(export_btn)
        header_layout.addWidget(delete_btn)
        layout.addLayout(header_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Information tab
        info_tab = self.create_info_tab(person_name)
        tab_widget.addTab(info_tab, "Information")
        
        # Images tab
        images_tab = self.create_images_tab(person_name)
        tab_widget.addTab(images_tab, "Images")
        
        # Audio tab
        audio_tab = self.create_audio_tab(person_name)
        tab_widget.addTab(audio_tab, "Audio")
        
        # Videos tab
        videos_tab = self.create_video_tab(person_name)
        tab_widget.addTab(videos_tab, "Videos")
        
        layout.addWidget(tab_widget)
        
    def create_info_tab(self, person_name):
        """Create the information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add info panel
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Info Type:"))
        self.info_type_edit = QLineEdit()
        self.info_type_edit.setFixedWidth(150)
        add_layout.addWidget(self.info_type_edit)
        
        add_layout.addWidget(QLabel("Value:"))
        self.info_value_edit = QLineEdit()
        self.info_value_edit.setFixedWidth(200)
        add_layout.addWidget(self.info_value_edit)
        
        add_info_btn = QPushButton("Add Info")
        add_info_btn.clicked.connect(lambda: self.on_add_info(person_name))
        add_layout.addWidget(add_info_btn)
        
        layout.addLayout(add_layout)
        
        # Info table
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(3)
        self.info_table.setHorizontalHeaderLabels(["Type", "Value", "Actions"])
        self.info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.info_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.info_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.info_table.customContextMenuRequested.connect(lambda pos: self.on_info_context_menu(pos, person_name))
        self.info_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.info_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.info_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout.addWidget(self.info_table)
        
        self.load_info_table(person_name)
        return widget
        
    def create_images_tab(self, person_name):
        """Create the images tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add image button
        add_btn = QPushButton("Add Image")
        add_btn.clicked.connect(lambda: self.on_add_image(person_name))
        layout.addWidget(add_btn)
        
        # Images table
        self.images_table = QTableWidget()
        self.images_table.setColumnCount(3)
        self.images_table.setHorizontalHeaderLabels(["Display Name", "Filename", "Actions"])
        self.images_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.images_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.images_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.images_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.images_table.customContextMenuRequested.connect(lambda pos: self.on_image_context_menu(pos, person_name))
        self.images_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.images_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.images_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout.addWidget(self.images_table)
        
        self.load_images_table(person_name)
        return widget
        
    def create_audio_tab(self, person_name):
        """Create the audio tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add audio button
        add_btn = QPushButton("Add Audio")
        add_btn.clicked.connect(lambda: self.on_add_audio(person_name))
        layout.addWidget(add_btn)
        
        # Audio table
        self.audio_table = QTableWidget()
        self.audio_table.setColumnCount(3)
        self.audio_table.setHorizontalHeaderLabels(["Display Name", "Filename", "Actions"])
        self.audio_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.audio_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.audio_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.audio_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.audio_table.customContextMenuRequested.connect(lambda pos: self.on_audio_context_menu(pos, person_name))
        self.audio_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.audio_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.audio_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout.addWidget(self.audio_table)
        
        self.load_audio_table(person_name)
        return widget
        
    def create_video_tab(self, person_name):
        """Create the video tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add video button
        add_btn = QPushButton("Add Video")
        add_btn.clicked.connect(lambda: self.on_add_video(person_name))
        layout.addWidget(add_btn)
        
        # Video table
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(3)
        self.video_table.setHorizontalHeaderLabels(["Display Name", "Filename", "Actions"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.video_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_table.customContextMenuRequested.connect(lambda pos: self.on_video_context_menu(pos, person_name))
        self.video_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.video_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.video_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout.addWidget(self.video_table)
        
        self.load_video_table(person_name)
        return widget

    # Continue with the rest of the methods...
    def on_add_info(self, person_name):
        """Add information for a person"""
        info_type = self.info_type_edit.text().strip()
        info_value = self.info_value_edit.text().strip()
        if info_type and info_value:
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': [],
                    'videos': []
                }
            if info_type not in self.person_data[person_name]['info']:
                self.person_data[person_name]['info'][info_type] = []
            self.person_data[person_name]['info'][info_type].append(info_value)
            self.save_person_data(person_name)
            self.load_info_table(person_name)
            self.info_type_edit.clear()
            self.info_value_edit.clear()

    def load_info_table(self, person_name):
        """Load information into the table"""
        self.info_table.setRowCount(0)
        if person_name in self.person_data:
            row = 0
            for info_type, values in self.person_data[person_name]['info'].items():
                for value in values:
                    self.info_table.insertRow(row)
                    self.info_table.setItem(row, 0, QTableWidgetItem(info_type))
                    self.info_table.setItem(row, 1, QTableWidgetItem(value))
                    self.info_table.setItem(row, 2, QTableWidgetItem("Delete"))
                    
                    # Make Actions column non-editable
                    self.info_table.item(row, 2).setFlags(self.info_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    row += 1

    def on_info_context_menu(self, pos, person_name):
        """Show context menu for info items"""
        item = self.info_table.itemAt(pos)
        if item:
            row = item.row()
            info_type = self.info_table.item(row, 0).text()
            info_value = self.info_table.item(row, 1).text()
            
            menu = QMenu(self)
            delete_action = menu.addAction("Delete")
            edit_action = menu.addAction("Edit")
            
            action = menu.exec(self.info_table.mapToGlobal(pos))
            if action == delete_action:
                self.delete_info_item(person_name, info_type, info_value)
            elif action == edit_action:
                self.edit_info_item(person_name, info_type, info_value, row)

    def delete_info_item(self, person_name, info_type, info_value):
        """Delete an information item"""
        if person_name in self.person_data and info_type in self.person_data[person_name]['info']:
            if info_value in self.person_data[person_name]['info'][info_type]:
                self.person_data[person_name]['info'][info_type].remove(info_value)
                if not self.person_data[person_name]['info'][info_type]:
                    del self.person_data[person_name]['info'][info_type]
                self.save_person_data(person_name)
                self.load_info_table(person_name)

    def edit_info_item(self, person_name, info_type, info_value, row):
        """Edit an information item"""
        new_value, ok = QInputDialog.getText(self, f"Edit {info_type}", "Enter new value:", text=info_value)
        if ok and new_value.strip() and new_value != info_value:
            # Remove the old value
            if person_name in self.person_data and info_type in self.person_data[person_name]['info']:
                if info_value in self.person_data[person_name]['info'][info_type]:
                    self.person_data[person_name]['info'][info_type].remove(info_value)
            
            # Ensure the info type exists
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': [],
                    'videos': []
                }
            if info_type not in self.person_data[person_name]['info']:
                self.person_data[person_name]['info'][info_type] = []
            
            # Add the new value
            self.person_data[person_name]['info'][info_type].append(new_value.strip())
            self.save_person_data(person_name)
            self.load_info_table(person_name)

    def save_person_data(self, person_name):
        """Save person data to JSON file"""
        folder_name = person_name.replace(' ', '_')
        person_dir = os.path.join(self.evidence_dir, folder_name)
        data_file = os.path.join(person_dir, 'person_data.json')
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.person_data[person_name], f, indent=2, ensure_ascii=False)

    def on_add_image(self, person_name):
        """Add an image file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select image file", "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*)"
        )
        if filepath:
            filename = os.path.basename(filepath)
            folder_name = person_name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            images_dir = os.path.join(person_dir, 'images')
            if not os.path.exists(person_dir):
                os.makedirs(person_dir)
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            dest_path = os.path.join(images_dir, filename)
            shutil.copy2(filepath, dest_path)
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': [],
                    'videos': []
                }
            # Store as dict with display name and filename
            image_data = {
                'display_name': os.path.splitext(filename)[0],
                'filename': filename
            }
            self.person_data[person_name]['images'].append(image_data)
            self.save_person_data(person_name)
            self.load_images_table(person_name)

    def load_images_table(self, person_name):
        """Load images into the table"""
        self.images_table.setRowCount(0)
        if person_name in self.person_data:
            row = 0
            for image_data in self.person_data[person_name]['images']:
                if isinstance(image_data, dict):
                    display_name = image_data.get('display_name', '')
                    filename = image_data.get('filename', '')
                else:
                    # Handle old format
                    filename = image_data
                    display_name = os.path.splitext(filename)[0]
                self.images_table.insertRow(row)
                self.images_table.setItem(row, 0, QTableWidgetItem(display_name))
                self.images_table.setItem(row, 1, QTableWidgetItem(filename))
                self.images_table.setItem(row, 2, QTableWidgetItem("Open | Rename | Delete"))
                
                # Make Actions column non-editable
                self.images_table.item(row, 2).setFlags(self.images_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                row += 1

    def on_image_context_menu(self, pos, person_name):
        """Show context menu for image items"""
        item = self.images_table.itemAt(pos)
        if item:
            row = item.row()
            display_name = self.images_table.item(row, 0).text()
            filename = self.images_table.item(row, 1).text()
            
            menu = QMenu(self)
            open_action = menu.addAction("Open Image")
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec(self.images_table.mapToGlobal(pos))
            if action == open_action:
                self.open_image_file(person_name, filename)
            elif action == rename_action:
                self.rename_image(person_name, display_name, filename, row)
            elif action == delete_action:
                self.delete_image(person_name, filename)

    def open_image_file(self, person_name, filename):
        """Open an image file"""
        folder_name = person_name.replace(' ', '_')
        image_path = os.path.join(self.evidence_dir, folder_name, 'images', filename)
        try:
            os.startfile(image_path)
        except:
            QMessageBox.critical(self, "Error", f"Could not open image: {image_path}")

    def rename_image(self, person_name, current_display_name, filename, row):
        """Rename an image"""
        new_display_name, ok = QInputDialog.getText(
            self, "Rename Image", "Enter new display name:", text=current_display_name
        )
        if ok and new_display_name.strip() and new_display_name != current_display_name:
            # Update the image data
            for image_data in self.person_data[person_name]['images']:
                if isinstance(image_data, dict) and image_data.get('filename') == filename:
                    image_data['display_name'] = new_display_name.strip()
                    break
                elif image_data == filename:  # Handle old format
                    idx = self.person_data[person_name]['images'].index(image_data)
                    self.person_data[person_name]['images'][idx] = {
                        'display_name': new_display_name.strip(),
                        'filename': filename
                    }
                    break
            self.save_person_data(person_name)
            self.load_images_table(person_name)

    def delete_image(self, person_name, filename):
        """Delete an image"""
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete image '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from person data
            if person_name in self.person_data:
                for i, image_data in enumerate(self.person_data[person_name]['images']):
                    if isinstance(image_data, dict) and image_data.get('filename') == filename:
                        del self.person_data[person_name]['images'][i]
                        break
                    elif image_data == filename:  # Handle old format
                        self.person_data[person_name]['images'].remove(filename)
                        break
                self.save_person_data(person_name)
            
            # Delete file
            folder_name = person_name.replace(' ', '_')
            image_path = os.path.join(self.evidence_dir, folder_name, 'images', filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Reload images
            self.load_images_table(person_name)

    def on_add_audio(self, person_name):
        """Add an audio file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select audio file", "",
            "Audio files (*.mp3 *.wav *.m4a *.aac *.ogg);;All files (*)"
        )
        if filepath:
            filename = os.path.basename(filepath)
            folder_name = person_name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            audio_dir = os.path.join(person_dir, 'audio')
            if not os.path.exists(person_dir):
                os.makedirs(person_dir)
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            dest_path = os.path.join(audio_dir, filename)
            shutil.copy2(filepath, dest_path)
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': [],
                    'videos': []
                }
            # Store as dict with display name and filename
            audio_data = {
                'display_name': os.path.splitext(filename)[0],
                'filename': filename
            }
            self.person_data[person_name]['audio'].append(audio_data)
            self.save_person_data(person_name)
            self.load_audio_table(person_name)

    def load_audio_table(self, person_name):
        """Load audio into the table"""
        self.audio_table.setRowCount(0)
        if person_name in self.person_data:
            row = 0
            for audio_data in self.person_data[person_name]['audio']:
                if isinstance(audio_data, dict):
                    display_name = audio_data.get('display_name', '')
                    filename = audio_data.get('filename', '')
                else:
                    # Handle old format
                    filename = audio_data
                    display_name = os.path.splitext(filename)[0]
                self.audio_table.insertRow(row)
                self.audio_table.setItem(row, 0, QTableWidgetItem(display_name))
                self.audio_table.setItem(row, 1, QTableWidgetItem(filename))
                self.audio_table.setItem(row, 2, QTableWidgetItem("Play | Rename | Delete"))
                
                # Make Actions column non-editable
                self.audio_table.item(row, 2).setFlags(self.audio_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                row += 1

    def on_audio_context_menu(self, pos, person_name):
        """Show context menu for audio items"""
        item = self.audio_table.itemAt(pos)
        if item:
            row = item.row()
            display_name = self.audio_table.item(row, 0).text()
            filename = self.audio_table.item(row, 1).text()
            
            menu = QMenu(self)
            play_action = menu.addAction("Play Audio")
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec(self.audio_table.mapToGlobal(pos))
            if action == play_action:
                self.play_audio_file(person_name, filename)
            elif action == rename_action:
                self.rename_audio(person_name, display_name, filename, row)
            elif action == delete_action:
                self.delete_audio(person_name, filename)

    def play_audio_file(self, person_name, filename):
        """Play an audio file"""
        folder_name = person_name.replace(' ', '_')
        audio_path = os.path.join(self.evidence_dir, folder_name, 'audio', filename)
        try:
            os.startfile(audio_path)
        except:
            QMessageBox.critical(self, "Error", f"Could not play audio: {audio_path}")

    def rename_audio(self, person_name, current_display_name, filename, row):
        """Rename an audio file"""
        new_display_name, ok = QInputDialog.getText(
            self, "Rename Audio", "Enter new display name:", text=current_display_name
        )
        if ok and new_display_name.strip() and new_display_name != current_display_name:
            # Update the audio data
            for audio_data in self.person_data[person_name]['audio']:
                if isinstance(audio_data, dict) and audio_data.get('filename') == filename:
                    audio_data['display_name'] = new_display_name.strip()
                    break
                elif audio_data == filename:  # Handle old format
                    idx = self.person_data[person_name]['audio'].index(audio_data)
                    self.person_data[person_name]['audio'][idx] = {
                        'display_name': new_display_name.strip(),
                        'filename': filename
                    }
                    break
            self.save_person_data(person_name)
            self.load_audio_table(person_name)

    def delete_audio(self, person_name, filename):
        """Delete an audio file"""
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete audio '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from person data
            if person_name in self.person_data:
                for i, audio_data in enumerate(self.person_data[person_name]['audio']):
                    if isinstance(audio_data, dict) and audio_data.get('filename') == filename:
                        del self.person_data[person_name]['audio'][i]
                        break
                    elif audio_data == filename:  # Handle old format
                        self.person_data[person_name]['audio'].remove(filename)
                        break
                self.save_person_data(person_name)
            
            # Delete file
            folder_name = person_name.replace(' ', '_')
            audio_path = os.path.join(self.evidence_dir, folder_name, 'audio', filename)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Reload audio
            self.load_audio_table(person_name)

    def on_add_video(self, person_name):
        """Add a video file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select video file", "",
            "Video files (*.mp4 *.avi *.mov *.wmv *.flv *.mkv *.webm);;All files (*)"
        )
        if filepath:
            filename = os.path.basename(filepath)
            folder_name = person_name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            videos_dir = os.path.join(person_dir, 'videos')
            if not os.path.exists(person_dir):
                os.makedirs(person_dir)
            if not os.path.exists(videos_dir):
                os.makedirs(videos_dir)
            dest_path = os.path.join(videos_dir, filename)
            shutil.copy2(filepath, dest_path)
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': [],
                    'videos': []
                }
            # Ensure videos array exists
            if 'videos' not in self.person_data[person_name]:
                self.person_data[person_name]['videos'] = []
            # Store as dict with display name and filename
            video_data = {
                'display_name': os.path.splitext(filename)[0],
                'filename': filename
            }
            self.person_data[person_name]['videos'].append(video_data)
            self.save_person_data(person_name)
            self.load_video_table(person_name)

    def load_video_table(self, person_name):
        """Load videos into the table"""
        self.video_table.setRowCount(0)
        if person_name in self.person_data:
            row = 0
            for video_data in self.person_data[person_name].get('videos', []):
                if isinstance(video_data, dict):
                    display_name = video_data.get('display_name', '')
                    filename = video_data.get('filename', '')
                else:
                    # Handle old format
                    filename = video_data
                    display_name = os.path.splitext(filename)[0]
                self.video_table.insertRow(row)
                self.video_table.setItem(row, 0, QTableWidgetItem(display_name))
                self.video_table.setItem(row, 1, QTableWidgetItem(filename))
                self.video_table.setItem(row, 2, QTableWidgetItem("Play | Rename | Delete"))
                
                # Make Actions column non-editable
                self.video_table.item(row, 2).setFlags(self.video_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                row += 1

    def on_video_context_menu(self, pos, person_name):
        """Show context menu for video items"""
        item = self.video_table.itemAt(pos)
        if item:
            row = item.row()
            display_name = self.video_table.item(row, 0).text()
            filename = self.video_table.item(row, 1).text()
            
            menu = QMenu(self)
            play_action = menu.addAction("Play Video")
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec(self.video_table.mapToGlobal(pos))
            if action == play_action:
                self.play_video_file(person_name, filename)
            elif action == rename_action:
                self.rename_video(person_name, display_name, filename, row)
            elif action == delete_action:
                self.delete_video(person_name, filename)

    def play_video_file(self, person_name, filename):
        """Play a video file"""
        folder_name = person_name.replace(' ', '_')
        video_path = os.path.join(self.evidence_dir, folder_name, 'videos', filename)
        try:
            os.startfile(video_path)
        except:
            QMessageBox.critical(self, "Error", f"Could not play video: {video_path}")

    def rename_video(self, person_name, current_display_name, filename, row):
        """Rename a video file"""
        new_display_name, ok = QInputDialog.getText(
            self, "Rename Video", "Enter new display name:", text=current_display_name
        )
        if ok and new_display_name.strip() and new_display_name != current_display_name:
            # Ensure videos array exists
            if 'videos' not in self.person_data[person_name]:
                self.person_data[person_name]['videos'] = []
            # Update the video data
            for video_data in self.person_data[person_name]['videos']:
                if isinstance(video_data, dict) and video_data.get('filename') == filename:
                    video_data['display_name'] = new_display_name.strip()
                    break
                elif video_data == filename:  # Handle old format
                    idx = self.person_data[person_name]['videos'].index(video_data)
                    self.person_data[person_name]['videos'][idx] = {
                        'display_name': new_display_name.strip(),
                        'filename': filename
                    }
                    break
            self.save_person_data(person_name)
            self.load_video_table(person_name)

    def delete_video(self, person_name, filename):
        """Delete a video file"""
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete video '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from person data
            if person_name in self.person_data:
                # Ensure videos array exists
                if 'videos' not in self.person_data[person_name]:
                    self.person_data[person_name]['videos'] = []
                for i, video_data in enumerate(self.person_data[person_name]['videos']):
                    if isinstance(video_data, dict) and video_data.get('filename') == filename:
                        del self.person_data[person_name]['videos'][i]
                        break
                    elif video_data == filename:  # Handle old format
                        self.person_data[person_name]['videos'].remove(filename)
                        break
                self.save_person_data(person_name)
            
            # Delete file
            folder_name = person_name.replace(' ', '_')
            video_path = os.path.join(self.evidence_dir, folder_name, 'videos', filename)
            if os.path.exists(video_path):
                os.remove(video_path)
            
            # Reload videos
            self.load_video_table(person_name)

    def on_export_evidence(self, person_name):
        """Export person's evidence as an .ema file"""
        folder_name = person_name.replace(' ', '_')
        person_dir = os.path.join(self.evidence_dir, folder_name)
        
        if not os.path.exists(person_dir):
            QMessageBox.critical(self, "Export Error", f"No evidence folder found for {person_name}")
            return
            
        # Generate filename from person name
        safe_filename = person_name.lower().replace(' ', '-')
        default_filename = f"{safe_filename}.ema"
        
        # Ask user for save location
        ema_path, _ = QFileDialog.getSaveFileName(
            self, f"Export evidence for {person_name}",
            default_filename, "Evidence Manager Archive (*.ema)"
        )
        
        if not ema_path:
            return
            
        if not ema_path.endswith('.ema'):
            ema_path += '.ema'
        
        try:
            with zipfile.ZipFile(ema_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    'export_type': 'single_person',
                    'person_name': person_name,
                    'export_date': datetime.now().isoformat()
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # Add all files
                for root, dirs, files in os.walk(person_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, person_dir)
                        arcname = os.path.join('Evidence', folder_name, relative_path)
                        zipf.write(file_path, arcname)
                        
            QMessageBox.information(self, "Export Complete", 
                                  f"Evidence exported successfully to:\n{ema_path}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting evidence: {str(e)}")

    def on_export_all_evidence(self):
        """Export all evidence as an .ema file"""
        if not os.path.exists(self.evidence_dir):
            QMessageBox.critical(self, "Export Error", "No Evidence folder found to export.")
            return
            
        # Ask user for save location
        ema_path, _ = QFileDialog.getSaveFileName(
            self, "Export all evidence", "", "Evidence Manager Archive (*.ema)"
        )
        
        if not ema_path:
            return
            
        if not ema_path.endswith('.ema'):
            ema_path += '.ema'
        
        try:
            with zipfile.ZipFile(ema_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    'export_type': 'all_evidence',
                    'export_date': datetime.now().isoformat(),
                    'person_count': len(self.person_data)
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # Add all files
                for root, dirs, files in os.walk(self.evidence_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(self.evidence_dir))
                        zipf.write(file_path, arcname)
                        
            QMessageBox.information(self, "Export Complete", 
                                  f"All evidence exported successfully to:\n{ema_path}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting evidence: {str(e)}")

    def on_import_evidence(self):
        """Import evidence from an .ema file"""
        ema_path, _ = QFileDialog.getOpenFileName(
            self, "Import evidence", "", "Evidence Manager Archive (*.ema)"
        )
        
        if not ema_path:
            return
            
        try:
            with zipfile.ZipFile(ema_path, 'r') as zipf:
                # Check if metadata exists
                if 'metadata.json' not in zipf.namelist():
                    QMessageBox.critical(self, "Import Error", "Invalid .ema file: No metadata found.")
                    return
                
                # Read metadata
                metadata_str = zipf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_str)
                export_type = metadata.get('export_type')
                
                if export_type == 'single_person':
                    self.import_single_person(zipf, metadata)
                elif export_type == 'all_evidence':
                    self.import_all_evidence(zipf, metadata)
                else:
                    QMessageBox.critical(self, "Import Error", "Unknown export type in .ema file.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing evidence: {str(e)}")

    def import_single_person(self, zipf, metadata):
        """Import a single person's evidence"""
        person_name = metadata.get('person_name')
        if not person_name:
            QMessageBox.critical(self, "Import Error", "Invalid .ema file: No person name in metadata.")
            return
        
        # Check if person already exists
        if person_name in self.person_data:
            reply = QMessageBox.question(
                self, "Confirm Import", f"Person '{person_name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        try:
            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zipf.extractall(temp_dir)
                
                # Look for the Evidence folder structure
                evidence_source = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path) and item == 'Evidence':
                        evidence_source = item_path
                        break
                
                if not evidence_source:
                    QMessageBox.critical(self, "Import Error", "Invalid .ema file: Could not find Evidence folder.")
                    return
                
                # Find the person's folder inside Evidence
                person_folders = [f for f in os.listdir(evidence_source) 
                                if os.path.isdir(os.path.join(evidence_source, f))]
                
                if len(person_folders) != 1:
                    QMessageBox.critical(self, "Import Error", 
                                       "Invalid .ema file: Could not find person folder in Evidence directory.")
                    return
                
                person_folder = person_folders[0]
                source_folder = os.path.join(evidence_source, person_folder)
                target_folder = os.path.join(self.evidence_dir, person_folder)
                
                # Copy the folder
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                shutil.copytree(source_folder, target_folder)
                
                # Load the person data
                data_file = os.path.join(target_folder, 'person_data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r', encoding='utf-8') as f:
                        self.person_data[person_name] = json.load(f)
                
                QMessageBox.information(self, "Import Complete", 
                                      f"Successfully imported evidence for '{person_name}'")
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing person evidence: {str(e)}")
            return
        
        # Refresh the UI
        self.update_person_list()

    def import_all_evidence(self, zipf, metadata):
        """Import all evidence from an .ema file"""
        reply = QMessageBox.question(
            self, "Confirm Import", "This will import all evidence from the archive. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zipf.extractall(temp_dir)
                
                # Find the Evidence folder
                evidence_source = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path) and item == 'Evidence':
                        evidence_source = item_path
                        break
                
                if not evidence_source:
                    QMessageBox.critical(self, "Import Error", "Invalid .ema file: Could not find Evidence folder.")
                    return
                
                # Copy all person folders
                imported_count = 0
                for person_folder in os.listdir(evidence_source):
                    person_source = os.path.join(evidence_source, person_folder)
                    if os.path.isdir(person_source):
                        person_target = os.path.join(self.evidence_dir, person_folder)
                        
                        # Check if person already exists
                        person_name = person_folder.replace('_', ' ')
                        if person_name in self.person_data:
                            reply = QMessageBox.question(
                                self, "Confirm Import", f"Person '{person_name}' already exists. Overwrite?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            )
                            if reply != QMessageBox.StandardButton.Yes:
                                continue
                        
                        # Copy the folder
                        if os.path.exists(person_target):
                            shutil.rmtree(person_target)
                        shutil.copytree(person_source, person_target)
                        
                        # Load the person data
                        data_file = os.path.join(person_target, 'person_data.json')
                        if os.path.exists(data_file):
                            with open(data_file, 'r', encoding='utf-8') as f:
                                self.person_data[person_name] = json.load(f)
                        
                        imported_count += 1
                
                QMessageBox.information(self, "Import Complete", 
                                      f"Successfully imported {imported_count} people's evidence")
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing all evidence: {str(e)}")
            return
        
        # Refresh the UI
        self.update_person_list()

    def on_delete_person(self, person_name):
        """Delete a person and all their evidence"""
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete person '{person_name}' and all their evidence?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if person_name in self.person_data:
                del self.person_data[person_name]
            folder_name = person_name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir)
            self.update_person_list()
            self.current_person = None
            
            # Reset right panel
            for child in self.right_panel.children():
                if isinstance(child, QWidget):
                    child.deleteLater()
            
            # Remove existing layout if any
            if self.right_panel.layout():
                QWidget().setLayout(self.right_panel.layout())
            
            layout = QVBoxLayout(self.right_panel)
            welcome_text = QLabel("Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.")
            welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            welcome_text.setFont(QFont("Arial", 12))
            layout.addWidget(welcome_text)

def main():
    app = QApplication(sys.argv)
    window = EvidenceManagerPyQt()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 