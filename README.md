# Notepad

A job-ready Notepad-style text editor built with Python and Tkinter.

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
python job_ready_notepad.py
```

## Build Windows executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed job_ready_notepad.py --name JobReadyNotepad
```

## License
MIT
