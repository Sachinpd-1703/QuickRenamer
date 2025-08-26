import os
import sys

try:
    from tkinterdnd2 import DND_FILES
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    DND_FILES = None


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def check_drag_drop():
    if not DRAG_DROP_AVAILABLE:
        print("Warning: tkinterdnd2 not found. Drag-and-drop disabled.")
        print("Install with: pip install tkinterdnd2")
    return DRAG_DROP_AVAILABLE
