"""Shared standard-library and optional third-party imports."""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
import json
import copy
import subprocess
import sys
import tempfile
import os
import ast
import re
import platform
import shutil
import threading
import queue
import importlib.util
import calendar
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

# Pillow is a listed requirement (see requirements.txt, needed by exported
# apps that use the Image element), but the *builder's own* design-canvas
# thumbnail preview for the Image element should never hard-crash the whole
# app just because it's missing from this particular Python environment --
# it degrades to a placeholder icon instead (see CanvasRenderer._draw_image).
# Aliased to PILImage so it never reads as though it's the Image *element
# type* string used elsewhere.
try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PILImage = None
    ImageTk = None
    PIL_AVAILABLE = False