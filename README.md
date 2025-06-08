# FocusFlow

**FocusFlow** is a Python app built with [Flet](https://flet.dev/) that helps you rotate through a list of tasks on a timer. Perfect for managing your attention span, or at least pretending to.

![FocusFlow main screen](screenshot.png)

## Features

- Create, edit, and delete tasks (aka procrastinate responsibly)
- Custom task order with rotation
- Timer-based transitions with auto-switch
- Option to extend task duration manually
- Persistent task storage via JSON (no database, no problem)
- Built with [Flet](https://flet.dev/) for a modern cross‑platform GUI

## Installation

You should use [`uv`](https://github.com/astral-sh/uv) with this project. Here's how to get started:

```bash
uv venv
uv sync
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
uv pip install pip  # needed because Flet installs packages at runtime
```

## Run
```bash
uv run main.py
```
