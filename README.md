# Evidence Manager

A cross-platform GUI application for managing evidence on people, built with Rust and egui.

## Features

- **Person Management**: Add, edit, and delete people with notes and tags
- **Evidence Organization**: Automatically organize evidence files by type (images, audio, video, documents)
- **Drag & Drop Support**: Drag files onto the application to add evidence or import .ema archives
- **Export/Import**: Export all evidence as .ema (Evidence Manager Archive) files and import them
- **Cross-Platform**: Works on Windows, macOS, and Linux

## File Structure

The application creates an `Evidence` folder relative to the executable with the following structure:

```
Evidence/
├── Person_Name/
│   ├── person_data.json    # Person information and metadata
│   ├── images/            # Image evidence files
│   ├── audio/             # Audio evidence files
│   ├── videos/            # Video evidence files
│   └── documents/         # Document evidence files
└── ...
```

## Supported File Types

- **Images**: jpg, jpeg, png, gif, bmp, tiff, webp
- **Audio**: mp3, wav, flac, aac, ogg, m4a
- **Video**: mp4, avi, mov, wmv, flv, webm, mkv
- **Documents**: pdf, doc, docx, txt, rtf

## Usage

### Adding People
1. Click "Add Person" to create a new person entry
2. Enter name, notes, and tags (comma-separated)
3. Click "Add" to save

### Adding Evidence
1. Select a person from the left panel
2. Drag and drop files onto the application
3. Files are automatically organized by type in the person's folder

### Exporting Evidence
1. Click "Export All" to export all evidence as an .ema file
2. Choose save location and filename
3. The archive contains all persons and their evidence files

### Importing Evidence
1. Click "Import" to import an .ema file, or
2. Drag and drop an .ema file onto the application
3. All persons and evidence will be imported and merged