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

# Now import dependencies
import wx
import wx.adv
import json
import shutil
import zipfile
from datetime import datetime
from PIL import Image

class EvidenceManager(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Evidence Manager", size=(1200, 800))
        self.evidence_dir = "Evidence"
        self.current_person = None
        self.person_data = {}
        self.ensure_evidence_directory()
        self.load_persons()
        self.init_ui()
        
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
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
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
        
        export_all_btn = wx.Button(buttons_panel, label="Export All", size=(100, 30))
        export_all_btn.Bind(wx.EVT_BUTTON, self.on_export_all_evidence)
        
        buttons_sizer.Add(add_btn, 0, wx.ALL, 2)
        buttons_sizer.Add(export_all_btn, 0, wx.ALL, 2)
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
        return panel
    def create_images_panel(self, parent, person_name):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add image section
        add_panel = wx.Panel(panel)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_image_btn = wx.Button(add_panel, label="Add Image", size=(100, 30))
        add_image_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_add_image(person_name))
        add_sizer.Add(add_image_btn, 0, wx.ALL, 5)
        add_panel.SetSizer(add_sizer)
        
        # Images list
        self.images_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.images_list.InsertColumn(0, "Display Name", width=200)
        self.images_list.InsertColumn(1, "Filename", width=200)
        self.images_list.InsertColumn(2, "Actions", width=150)
        
        # Bind events
        self.images_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, lambda evt: self.on_image_right_click(evt, person_name))
        
        sizer.Add(add_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.images_list, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Load existing images
        self.load_images_list(person_name)
        
        return panel
        
    def create_audio_panel(self, parent, person_name):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add audio section
        add_panel = wx.Panel(panel)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_audio_btn = wx.Button(add_panel, label="Add Audio", size=(100, 30))
        add_audio_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_add_audio(person_name))
        add_sizer.Add(add_audio_btn, 0, wx.ALL, 5)
        add_panel.SetSizer(add_sizer)
        
        # Audio list
        self.audio_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.audio_list.InsertColumn(0, "Display Name", width=200)
        self.audio_list.InsertColumn(1, "Filename", width=200)
        self.audio_list.InsertColumn(2, "Actions", width=150)
        
        # Bind events
        self.audio_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, lambda evt: self.on_audio_right_click(evt, person_name))
        
        sizer.Add(add_panel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.audio_list, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Load existing audio
        self.load_audio_list(person_name)
        
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
                    row += 1
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
                self.delete_info_item(person_name, info_type, info_value)
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
                row += 1
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
                row += 1
                
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
        """Export person's evidence folder as a zip file"""
        folder_name = person_name.replace(' ', '_')
        person_dir = os.path.join(self.evidence_dir, folder_name)
        
        if not os.path.exists(person_dir):
            wx.MessageBox(f"No evidence folder found for {person_name}", "Export Error", wx.OK | wx.ICON_ERROR)
            return
            
        # Ask user for save location
        with wx.FileDialog(self, f"Export evidence for {person_name}", 
                          wildcard="ZIP files (*.zip)|*.zip",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            zip_path = fileDialog.GetPath()
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Walk through the person's directory and add all files
                    for root, dirs, files in os.walk(person_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path for the zip
                            arcname = os.path.relpath(file_path, person_dir)
                            zipf.write(file_path, arcname)
                            
                wx.MessageBox(f"Evidence exported successfully to:\n{zip_path}", 
                            "Export Complete", wx.OK | wx.ICON_INFORMATION)
                            
            except Exception as e:
                wx.MessageBox(f"Error exporting evidence: {str(e)}", 
                            "Export Error", wx.OK | wx.ICON_ERROR)
    
    def on_export_all_evidence(self, event):
        """Export entire Evidence folder as a zip file"""
        if not os.path.exists(self.evidence_dir):
            wx.MessageBox("No Evidence folder found to export.", "Export Error", wx.OK | wx.ICON_ERROR)
            return
            
        # Ask user for save location
        with wx.FileDialog(self, "Export all evidence", 
                          wildcard="ZIP files (*.zip)|*.zip",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            zip_path = fileDialog.GetPath()
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Walk through the entire Evidence directory and add all files
                    for root, dirs, files in os.walk(self.evidence_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path for the zip
                            arcname = os.path.relpath(file_path, os.path.dirname(self.evidence_dir))
                            zipf.write(file_path, arcname)
                            
                wx.MessageBox(f"All evidence exported successfully to:\n{zip_path}", 
                            "Export Complete", wx.OK | wx.ICON_INFORMATION)
                            
            except Exception as e:
                wx.MessageBox(f"Error exporting evidence: {str(e)}", 
                            "Export Error", wx.OK | wx.ICON_ERROR)
            
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
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main() 