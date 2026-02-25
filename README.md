![Wacht Logo](/docs/assets/src/img/wacht.png "Wacht Logo")  

A minimal HTTP server with automatic live reload for web development.

## What It Does

Wacht serves static files from a directory and automatically reloads your browser when files change. No browser extensions needed—it injects a small JavaScript snippet into HTML pages that polls for changes.

## Installation

### Quick Run (No Install)

```bash
python3 wacht.py
```

### Development Install

```bash
pip install -e .
wacht --help
```

### Binary Install

```bash
make install  # Requires sudo, installs to /usr/local/bin/
```

## Usage

    wacht                           # Serve current directory on port 8080
    wacht -p 3000                   # Use custom port
    wacht ./public                  # Serve from specific directory
    wacht -l /var/log/wacht.log     # Log to file
    wacht -d                        # Run as background daemon
    wacht -s                        # Stop running daemon (or --stop)

## How It Works

1. Wacht starts an HTTP server on the specified port
2. When serving HTML files, it injects a script that polls `/.mtimes` every second
3. The `/.mtimes` endpoint returns JSON with file modification timestamps
4. When a file changes, the browser reloads automatically

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Serves index.html or default landing page |
| `/*.html` | Serves HTML with reload script injected |
| `/.mtimes` | Returns JSON of file modification times |
| `/*` | Serves static files (CSS, JS, images, etc.) |

## Development

```bash
make test      # Run test suite
make run       # Start server (python3 wacht.py)
make build     # Build binary with pyinstaller
make clean     # Remove build artifacts
```

## Architecture

wacht/
├── wacht.py              # CLI entry point
├── src/wacht/__init__.py # Core server implementation
├── tests/test_wacht.py   # Test suite
└── README.md             # This file

### Key Components

- **ReloadServer**: Main server class with daemon support
- **ReloadHandler**: HTTP request handler with live reload injection
- **get_mtime()**: Returns file modification times
- **get_pid_file()**: Manages daemon PID file location

## Requirements

- Python 3.10+
- No external dependencies (uses stdlib only)

## License

MIT
