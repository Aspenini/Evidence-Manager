#!/usr/bin/env python3
"""
Evidence Manager - Single File Version
A self-contained evidence management app with built-in dependency check and GUI.
Just run this file: python evidence_manager.py
"""

import sys
import os
import subprocess
import importlib.util
import json
import shutil
import zipfile
import tempfile
import threading
import requests
import wx

__version__ = "1.1.1"

GITHUB_REPO = "Aspenini/Evidence-Manager"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Dependency check and install prompt
REQUIRED = [
    ("wx", "wxPython"),
    ("PIL", "Pillow"),
]

def check_and_install():
    missing = []
    for mod, pkg in REQUIRED:
        if importlib.util.find_spec(mod) is None:
            print(f"❌ {pkg} is not installed.")
            missing.append(pkg)
        else:
            print(f"✅ {pkg} is available.")
    if missing:
        print("\nMissing dependencies detected:", ", ".join(missing))
        resp = input("Would you like to install them now? (y/n): ").strip().lower()
        if resp in ("y", "yes"):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
                print("\nDependencies installed! Please re-run the program.")
            except Exception as e:
                print(f"❌ Failed to install dependencies: {e}")
            sys.exit(0)
        else:
            print("Please install the required dependencies and re-run this script.")
            sys.exit(1)

check_and_install()

