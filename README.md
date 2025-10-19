# Evidence Manager

A cross-platform GUI application for managing evidence on people, built with Rust and iced.

## Features

- **Person Management**: Add, edit, and delete people with information and quotes
- **Evidence Organization**: Organize evidence files by type (images, audio, video, documents, quotes)
- **File Selection**: Native file dialogs for adding evidence files with proper type filtering
- **Export/Import**: Export all evidence or individual persons as .ema (Evidence Manager Archive) files
- **Search and Filter**: Find people quickly with real-time search
- **Cross-Platform**: Works on Windows, macOS, and Linux

## File Structure

The application creates an `Evidence` folder in the project directory with the following structure:

```
Evidence/
├── Person_Name/
│   ├── person_data.json    # Person information and metadata
│   ├── images/            # Image evidence files
│   ├── audio/             # Audio evidence files
│   ├── videos/            # Video evidence files
│   ├── documents/         # Document evidence files
│   └── quotes/            # Quote evidence files
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
2. Enter the person's name
3. Click "Add" to save

### Adding Evidence
1. Select a person from the left panel
2. Choose the appropriate tab (Images, Audio, Videos, Documents)
3. Click "Select File to Add" to choose evidence files
4. Files are automatically organized by type in the person's folder

### Managing Information and Quotes
1. Select a person from the left panel
2. Go to the "Information" tab to add personal details
3. Go to the "Quotes" tab to add quotes with date, time, and place information

### Exporting Evidence
1. **Export All**: Click "Export All" to export all evidence as an .ema file
2. **Export Single Person**: Select a person and click "Export Evidence" to export only that person
3. Choose save location and filename
4. The archive contains all selected persons and their evidence files

### Importing Evidence
1. Click "Import .ema" to import an .ema file
2. Choose the .ema file to import
3. All persons and evidence will be imported and merged
4. Missing folder structures are automatically created

## Building

### Prerequisites
- Rust 1.70 or later
- Cargo

### Build Commands
```bash
# Debug build
cargo build

# Release build
cargo build --release

# Run the application
cargo run
```

## Architecture

The application is built with a clean separation between frontend and backend:

- **`main.rs`** - Application entry point and iced initialization
- **`state.rs`** - Application state management and message handling
- **`gui.rs`** - User interface rendering with iced widgets
- **`models.rs`** - Data structures and types
- **`file_manager.rs`** - File system operations and evidence management
- **`export_import.rs`** - Import/export functionality for .ema archives

## Technical Details

- **GUI Framework**: iced (cross-platform Rust GUI framework)
- **File Operations**: Native file dialogs via rfd
- **Data Storage**: JSON files with organized folder structure
- **Archive Format**: ZIP-based .ema files with person folders at root level
- **Async Operations**: Non-blocking file operations using iced's Command system

## License

This project is licensed under the MIT License.
