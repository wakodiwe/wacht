<div align="center">

<img src="docs/assets/src/img/wacht.png" alt="Wacht Logo" width="75%"/>

**A minimal HTTP server with automatic live reload for web development.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square)](pyproject.toml)

*Zero config. Zero browser extensions. Just save and watch your browser update.*

</div>

---

## What is wacht?

**Wacht** (German for *watch*) is a dead-simple local dev server that serves your static files and automatically reloads the browser whenever something changes — no plugins, no config files, no fuss.

It works by injecting a tiny JavaScript snippet into HTML pages that polls a `/.mtimes` endpoint. When it detects a change, the page reloads. That's it.

---

## Installation

**Quick run — no install needed:**
```bash
python3 wacht.py
```

**Install as a local dev tool:**
```bash
pip install -e .
wacht --help
```

**Install system-wide as a binary:**
```bash
make install   # requires sudo — installs to /usr/local/bin/
```

---

## Usage

```bash
wacht                          # Serve current directory on port 8080
wacht ./public                 # Serve a specific directory
wacht -p 3000                  # Use a custom port
wacht -l /var/log/wacht.log    # Log output to a file
wacht -d                       # Run as a background daemon
wacht -s                       # Stop a running daemon
```

---

## How It Works

```
Browser                  wacht server
   │                           │
   │   GET /index.html         │
   │──────────────────────────▶│
   │   HTML + injected <script>│
   │◀──────────────────────────│
   │                           │
   │   Poll /.mtimes (1s)      │
   │──────────────────────────▶│
   │   { "file.html": 1234567 }│
   │◀──────────────────────────│
   │                           │
   │   [file changed]          │
   │   window.location.reload()│
   │◀──────────────────────────│
```

1. Wacht starts an HTTP server on the specified port
2. HTML responses get a small polling script injected automatically
3. The `/.mtimes` endpoint returns a JSON map of file → modification timestamp
4. When a timestamp changes, the browser reloads itself

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `/` | Serves `index.html` or a default landing page |
| `/*.html` | Serves HTML with the live-reload script injected |
| `/.mtimes` | Returns JSON with file modification timestamps |
| `/*` | Serves static assets (CSS, JS, images, fonts…) |

---

## Development

```bash
make test     # Run the test suite
make run      # Start the server via python3 wacht.py
make build    # Build a standalone binary with PyInstaller
make clean    # Remove build artifacts
```

---

## Project Structure

```
wacht/
├── wacht.py                    # CLI entry point
├── wacht/
│   └── __init__.py             # Core server implementation
├── tests/
│   └── test_wacht.py           # Test suite
├── docs/assets/src/img/        # Logo and assets
├── Makefile
├── pyproject.toml
└── README.md
```

**Key internals:**
- `ReloadServer` — main server class with optional daemon support
- `ReloadHandler` — HTTP handler that injects the live-reload script into HTML
- `get_mtime()` — returns modification timestamps for the watched directory
- `get_pid_file()` — manages the daemon PID file location

---

## Requirements

- Python 3.10+
- No external dependencies (pure stdlib)

---

## License

[MIT](LICENSE) — use it, fork it, ship it.

---