# --- Auto-update logic ---
def check_for_update(parent=None):
    try:
        resp = requests.get(GITHUB_API_RELEASES, timeout=5)
        if resp.status_code != 200:
            return
        data = resp.json()
        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            return
        if version_tuple(latest_tag) > version_tuple(__version__):
            if parent:
                dlg = wx.MessageDialog(parent, f"A new version (v{latest_tag}) is available. Do you want to update?", "Update Available", wx.YES_NO | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    asset = next((a for a in data.get("assets", []) if a["name"].endswith(".zip")), None)
                    if asset:
                        download_and_replace_exe(asset["browser_download_url"], parent)
                dlg.Destroy()
    except Exception as e:
        pass  # Silently ignore update errors

def version_tuple(v):
    return tuple(map(int, (v.split("."))))

def download_and_replace_exe(zip_url, parent):
    try:
        # Download zip
        tmp_zip = os.path.join(tempfile.gettempdir(), "evidence_manager_update.zip")
        r = requests.get(zip_url, stream=True, timeout=30)
        with open(tmp_zip, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        # Extract zip
        with zipfile.ZipFile(tmp_zip, 'r') as zipf:
            extract_dir = os.path.join(tempfile.gettempdir(), "evidence_manager_update")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            zipf.extractall(extract_dir)
            # Find exe inside any folder
            exe_path = None
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith('.exe'):
                        exe_path = os.path.join(root, file)
                        break
                if exe_path:
                    break
            if not exe_path:
                wx.MessageBox("No .exe found in update package.", "Update Error", wx.OK | wx.ICON_ERROR)
                return
            # Prepare to replace
            current_exe = sys.executable
            backup_exe = current_exe + ".bak"
            wx.MessageBox("The app will now close to complete the update. Please re-launch after a few seconds.", "Update", wx.OK | wx.ICON_INFORMATION)
            # Move current exe to .bak
            try:
                if os.path.exists(backup_exe):
                    os.remove(backup_exe)
                os.rename(current_exe, backup_exe)
            except Exception as e:
                wx.MessageBox(f"Failed to backup old exe: {e}", "Update Error", wx.OK | wx.ICON_ERROR)
                return
            # Move new exe in place
            try:
                shutil.copy2(exe_path, current_exe)
            except Exception as e:
                wx.MessageBox(f"Failed to replace exe: {e}", "Update Error", wx.OK | wx.ICON_ERROR)
                return
            # Exit app
            wx.GetApp().Exit()
    except Exception as e:
        wx.MessageBox(f"Update failed: {e}", "Update Error", wx.OK | wx.ICON_ERROR)

# --- End auto-update logic ---

# Now import dependencies
import wx.adv
from datetime import datetime
from PIL import Image

class EvidenceManager(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Evidence Manager", size=(1200, 800))
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
            bg_color = wx.Colour(30, 30, 30)
            text_color = wx.Colour(230, 230, 230)
            panel_color = wx.Colour(45, 45, 45)
            list_bg_color = wx.Colour(40, 40, 40)
            button_bg = wx.Colour(50, 50, 50)
            button_fg = wx.Colour(230, 230, 230)
        else:
            # Light mode colors
            bg_color = wx.Colour(240, 240, 240)
            text_color = wx.Colour(0, 0, 0)
            panel_color = wx.Colour(255, 255, 255)
            list_bg_color = wx.Colour(255, 255, 255)
            button_bg = wx.Colour(240, 240, 240)
            button_fg = wx.Colour(0, 0, 0)

        self.SetBackgroundColour(bg_color)
        for child in self.GetChildren():
            self._apply_theme_recursive(child, bg_color, text_color, panel_color, list_bg_color, button_bg, button_fg)
        self.Refresh()

    def _apply_theme_recursive(self, widget, bg_color, text_color, panel_color, list_bg_color, button_bg, button_fg):
        if isinstance(widget, wx.Panel):
            widget.SetBackgroundColour(panel_color)
        elif isinstance(widget, wx.ListCtrl):
            widget.SetBackgroundColour(list_bg_color)
            widget.SetForegroundColour(text_color)
            # Set column and item colors for ListCtrl
            for col in range(widget.GetColumnCount()):
                widget.SetColumn(col, widget.GetColumn(col))  # force refresh
            for i in range(widget.GetItemCount()):
                widget.SetItemBackgroundColour(i, list_bg_color)
                widget.SetItemTextColour(i, text_color)
        elif isinstance(widget, wx.ListBox):
            widget.SetBackgroundColour(list_bg_color)
            widget.SetForegroundColour(text_color)
        elif isinstance(widget, wx.Notebook):
            widget.SetBackgroundColour(panel_color)
            widget.SetForegroundColour(text_color)
            for page in range(widget.GetPageCount()):
                widget.GetPage(page).SetBackgroundColour(panel_color)
        elif isinstance(widget, wx.Button):
            widget.SetBackgroundColour(button_bg)
            widget.SetForegroundColour(button_fg)
        elif isinstance(widget, wx.StaticText):
            widget.SetForegroundColour(text_color)
        elif isinstance(widget, wx.TextCtrl):
            widget.SetBackgroundColour(panel_color)
            widget.SetForegroundColour(text_color)
        for child in widget.GetChildren():
            self._apply_theme_recursive(child, bg_color, text_color, panel_color, list_bg_color, button_bg, button_fg)

    def toggle_dark_mode(self, event):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.apply_theme()
        # Update button text
        if hasattr(self, 'dark_mode_btn'):
            self.dark_mode_btn.SetLabel("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")
        self.Refresh()
        
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
                        except:
                            self.person_data[person_name] = {
                                'name': person_name,
                                'created': datetime.now().isoformat(),
                                'info': {},
                                'images': [],
                                'audio': []
                            }
                    else:
                        self.person_data[person_name] = {
                            'name': person_name,
                            'created': datetime.now().isoformat(),
                            'info': {},
                            'images': [],
                            'audio': []
                        }
    def init_ui(self):
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.Panel(main_panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        header_panel = wx.Panel(left_panel)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(header_panel, label="People", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Add buttons panel
        buttons_panel = wx.Panel(header_panel)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_btn = wx.Button(buttons_panel, label="+ Add Person", size=(100, 30))
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_person)
        
        import_btn = wx.Button(buttons_panel, label="Import .ema", size=(100, 30))
        import_btn.Bind(wx.EVT_BUTTON, self.on_import_evidence)
        
        export_all_btn = wx.Button(buttons_panel, label="Export All", size=(100, 30))
        export_all_btn.Bind(wx.EVT_BUTTON, self.on_export_all_evidence)
        
        # Dark mode toggle button
        dark_mode_btn = wx.Button(buttons_panel, label="🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode", size=(100, 30))
        dark_mode_btn.Bind(wx.EVT_BUTTON, self.toggle_dark_mode)
        self.dark_mode_btn = dark_mode_btn  # Store reference for updating text
        
        buttons_sizer.Add(add_btn, 0, wx.ALL, 2)
        buttons_sizer.Add(import_btn, 0, wx.ALL, 2)
        buttons_sizer.Add(export_all_btn, 0, wx.ALL, 2)
        buttons_sizer.Add(dark_mode_btn, 0, wx.ALL, 2)
        buttons_panel.SetSizer(buttons_sizer)
        header_sizer.Add(title, 1, wx.ALL | wx.EXPAND, 5)
        header_sizer.Add(buttons_panel, 0, wx.ALL, 5)
        header_panel.SetSizer(header_sizer)
        self.person_list = wx.ListBox(left_panel, style=wx.LB_SINGLE)
        self.person_list.Bind(wx.EVT_LISTBOX, self.on_person_selected)
        left_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.person_list, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)
        self.right_panel = wx.Panel(main_panel)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        welcome_text = wx.StaticText(self.right_panel, 
                                   label="Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.",
                                   style=wx.ALIGN_CENTER)
        welcome_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.right_sizer.Add(welcome_text, 1, wx.ALL | wx.EXPAND, 20)
        self.right_panel.SetSizer(self.right_sizer)
        main_sizer.Add(left_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.right_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_panel.SetSizer(main_sizer)
        self.update_person_list()
        self.Center()
        self.apply_theme()
    def update_person_list(self):
        self.person_list.Clear()
        for person_name in sorted(self.person_data.keys()):
            self.person_list.Append(person_name)
    def on_add_person(self, event):
        dialog = wx.TextEntryDialog(self, "Enter person's name:", "Add Person")
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue().strip()
            if name:
                folder_name = name.replace(' ', '_')
                person_dir = os.path.join(self.evidence_dir, folder_name)
                if not os.path.exists(person_dir):
                    os.makedirs(person_dir)
                    os.makedirs(os.path.join(person_dir, 'images'))
                    os.makedirs(os.path.join(person_dir, 'audio'))
                self.person_data[name] = {
                    'name': name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': [],
                    'audio': []
                }
                self.save_person_data(name)
                self.update_person_list()
        dialog.Destroy()
    def on_person_selected(self, event):
        selection = self.person_list.GetSelection()
        if selection != wx.NOT_FOUND:
            person_name = self.person_list.GetString(selection)
            self.current_person = person_name
            self.show_person_details(person_name)
    def show_person_details(self, person_name):
        self.right_panel.DestroyChildren()
        self.right_sizer.Clear()
        header_panel = wx.Panel(self.right_panel)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(header_panel, label=f"Evidence for: {person_name}")
        title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Add export button
        export_btn = wx.Button(header_panel, label="Export Evidence", size=(120, 30))
        export_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_export_evidence(person_name))
        
        delete_btn = wx.Button(header_panel, label="Delete Person", size=(100, 30))
        delete_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_delete_person(person_name))
        header_sizer.Add(title, 1, wx.ALL | wx.EXPAND, 5)
        header_sizer.Add(export_btn, 0, wx.ALL, 5)
        header_sizer.Add(delete_btn, 0, wx.ALL, 5)
        header_panel.SetSizer(header_sizer)
        notebook = wx.Notebook(self.right_panel)
        info_panel = self.create_info_panel(notebook, person_name)
        notebook.AddPage(info_panel, "Information")
        images_panel = self.create_images_panel(notebook, person_name)
        notebook.AddPage(images_panel, "Images")
        
        # Audio tab
        audio_panel = self.create_audio_panel(notebook, person_name)
        notebook.AddPage(audio_panel, "Audio")
        self.right_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.right_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.right_panel.Layout()
    def create_info_panel(self, parent, person_name):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        add_panel = wx.Panel(panel)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        info_type_label = wx.StaticText(add_panel, label="Info Type:")
        self.info_type_ctrl = wx.TextCtrl(add_panel, value="", size=(150, 25))
        info_value_label = wx.StaticText(add_panel, label="Value:")
        self.info_value_ctrl = wx.TextCtrl(add_panel, value="", size=(200, 25))
        add_info_btn = wx.Button(add_panel, label="Add Info", size=(80, 25))
        add_info_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_add_info(person_name))
        add_sizer.Add(info_type_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        add_sizer.Add(self.info_type_ctrl, 0, wx.ALL, 5)
        add_sizer.Add(info_value_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        add_sizer.Add(self.info_value_ctrl, 0, wx.ALL, 5)
        add_sizer.Add(add_info_btn, 0, wx.ALL, 5)
        add_panel.SetSizer(add_sizer)
        self.info_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_EDIT_LABELS)
        self.info_list.InsertColumn(0, "Type", width=150)
        self.info_list.InsertColumn(1, "Value", width=300)
        self.info_list.InsertColumn(2, "Actions", width=100)
        self.info_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, lambda evt: self.on_info_right_click(evt, person_name))
        sizer.Add(add_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.info_list, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.load_info_list(person_name)
        if self.dark_mode:
            panel.SetBackgroundColour(wx.Colour(45, 45, 45))
            add_panel.SetBackgroundColour(wx.Colour(45, 45, 45))
            self.info_type_ctrl.SetBackgroundColour(wx.Colour(45, 45, 45))
            self.info_type_ctrl.SetForegroundColour(wx.Colour(230, 230, 230))
            self.info_value_ctrl.SetBackgroundColour(wx.Colour(45, 45, 45))
            self.info_value_ctrl.SetForegroundColour(wx.Colour(230, 230, 230))
        return panel

    def create_images_panel(self, parent, person_name):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        add_panel = wx.Panel(panel)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_image_btn = wx.Button(add_panel, label="Add Image", size=(100, 30))
        add_image_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_add_image(person_name))
        add_sizer.Add(add_image_btn, 0, wx.ALL, 5)
        add_panel.SetSizer(add_sizer)
        self.images_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.images_list.InsertColumn(0, "Display Name", width=200)
        self.images_list.InsertColumn(1, "Filename", width=200)
        self.images_list.InsertColumn(2, "Actions", width=150)
        self.images_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, lambda evt: self.on_image_right_click(evt, person_name))
        sizer.Add(add_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.images_list, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.load_images_list(person_name)
        if self.dark_mode:
            panel.SetBackgroundColour(wx.Colour(45, 45, 45))
            add_panel.SetBackgroundColour(wx.Colour(45, 45, 45))
        return panel

    def create_audio_panel(self, parent, person_name):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        add_panel = wx.Panel(panel)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_audio_btn = wx.Button(add_panel, label="Add Audio", size=(100, 30))
        add_audio_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_add_audio(person_name))
        add_sizer.Add(add_audio_btn, 0, wx.ALL, 5)
        add_panel.SetSizer(add_sizer)
        self.audio_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.audio_list.InsertColumn(0, "Display Name", width=200)
        self.audio_list.InsertColumn(1, "Filename", width=200)
        self.audio_list.InsertColumn(2, "Actions", width=150)
        self.audio_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, lambda evt: self.on_audio_right_click(evt, person_name))
        sizer.Add(add_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.audio_list, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.load_audio_list(person_name)
        if self.dark_mode:
            panel.SetBackgroundColour(wx.Colour(45, 45, 45))
            add_panel.SetBackgroundColour(wx.Colour(45, 45, 45))
        return panel
        
    def on_add_info(self, person_name):
        info_type = self.info_type_ctrl.GetValue().strip()
        info_value = self.info_value_ctrl.GetValue().strip()
        if info_type and info_value:
            if person_name not in self.person_data:
                self.person_data[person_name] = {
                    'name': person_name,
                    'created': datetime.now().isoformat(),
                    'info': {},
                    'images': []
                }
            if info_type not in self.person_data[person_name]['info']:
                self.person_data[person_name]['info'][info_type] = []
            self.person_data[person_name]['info'][info_type].append(info_value)
            self.save_person_data(person_name)
            self.load_info_list(person_name)
            self.info_type_ctrl.SetValue("")
            self.info_value_ctrl.SetValue("")
    def load_info_list(self, person_name):
        self.info_list.DeleteAllItems()
        if person_name in self.person_data:
            row = 0
            for info_type, values in self.person_data[person_name]['info'].items():
                for value in values:
                    self.info_list.InsertItem(row, info_type)
                    self.info_list.SetItem(row, 1, value)
                    self.info_list.SetItem(row, 2, "Delete")
                    if self.dark_mode:
                        self.info_list.SetItemBackgroundColour(row, wx.Colour(40, 40, 40))
                        self.info_list.SetItemTextColour(row, wx.Colour(230, 230, 230))
                    row += 1
        if self.dark_mode:
            self.info_list.SetBackgroundColour(wx.Colour(40, 40, 40))
            self.info_list.SetForegroundColour(wx.Colour(230, 230, 230))
    def on_info_right_click(self, event, person_name):
        item = event.GetIndex()
        if item != wx.NOT_FOUND:
            info_type = self.info_list.GetItem(item, 0).GetText()
            info_value = self.info_list.GetItem(item, 1).GetText()
            menu = wx.Menu()
            delete_item = menu.Append(wx.ID_ANY, "Delete")
            edit_item = menu.Append(wx.ID_ANY, "Edit")
            self.Bind(wx.EVT_MENU, lambda evt: self.delete_info_item(person_name, info_type, info_value), delete_item)
            self.Bind(wx.EVT_MENU, lambda evt: self.edit_info_item(person_name, info_type, info_value, item), edit_item)
            self.PopupMenu(menu)
            menu.Destroy()
    def delete_info_item(self, person_name, info_type, info_value):
        if person_name in self.person_data and info_type in self.person_data[person_name]['info']:
            if info_value in self.person_data[person_name]['info'][info_type]:
                self.person_data[person_name]['info'][info_type].remove(info_value)
                if not self.person_data[person_name]['info'][info_type]:
                    del self.person_data[person_name]['info'][info_type]
                self.save_person_data(person_name)
                self.load_info_list(person_name)
    def edit_info_item(self, person_name, info_type, info_value, item):
        dialog = wx.TextEntryDialog(self, f"Edit {info_type}:", "Edit Information", info_value)
        if dialog.ShowModal() == wx.ID_OK:
            new_value = dialog.GetValue().strip()
            if new_value and new_value != info_value:
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
                        'audio': []
                    }
                if info_type not in self.person_data[person_name]['info']:
                    self.person_data[person_name]['info'][info_type] = []
                
                # Add the new value
                self.person_data[person_name]['info'][info_type].append(new_value)
                self.save_person_data(person_name)
                self.load_info_list(person_name)
        dialog.Destroy()
    def on_add_image(self, person_name):
        with wx.FileDialog(self, "Select image file", wildcard="Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            filepath = fileDialog.GetPath()
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
                    'images': []
                }
            if filename not in self.person_data[person_name]['images']:
                # Store as dict with display name and filename
                image_data = {
                    'display_name': os.path.splitext(filename)[0],  # filename without extension
                    'filename': filename
                }
                self.person_data[person_name]['images'].append(image_data)
                self.save_person_data(person_name)
                self.load_images_list(person_name)
    def load_images_list(self, person_name):
        self.images_list.DeleteAllItems()
        if person_name in self.person_data:
            row = 0
            for image_data in self.person_data[person_name]['images']:
                if isinstance(image_data, dict):
                    display_name = image_data.get('display_name', '')
                    filename = image_data.get('filename', '')
                else:
                    # Handle old format (just filename string)
                    filename = image_data
                    display_name = os.path.splitext(filename)[0]
                self.images_list.InsertItem(row, display_name)
                self.images_list.SetItem(row, 1, filename)
                self.images_list.SetItem(row, 2, "Open | Rename | Delete")
                if self.dark_mode:
                    self.images_list.SetItemBackgroundColour(row, wx.Colour(40, 40, 40))
                    self.images_list.SetItemTextColour(row, wx.Colour(230, 230, 230))
                row += 1
        if self.dark_mode:
            self.images_list.SetBackgroundColour(wx.Colour(40, 40, 40))
            self.images_list.SetForegroundColour(wx.Colour(230, 230, 230))
    def on_image_right_click(self, event, person_name):
        item = event.GetIndex()
        if item != wx.NOT_FOUND:
            display_name = self.images_list.GetItem(item, 0).GetText()
            filename = self.images_list.GetItem(item, 1).GetText()
            
            menu = wx.Menu()
            open_item = menu.Append(wx.ID_ANY, "Open Image")
            rename_item = menu.Append(wx.ID_ANY, "Rename")
            delete_item = menu.Append(wx.ID_ANY, "Delete")
            
            self.Bind(wx.EVT_MENU, lambda evt: self.open_image_file(person_name, filename), open_item)
            self.Bind(wx.EVT_MENU, lambda evt: self.rename_image(person_name, display_name, filename, item), rename_item)
            self.Bind(wx.EVT_MENU, lambda evt: self.delete_image(person_name, filename), delete_item)
            
            self.PopupMenu(menu)
            menu.Destroy()
    def open_image_file(self, person_name, filename):
        folder_name = person_name.replace(' ', '_')
        image_path = os.path.join(self.evidence_dir, folder_name, 'images', filename)
        try:
            os.startfile(image_path)
        except:
            wx.MessageBox(f"Could not open image: {image_path}", "Error", wx.OK | wx.ICON_ERROR)
            
    def rename_image(self, person_name, current_display_name, filename, item):
        dialog = wx.TextEntryDialog(self, "Enter new display name:", "Rename Image", current_display_name)
        if dialog.ShowModal() == wx.ID_OK:
            new_display_name = dialog.GetValue().strip()
            if new_display_name and new_display_name != current_display_name:
                # Update the image data
                for image_data in self.person_data[person_name]['images']:
                    if isinstance(image_data, dict) and image_data.get('filename') == filename:
                        image_data['display_name'] = new_display_name
                        break
                    elif image_data == filename:  # Handle old format
                        # Convert to new format
                        idx = self.person_data[person_name]['images'].index(image_data)
                        self.person_data[person_name]['images'][idx] = {
                            'display_name': new_display_name,
                            'filename': filename
                        }
                        break
                self.save_person_data(person_name)
                self.load_images_list(person_name)
        dialog.Destroy()
    def delete_image(self, person_name, filename):
        if wx.MessageBox(f"Delete image '{filename}'?", "Confirm Delete", 
                        wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
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
            self.load_images_list(person_name)
            
    def on_add_audio(self, person_name):
        with wx.FileDialog(self, "Select audio file", wildcard="Audio files (*.mp3;*.wav;*.m4a;*.aac;*.ogg)|*.mp3;*.wav;*.m4a;*.aac;*.ogg",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            filepath = fileDialog.GetPath()
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
                    'audio': []
                }
            # Store as dict with display name and filename
            audio_data = {
                'display_name': os.path.splitext(filename)[0],  # filename without extension
                'filename': filename
            }
            self.person_data[person_name]['audio'].append(audio_data)
            self.save_person_data(person_name)
            self.load_audio_list(person_name)
            
    def load_audio_list(self, person_name):
        self.audio_list.DeleteAllItems()
        if person_name in self.person_data:
            row = 0
            for audio_data in self.person_data[person_name]['audio']:
                if isinstance(audio_data, dict):
                    display_name = audio_data.get('display_name', '')
                    filename = audio_data.get('filename', '')
                else:
                    # Handle old format (just filename string)
                    filename = audio_data
                    display_name = os.path.splitext(filename)[0]
                self.audio_list.InsertItem(row, display_name)
                self.audio_list.SetItem(row, 1, filename)
                self.audio_list.SetItem(row, 2, "Play | Rename | Delete")
                if self.dark_mode:
                    self.audio_list.SetItemBackgroundColour(row, wx.Colour(40, 40, 40))
                    self.audio_list.SetItemTextColour(row, wx.Colour(230, 230, 230))
                row += 1
        if self.dark_mode:
            self.audio_list.SetBackgroundColour(wx.Colour(40, 40, 40))
            self.audio_list.SetForegroundColour(wx.Colour(230, 230, 230))
                
    def on_audio_right_click(self, event, person_name):
        item = event.GetIndex()
        if item != wx.NOT_FOUND:
            display_name = self.audio_list.GetItem(item, 0).GetText()
            filename = self.audio_list.GetItem(item, 1).GetText()
            
            menu = wx.Menu()
            play_item = menu.Append(wx.ID_ANY, "Play Audio")
            rename_item = menu.Append(wx.ID_ANY, "Rename")
            delete_item = menu.Append(wx.ID_ANY, "Delete")
            
            self.Bind(wx.EVT_MENU, lambda evt: self.play_audio_file(person_name, filename), play_item)
            self.Bind(wx.EVT_MENU, lambda evt: self.rename_audio(person_name, display_name, filename, item), rename_item)
            self.Bind(wx.EVT_MENU, lambda evt: self.delete_audio(person_name, filename), delete_item)
            
            self.PopupMenu(menu)
            menu.Destroy()
            
    def play_audio_file(self, person_name, filename):
        folder_name = person_name.replace(' ', '_')
        audio_path = os.path.join(self.evidence_dir, folder_name, 'audio', filename)
        try:
            os.startfile(audio_path)
        except:
            wx.MessageBox(f"Could not play audio: {audio_path}", "Error", wx.OK | wx.ICON_ERROR)
            
    def rename_audio(self, person_name, current_display_name, filename, item):
        dialog = wx.TextEntryDialog(self, "Enter new display name:", "Rename Audio", current_display_name)
        if dialog.ShowModal() == wx.ID_OK:
            new_display_name = dialog.GetValue().strip()
            if new_display_name and new_display_name != current_display_name:
                # Update the audio data
                for audio_data in self.person_data[person_name]['audio']:
                    if isinstance(audio_data, dict) and audio_data.get('filename') == filename:
                        audio_data['display_name'] = new_display_name
                        break
                    elif audio_data == filename:  # Handle old format
                        # Convert to new format
                        idx = self.person_data[person_name]['audio'].index(audio_data)
                        self.person_data[person_name]['audio'][idx] = {
                            'display_name': new_display_name,
                            'filename': filename
                        }
                        break
                self.save_person_data(person_name)
                self.load_audio_list(person_name)
        dialog.Destroy()
        
    def delete_audio(self, person_name, filename):
        if wx.MessageBox(f"Delete audio '{filename}'?", "Confirm Delete", 
                        wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
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
            self.load_audio_list(person_name)
            
    def on_export_evidence(self, person_name):
        """Export person's evidence folder as an .ema file"""
        folder_name = person_name.replace(' ', '_')
        person_dir = os.path.join(self.evidence_dir, folder_name)
        
        if not os.path.exists(person_dir):
            wx.MessageBox(f"No evidence folder found for {person_name}", "Export Error", wx.OK | wx.ICON_ERROR)
            return
            
        # Ask user for save location
        with wx.FileDialog(self, f"Export evidence for {person_name}", 
                          wildcard="Evidence Manager Archive (*.ema)|*.ema",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            ema_path = fileDialog.GetPath()
            if not ema_path.endswith('.ema'):
                ema_path += '.ema'
            
            try:
                with zipfile.ZipFile(ema_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add metadata to identify this as a single person export
                    metadata = {
                        'export_type': 'single_person',
                        'person_name': person_name,
                        'export_date': datetime.now().isoformat()
                    }
                    zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                    
                    # Create the same structure as all evidence export but with just one person
                    # Walk through the person's directory and add all files with Evidence/Person_Name/ prefix
                    for root, dirs, files in os.walk(person_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path from the person directory
                            relative_path = os.path.relpath(file_path, person_dir)
                            # Create the full archive path with Evidence/Person_Name/ prefix
                            arcname = os.path.join('Evidence', folder_name, relative_path)
                            zipf.write(file_path, arcname)
                            
                wx.MessageBox(f"Evidence exported successfully to:\n{ema_path}", 
                            "Export Complete", wx.OK | wx.ICON_INFORMATION)
                            
            except Exception as e:
                wx.MessageBox(f"Error exporting evidence: {str(e)}", 
                            "Export Error", wx.OK | wx.ICON_ERROR)
    
    def on_export_all_evidence(self, event):
        """Export entire Evidence folder as an .ema file"""
        if not os.path.exists(self.evidence_dir):
            wx.MessageBox("No Evidence folder found to export.", "Export Error", wx.OK | wx.ICON_ERROR)
            return
            
        # Ask user for save location
        with wx.FileDialog(self, "Export all evidence", 
                          wildcard="Evidence Manager Archive (*.ema)|*.ema",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            ema_path = fileDialog.GetPath()
            if not ema_path.endswith('.ema'):
                ema_path += '.ema'
            
            try:
                with zipfile.ZipFile(ema_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add metadata to identify this as an all evidence export
                    metadata = {
                        'export_type': 'all_evidence',
                        'export_date': datetime.now().isoformat(),
                        'person_count': len(self.person_data)
                    }
                    zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                    
                    # Walk through the entire Evidence directory and add all files
                    for root, dirs, files in os.walk(self.evidence_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path for the zip
                            arcname = os.path.relpath(file_path, os.path.dirname(self.evidence_dir))
                            zipf.write(file_path, arcname)
                            
                wx.MessageBox(f"All evidence exported successfully to:\n{ema_path}", 
                            "Export Complete", wx.OK | wx.ICON_INFORMATION)
                            
            except Exception as e:
                wx.MessageBox(f"Error exporting evidence: {str(e)}", 
                            "Export Error", wx.OK | wx.ICON_ERROR)
            
    def on_import_evidence(self, event):
        """Import evidence from an .ema file"""
        with wx.FileDialog(self, "Import evidence", 
                          wildcard="Evidence Manager Archive (*.ema)|*.ema",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            ema_path = fileDialog.GetPath()
            
            try:
                with zipfile.ZipFile(ema_path, 'r') as zipf:
                    # Check if metadata exists
                    if 'metadata.json' not in zipf.namelist():
                        wx.MessageBox("Invalid .ema file: No metadata found.", "Import Error", wx.OK | wx.ICON_ERROR)
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
                        wx.MessageBox("Unknown export type in .ema file.", "Import Error", wx.OK | wx.ICON_ERROR)
                        
            except Exception as e:
                wx.MessageBox(f"Error importing evidence: {str(e)}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def import_single_person(self, zipf, metadata):
        """Import a single person's evidence"""
        person_name = metadata.get('person_name')
        if not person_name:
            wx.MessageBox("Invalid .ema file: No person name in metadata.", "Import Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Check if person already exists
        if person_name in self.person_data:
            result = wx.MessageBox(f"Person '{person_name}' already exists. Overwrite?", 
                                 "Confirm Import", wx.YES_NO | wx.ICON_QUESTION)
            if result != wx.YES:
                return
        
        try:
            # Extract to temporary directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                zipf.extractall(temp_dir)
                
                # Look for the Evidence folder structure (same as all evidence import)
                evidence_source = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path) and item == 'Evidence':
                        evidence_source = item_path
                        break
                
                if not evidence_source:
                    wx.MessageBox("Invalid .ema file: Could not find Evidence folder.", "Import Error", wx.OK | wx.ICON_ERROR)
                    return
                
                # Find the person's folder inside Evidence
                person_folders = [f for f in os.listdir(evidence_source) if os.path.isdir(os.path.join(evidence_source, f))]
                
                if len(person_folders) != 1:
                    wx.MessageBox("Invalid .ema file: Could not find person folder in Evidence directory.", "Import Error", wx.OK | wx.ICON_ERROR)
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
                
                wx.MessageBox(f"Successfully imported evidence for '{person_name}'", "Import Complete", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            wx.MessageBox(f"Error importing person evidence: {str(e)}", "Import Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Refresh the UI
        self.update_person_list()
    
    def import_all_evidence(self, zipf, metadata):
        """Import all evidence from an .ema file"""
        result = wx.MessageBox("This will import all evidence from the archive. Continue?", 
                             "Confirm Import", wx.YES_NO | wx.ICON_QUESTION)
        if result != wx.YES:
            return
        
        try:
            # Extract to temporary directory
            import tempfile
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
                    wx.MessageBox("Invalid .ema file: Could not find Evidence folder.", "Import Error", wx.OK | wx.ICON_ERROR)
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
                            result = wx.MessageBox(f"Person '{person_name}' already exists. Overwrite?", 
                                                 "Confirm Import", wx.YES_NO | wx.ICON_QUESTION)
                            if result != wx.YES:
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
                
                wx.MessageBox(f"Successfully imported {imported_count} people's evidence", "Import Complete", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            wx.MessageBox(f"Error importing all evidence: {str(e)}", "Import Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Refresh the UI
        self.update_person_list()
    
    def on_delete_person(self, person_name):
        if wx.MessageBox(f"Delete person '{person_name}' and all their evidence?", 
                        "Confirm Delete", wx.YES_NO | wx.ICON_WARNING) == wx.YES:
            if person_name in self.person_data:
                del self.person_data[person_name]
            folder_name = person_name.replace(' ', '_')
            person_dir = os.path.join(self.evidence_dir, folder_name)
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir)
            self.update_person_list()
            self.current_person = None
            self.right_panel.DestroyChildren()
            self.right_sizer.Clear()
            welcome_text = wx.StaticText(self.right_panel, 
                                       label="Welcome to Evidence Manager\n\nSelect a person from the list to view and manage their evidence.",
                                       style=wx.ALIGN_CENTER)
            welcome_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            self.right_sizer.Add(welcome_text, 1, wx.ALL | wx.EXPAND, 20)
            self.right_panel.Layout()
    def save_person_data(self, person_name):
        folder_name = person_name.replace(' ', '_')
        person_dir = os.path.join(self.evidence_dir, folder_name)
        data_file = os.path.join(person_dir, 'person_data.json')
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.person_data[person_name], f, indent=2, ensure_ascii=False)

def main():
    app = wx.App()
    frame = EvidenceManager()
    # Only check for update if running as exe
    if getattr(sys, 'frozen', False):
        threading.Thread(target=check_for_update, args=(frame,), daemon=True).start()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main() 