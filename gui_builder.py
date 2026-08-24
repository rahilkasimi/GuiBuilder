#!/usr/bin/env python3
"""Tkinter Visual GUI Designer — SRP modular entry point."""
import tkinter as tk
from gui_builder.app import GUIBuilderApp


def main() -> None:
    root = tk.Tk()
    GUIBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
