"""
notepad.py
Notepad application using tkinter.

Features:
- New / Open / Save / Save As
- Recent files (stores last 10 in user's home)
- Undo / Redo / Cut / Copy / Paste / Select All
- Find & Replace
- Go To Line
- Font selection (family & size)
- Word wrap toggle
- Status bar (line, column, chars)
- Auto-save toggle & interval
- Keyboard shortcuts
- Simple About dialog

Dependencies: only Python standard library (tkinter)
Tested: Python 3.8+

Author: Generated for Vikash
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font, simpledialog
import os
import json
import time
import threading
from pathlib import Path

# --------- Constants and paths ----------
APP_NAME = "Notepad"
CONFIG_DIR = Path.home() / ".jobready_notepad"
CONFIG_DIR.mkdir(exist_ok=True)
RECENT_FILE = CONFIG_DIR / "recent.json"
AUTOSAVE_FILE = CONFIG_DIR / "autosave.txt"

MAX_RECENT = 10
DEFAULT_AUTOSAVE_INTERVAL = 120  # seconds

# --------- Utility functions ----------
def load_recent():
    try:
        if RECENT_FILE.exists():
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("recent", [])
    except Exception:
        pass
    return []

def save_recent(recent_list):
    try:
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"recent": recent_list[:MAX_RECENT]}, f)
    except Exception:
        pass

def add_to_recent(filepath):
    if not filepath:
        return
    recent = load_recent()
    filepath = os.path.abspath(filepath)
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    save_recent(recent)

# --------- Main Application ----------
class JobReadyNotepad(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Untitled")
        self.geometry("1000x650")
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # State
        self.filepath = None
        self.saved = True
        self.wrap_mode = tk.FALSE
        self.autosave_enabled = False
        self.autosave_interval = DEFAULT_AUTOSAVE_INTERVAL
        self.autosave_thread = None
        self.quit_autosave = threading.Event()

        # Fonts
        self.current_font_family = "Arial"
        self.current_font_size = 12

        # Build UI
        self._build_menu()
        self._build_toolbar()
        self._build_text_widget()
        self._build_statusbar()
        self._bind_shortcuts()
        self._load_recent_menu()

        # Start status update
        self.after(200, self._update_status)

    # ---------- UI Construction ----------
    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        self.recent_menu = tk.Menu(file_menu, tearoff=False)
        file_menu.add_cascade(label="Open Recent", menu=self.recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self.text_event("<<Undo>>"))
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self.text_event("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.text_event("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.text_event("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.text_event("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace...", accelerator="Ctrl+F", command=self.find_replace)
        edit_menu.add_command(label="Go To Line...", accelerator="Ctrl+G", command=self.go_to_line)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=lambda: self.text_event("<<SelectAll>>"))
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_checkbutton(label="Word Wrap", command=self.toggle_wrap, variable=self.wrap_mode)
        view_menu.add_command(label="Font...", command=self.choose_font)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Auto-save", command=self.toggle_autosave, onvalue=True, offvalue=False,
                                 variable=tk.BooleanVar(value=self.autosave_enabled))
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def _build_toolbar(self):
        # Simple toolbar with basic buttons
        toolbar = ttk.Frame(self, padding=(2,2))
        toolbar.pack(side=tk.TOP, fill=tk.X)
        new_btn = ttk.Button(toolbar, text="New", command=self.new_file)
        open_btn = ttk.Button(toolbar, text="Open", command=self.open_file)
        save_btn = ttk.Button(toolbar, text="Save", command=self.save_file)
        fs_btn = ttk.Button(toolbar, text="Find", command=self.find_replace)
        font_btn = ttk.Button(toolbar, text="Font", command=self.choose_font)

        for w in (new_btn, open_btn, save_btn, fs_btn, font_btn):
            w.pack(side=tk.LEFT, padx=2)

    def _build_text_widget(self):
        # Main text widget with vertical & horizontal scrollbars
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(frame, wrap="none", undo=True, autoseparators=True, maxundo=-1)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Set default font
        self._apply_font()

        # Scrollbars
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.text.yview)
        x_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Track changes
        self.text.bind("<<Modified>>", self._on_text_modified)
        self.text.bind("<KeyRelease>", lambda e: self._update_status())

    def _build_statusbar(self):
        status = ttk.Frame(self, relief=tk.SUNKEN)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status, text="Line 1, Col 1 | 0 chars")
        self.status_label.pack(side=tk.LEFT, padx=4)

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-s>", lambda e: self.save_file())
        self.bind_all("<Control-S>", lambda e: self.save_as())
        self.bind_all("<Control-f>", lambda e: self.find_replace())
        self.bind_all("<Control-g>", lambda e: self.go_to_line())
        self.bind_all("<Control-a>", lambda e: self.text_event("<<SelectAll>>"))
        self.bind_all("<Control-z>", lambda e: self.text_event("<<Undo>>"))
        self.bind_all("<Control-y>", lambda e: self.text_event("<<Redo>>"))

    # ---------- File operations ----------
    def new_file(self):
        if not self._confirm_discard():
            return
        self.text.delete("1.0", tk.END)
        self.filepath = None
        self.saved = True
        self.title(f"{APP_NAME} - Untitled")

    def open_file(self, path=None):
        if not self._confirm_discard():
            return
        if path is None:
            path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt *.md *.py *.log *.cfg"), ("All files", "*.*")])
            if not path:
                return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", data)
            self.filepath = path
            self.saved = True
            self.title(f"{APP_NAME} - {os.path.basename(path)}")
            add_to_recent(path)
            self._load_recent_menu()
        except Exception as e:
            messagebox.showerror("Open Error", f"Could not open file:\n{e}")

    def save_file(self):
        if not self.filepath:
            return self.save_as()
        try:
            text = self.text.get("1.0", tk.END)
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(text.rstrip("\n"))
            self.saved = True
            add_to_recent(self.filepath)
            self._load_recent_menu()
            self.title(f"{APP_NAME} - {os.path.basename(self.filepath)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{e}")

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        self.filepath = path
        self.save_file()

    def _confirm_discard(self):
        if not self.saved and self.text.get("1.0", tk.END).strip():
            res = messagebox.askyesnocancel("Save Changes", "You have unsaved changes. Save before continuing?")
            if res is None:
                return False
            if res:
                self.save_file()
        return True

    # ---------- Edit helpers ----------
    def text_event(self, sequence):
        try:
            self.text.event_generate(sequence)
        except Exception:
            pass

    def _on_text_modified(self, event=None):
        # mark saved flag false when modified
        self.text.edit_modified(False)
        self.saved = False

    # ---------- Find & Replace ----------
    def find_replace(self):
        dialog = tk.Toplevel(self)
        dialog.title("Find & Replace")
        dialog.transient(self)
        dialog.geometry("400x160")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Find:").pack(anchor=tk.W, padx=8, pady=(8,0))
        find_entry = ttk.Entry(dialog, width=50)
        find_entry.pack(padx=8)

        ttk.Label(dialog, text="Replace with:").pack(anchor=tk.W, padx=8, pady=(6,0))
        replace_entry = ttk.Entry(dialog, width=50)
        replace_entry.pack(padx=8)

        def do_find():
            target = find_entry.get()
            if not target:
                return
            start = self.text.index(tk.INSERT)
            idx = self.text.search(target, start, tk.END, nocase=True)
            if not idx:
                messagebox.showinfo("Find", "No more occurrences found.")
                return
            end = f"{idx}+{len(target)}c"
            self.text.tag_remove("findsel", "1.0", tk.END)
            self.text.tag_add("findsel", idx, end)
            self.text.tag_config("findsel", background="yellow")
            self.text.mark_set(tk.INSERT, end)
            self.text.see(idx)

        def do_replace():
            target = find_entry.get()
            repl = replace_entry.get()
            if not target:
                return
            content = self.text.get("1.0", tk.END)
            new_content = content.replace(target, repl)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", new_content)
            self.saved = False
            messagebox.showinfo("Replace", "All occurrences replaced.")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Find Next", command=do_find).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Replace All", command=do_replace).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=6)

    # ---------- Go To Line ----------
    def go_to_line(self):
        total_lines = int(self.text.index("end-1c").split(".")[0])
        line_no = simpledialog.askinteger("Go To Line", f"Enter line number (1 - {total_lines}):", parent=self, minvalue=1, maxvalue=total_lines)
        if line_no is None:
            return
        self.text.mark_set(tk.INSERT, f"{line_no}.0")
        self.text.see(f"{line_no}.0")
        self._update_status()

    # ---------- Font & wrap ----------
    def choose_font(self):
        # Simple font chooser dialog
        dialog = tk.Toplevel(self)
        dialog.title("Choose Font")
        dialog.transient(self)
        dialog.geometry("360x220")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Family:").pack(anchor=tk.W, padx=8, pady=(8,0))
        families = list(font.families())
        fam_var = tk.StringVar(value=self.current_font_family)
        fam_combo = ttk.Combobox(dialog, values=sorted(families), textvariable=fam_var)
        fam_combo.pack(fill=tk.X, padx=8)

        ttk.Label(dialog, text="Size:").pack(anchor=tk.W, padx=8, pady=(8,0))
        size_var = tk.IntVar(value=self.current_font_size)
        size_spin = ttk.Spinbox(dialog, from_=6, to=72, textvariable=size_var)
        size_spin.pack(fill=tk.X, padx=8)

        def apply_font():
            self.current_font_family = fam_var.get()
            self.current_font_size = int(size_var.get())
            self._apply_font()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=12)
        ttk.Button(btn_frame, text="Apply", command=apply_font).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=6)

    def _apply_font(self):
        f = font.Font(family=self.current_font_family, size=self.current_font_size)
        self.text.configure(font=f)

    def toggle_wrap(self):
        if self.wrap_mode.get():
            self.text.configure(wrap="word")
        else:
            self.text.configure(wrap="none")

    # ---------- Status updates ----------
    def _update_status(self):
        line, col = self.text.index(tk.INSERT).split(".")
        chars = len(self.text.get("1.0", "end-1c"))
        self.status_label.config(text=f"Line {line}, Col {int(col)+1} | {chars} chars")
        # schedule next update
        self.after(400, self._update_status)

    # ---------- Recent files ----------
    def _load_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        recent = load_recent()
        if not recent:
            self.recent_menu.add_command(label="(No recent files)", state=tk.DISABLED)
            return
        for i, path in enumerate(recent):
            lbl = f"{i+1}. {os.path.basename(path)}"
            self.recent_menu.add_command(label=lbl, command=lambda p=path: self.open_file(p))

    # ---------- Auto-save ----------
    def toggle_autosave(self):
        self.autosave_enabled = not self.autosave_enabled
        if self.autosave_enabled:
            # ask interval
            val = simpledialog.askinteger("Auto-save", "Auto-save interval (seconds):", parent=self, minvalue=10, initialvalue=self.autosave_interval)
            if val:
                self.autosave_interval = val
            self.quit_autosave.clear()
            self.autosave_thread = threading.Thread(target=self._autosave_loop, daemon=True)
            self.autosave_thread.start()
            messagebox.showinfo("Auto-save", f"Auto-save enabled every {self.autosave_interval} seconds.")
        else:
            self.quit_autosave.set()
            messagebox.showinfo("Auto-save", "Auto-save disabled.")

    def _autosave_loop(self):
        while not self.quit_autosave.is_set():
            time.sleep(self.autosave_interval)
            if self.quit_autosave.is_set():
                break
            try:
                data = self.text.get("1.0", tk.END)
                with open(AUTOSAVE_FILE, "w", encoding="utf-8") as f:
                    f.write(data)
                # lightweight feedback to the titlebar (non-intrusive)
                self.after(0, lambda: self.title(f"{APP_NAME} - Auto-saved"))
                # restore title after short delay
                self.after(1200, lambda: self._restore_title())
            except Exception:
                pass

    def _restore_title(self):
        if self.filepath:
            name = os.path.basename(self.filepath)
        else:
            name = "Untitled"
        self.title(f"{APP_NAME} - {name}")

    # ---------- About & Exit ----------
    def show_about(self):
        messagebox.showinfo("About", f"{APP_NAME}\nA job-ready Notepad built with Python & Tkinter.\n\nFeatures: Find/Replace, Recent Files, Auto-save, Font selection, Word wrap, Status bar.")

    def on_exit(self):
        if not self._confirm_discard():
            return
        # stop autosave thread if running
        self.quit_autosave.set()
        self.destroy()

# ---------- Run ----------
def main():
    app = JobReadyNotepad()
    # Try to open autosave if exists
    if AUTOSAVE_FILE.exists():
        try:
            with open(AUTOSAVE_FILE, "r", encoding="utf-8") as f:
                data = f.read()
            if data.strip():
                if messagebox.askyesno("Recover file", "An autosave file was found. Recover it?"):
                    app.text.delete("1.0", tk.END)
                    app.text.insert("1.0", data)
                    app.saved = False
        except Exception:
            pass
    app.mainloop()

if __name__ == "__main__":
    main()
