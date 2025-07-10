# Evidence Manager

A comprehensive evidence management application built with Python and wxPython for organizing and tracking evidence related to people.

## Features

- **Person Management**: Add, view, and delete people from your evidence database
- **Information Organization**: Store various types of information (usernames, addresses, phone numbers, etc.) for each person
- **Image Management**: Add and organize images with thumbnail previews
- **Auto-Organization**: Automatically creates folder structure and organizes data
- **Clean Interface**: Modern, intuitive GUI with tabbed interface
- **Data Persistence**: All data is saved in JSON format and organized in folders

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
3. **View Images**: Double-click on any thumbnail to open the image in your default viewer
4. **Delete Images**: Click the "Delete" button below any image

### Data Organization

The application automatically organizes data as follows:

```
Evidence/
├── Person_Name_1/
│   ├── person_data.json
│   └── images/
│       ├── image1.jpg
│       └── image2.png
├── Person_Name_2/
│   ├── person_data.json
│   └── images/
│       └── image3.gif
```

- **Folder Names**: Person names with spaces replaced by underscores
- **JSON Data**: All information is stored in `person_data.json` files
- **Images**: All images are stored in `images/` subfolders

## File Structure

- `evidence_manager.py` - Main application file
- `requirements.txt` - Python dependencies
- `Evidence/` - Auto-created folder containing all evidence data

## Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- BMP

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
  "images": ["image1.jpg", "image2.png"]
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

## Requirements

- Python 3.6+
- wxPython 4.2.1
- Pillow 10.0.1 