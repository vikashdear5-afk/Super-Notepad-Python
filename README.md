# Notepad

Notepad-style text editor built with Python and Tkinter.

## Features
- New / Open / Save / Save As
- Recent files (persisted)
- Undo/Redo, Cut/Copy/Paste, Select All
- Find & Replace, Go To Line
- Font selection and Word wrap
- Status bar showing line/column/characters
- Optional auto-save
- Single-file distribution via PyInstaller

## Run
```bash
python NOTEPAD.py
```

## Build Windows executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed NOTEPAD.py --name NOTEPAD
```

## License
MIT
