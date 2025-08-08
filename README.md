# Evidence Manager

A comprehensive evidence management application built with Python and PyQt6 for organizing and tracking evidence related to people.

## Features

- **Person Management**: Add, view, and delete people from your evidence database
- **Information Organization**: Store various types of information (usernames, addresses, phone numbers, etc.) for each person
- **Image Management**: Add and organize images with thumbnail previews
- **Audio Management**: Add and organize audio files with playback support
- **Video Management**: Add and organize video files with playback support
- **Auto-Organization**: Automatically creates folder structure and organizes data
- **Clean Interface**: Modern, intuitive GUI with tabbed interface
- **Data Persistence**: All data is saved in JSON format and organized in folders

## Improvements (Refactor)

- Non-blocking import/export and file copy operations to prevent UI freezes
- Safer, atomic JSON writes for settings and person data to avoid corruption
- Image thumbnail generation and caching for fast loading in tables
- Deduplicated media handling for images, audio, and videos (less code, fewer bugs)
- More defensive error handling and cross-platform open/play support

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python evidence_manager.py
   ```

## Usage

### Getting Started

1. **Launch the Application**: Run `python evidence_manager.py`
2. **Evidence Folder**: The app automatically creates an "Evidence" folder in the same directory as the script
3. **Add Your First Person**: Click the "+ Add Person" button and enter a name

### Managing People

- **Add Person**: Click "+ Add Person" and enter the person's name
- **Select Person**: Click on any person in the left panel to view their evidence
- **Delete Person**: Select a person and click "Delete Person" (removes all associated data)

### Information Management

1. **Select the "Information" tab** when viewing a person
2. **Add Information**:
   - Enter the type of information (e.g., "Online Username", "Address", "Phone Number")
   - Enter the value
   - Click "Add Info"
3. **Edit Information**: Right-click on any information item and select "Edit"
4. **Delete Information**: Right-click on any information item and select "Delete"

### Image Management

1. **Select the "Images" tab** when viewing a person
2. **Add Images**: Click "Add Image" and select image files (supports PNG, JPG, JPEG, GIF, BMP)
3. **View Images**: Right-click on any image and select "Open Image"
4. **Rename Images**: Right-click on any image and select "Rename"
5. **Delete Images**: Right-click on any image and select "Delete"

### Audio Management

1. **Select the "Audio" tab** when viewing a person
2. **Add Audio**: Click "Add Audio" and select audio files (supports MP3, WAV, M4A, AAC, OGG)
3. **Play Audio**: Right-click on any audio file and select "Play Audio"
4. **Rename Audio**: Right-click on any audio file and select "Rename"
5. **Delete Audio**: Right-click on any audio file and select "Delete"

### Video Management

1. **Select the "Videos" tab** when viewing a person
2. **Add Videos**: Click "Add Video" and select video files (supports MP4, AVI, MOV, WMV, FLV, MKV, WEBM)
3. **Play Videos**: Right-click on any video file and select "Play Video"
4. **Rename Videos**: Right-click on any video file and select "Rename"
5. **Delete Videos**: Right-click on any video file and select "Delete"

### Data Organization

The application automatically organizes data as follows:

```
Evidence/
├── Person_Name_1/
│   ├── person_data.json
│   ├── images/
│   │   ├── image1.jpg
│   │   └── image2.png
│   ├── audio/
│   │   └── recording1.mp3
│   └── videos/
│       └── video1.mp4
├── Person_Name_2/
│   ├── person_data.json
│   ├── images/
│   │   └── image3.gif
│   ├── audio/
│   └── videos/
```

- **Folder Names**: Person names with spaces replaced by underscores
- **JSON Data**: All information is stored in `person_data.json` files
- **Images**: All images are stored in `images/` subfolders

## File Structure

- `evidence_manager.py` - Main application file
- `requirements.txt` - Python dependencies
- `Evidence/` - Auto-created folder containing all evidence data

## Supported File Formats

### Images
- PNG
- JPG/JPEG
- GIF
- BMP

### Audio
- MP3
- WAV
- M4A
- AAC
- OGG

### Video
- MP4
- AVI
- MOV
- WMV
- FLV
- MKV
- WEBM

## Data Format

Each person's data is stored in JSON format with the following structure:

```json
{
  "name": "Person Name",
  "created": "2024-01-01T12:00:00",
  "info": {
    "Online Username": ["username1", "username2"],
    "Address": ["123 Main St"],
    "Phone Number": ["555-1234"]
  },
  "images": [{"display_name": "Image1", "filename": "image1.jpg"}],
  "audio": [{"display_name": "Recording1", "filename": "recording1.mp3"}],
  "videos": [{"display_name": "Video1", "filename": "video1.mp4"}]
}
```

## Tips

- **Backup**: Regularly backup your "Evidence" folder
- **Naming**: Use descriptive information types for better organization
- **Images**: The app creates thumbnails for better performance
- **Data Integrity**: The app automatically handles file organization and data persistence

## Troubleshooting

- **Missing Dependencies**: Run `pip install -r requirements.txt`
- **Permission Errors**: Ensure you have write permissions in the application directory
- **Image Loading Issues**: Check that image files are not corrupted and are in supported formats