#!/usr/bin/env python3
"""
Interactive terminal UI to pick a .gitignore template from github/gitignore.
Type to filter, arrow keys to navigate, Enter to select.

Keeps a local clone of https://github.com/github/gitignore at
~/.local/share/gitignore-templates and pulls on each run when online.
"""

import curses
import os
import subprocess
import sys
from pathlib import Path


REPO_URL = "https://github.com/github/gitignore"
REPO_DIR = Path.home() / ".local" / "share" / "gitignore-templates"


def ensure_repo():
    if REPO_DIR.exists():
        print("Updating gitignore templates...", flush=True)
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=REPO_DIR,
            capture_output=True,
        )
    else:
        print("Cloning gitignore templates (one-time setup)...", flush=True)
        result = subprocess.run(
            ["git", "clone", "--depth=1", REPO_URL, str(REPO_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error cloning repo: {result.stderr.strip()}")
            sys.exit(1)


def get_templates():
    files = sorted(REPO_DIR.rglob("*.gitignore"), key=lambda p: p.name.lower())
    # Return paths relative to REPO_DIR, strip the .gitignore suffix for display
    return [str(p.relative_to(REPO_DIR))[: -len(".gitignore")] for p in files]


def interactive_select(stdscr, templates):
    curses.curs_set(1)
    curses.use_default_colors()
    try:
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # selected row
        curses.init_pair(2, curses.COLOR_CYAN, -1)                   # search label
        curses.init_pair(3, curses.COLOR_WHITE, -1)                  # dim status
    except curses.error:
        pass

    query = ""
    selected_idx = 0
    scroll_offset = 0

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        # Filter templates
        filtered = (
            [t for t in templates if query.lower() in t.lower()]
            if query
            else templates
        )

        # Clamp selection
        if selected_idx >= len(filtered):
            selected_idx = max(0, len(filtered) - 1)

        # Adjust scroll to keep selection visible
        list_height = max(1, height - 3)  # rows 2..height-2
        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + list_height:
            scroll_offset = selected_idx - list_height + 1

        # --- Search bar (row 0) ---
        label = "Search: "
        try:
            stdscr.addstr(0, 0, label, curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, len(label), query[: width - len(label) - 1])
        except curses.error:
            pass

        # --- Separator (row 1) ---
        try:
            stdscr.addstr(1, 0, ("─" * width)[: width - 1])
        except curses.error:
            pass

        # --- Template list (rows 2..height-2) ---
        for i in range(list_height):
            idx = i + scroll_offset
            if idx >= len(filtered):
                break
            row = i + 2
            if row >= height - 1:
                break
            name = filtered[idx]
            line = f" {name}"
            try:
                if idx == selected_idx:
                    stdscr.addstr(row, 0, line.ljust(width - 1)[: width - 1], curses.color_pair(1))
                else:
                    stdscr.addstr(row, 0, line[: width - 1])
            except curses.error:
                pass

        # --- Status bar (last row) ---
        if len(filtered) == 0:
            status = " No matches "
        else:
            status = f" {len(filtered)} template(s)  |  ↑↓ navigate  |  Enter select  |  Ctrl+C cancel "
        try:
            stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_DIM)
        except curses.error:
            pass

        # Position cursor in search bar
        cursor_x = min(len(label) + len(query), width - 1)
        try:
            stdscr.move(0, cursor_x)
        except curses.error:
            pass

        stdscr.refresh()

        # --- Input handling ---
        try:
            key = stdscr.get_wch()
        except KeyboardInterrupt:
            return None
        except curses.error:
            continue

        if key in ("\n", "\r", curses.KEY_ENTER):
            if filtered:
                return filtered[selected_idx]
            return None

        elif key == curses.KEY_UP:
            if selected_idx > 0:
                selected_idx -= 1

        elif key == curses.KEY_DOWN:
            if selected_idx < len(filtered) - 1:
                selected_idx += 1

        elif key == curses.KEY_PPAGE:  # Page Up
            selected_idx = max(0, selected_idx - list_height)

        elif key == curses.KEY_NPAGE:  # Page Down
            selected_idx = min(len(filtered) - 1, selected_idx + list_height)

        elif key in (curses.KEY_BACKSPACE, "\x7f", "\b", 127):
            if query:
                query = query[:-1]
                selected_idx = 0
                scroll_offset = 0

        elif key == "\x03":  # Ctrl+C
            return None

        elif key == "\x15":  # Ctrl+U — clear query
            query = ""
            selected_idx = 0
            scroll_offset = 0

        elif isinstance(key, str) and key.isprintable():
            query += key
            selected_idx = 0
            scroll_offset = 0


def main():
    if os.path.exists(".gitignore"):
        print("Error: .gitignore already exists in the current directory.")
        sys.exit(1)

    ensure_repo()

    templates = get_templates()
    if not templates:
        print("No templates found.")
        sys.exit(1)

    selected = curses.wrapper(interactive_select, templates)

    if not selected:
        print("No template selected.")
        sys.exit(0)

    src = REPO_DIR / (selected + ".gitignore")
    content = src.read_text()

    with open(".gitignore", "w") as f:
        f.write(content)

    print(f"Created .gitignore from '{selected}' template.")


if __name__ == "__main__":
    main()
