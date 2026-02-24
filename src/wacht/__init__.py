"""Wacht - Live Reload Server

A simple HTTP server with automatic browser reload when files change.
"""

__version__ = "0.1.0"

import http.server
import json
import os
import signal
import socketserver
import sys
import threading
import time
from pathlib import Path
from urllib.parse import unquote


RELOAD_SCRIPT = """<script>
(function() {
    let mtimes = {};
    function check() {
        fetch('/.mtimes', {cache: 'no-cache'})
            .then(r => r.json())
            .then(newMtimes => {
                if (JSON.stringify(newMtimes) !== JSON.stringify(mtimes)) {
                    mtimes = newMtimes;
                    location.reload();
                }
            }).catch(() => {});
    }
    setInterval(check, 1000);
})();
</script>"""

DEFAULT_HTML = """<!DOCTYPE html>
<html><body>
<h1>Wacht</h1>
<p>Live reload server running.</p>
<p>Place an index.html file in the webroot to get started.</p>
</body></html>"""


def get_mtime(webroot: str | Path) -> dict:
    """Get modification times of all files in webroot."""
    mtime = {}
    path = Path(webroot)
    if path.is_dir():
        for f in path.iterdir():
            if f.is_file():
                mtime[f.name] = int(f.stat().st_mtime)
    return mtime


def get_pid_file() -> Path:
    """Get path to PID file."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    pid_dir = Path(runtime) / "wacht" if runtime else Path("/tmp/wacht")
    pid_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    return pid_dir / "wacht.pid"


class ReloadHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with live reload injection."""

    def __init__(self, *args, webroot=".", **kwargs):
        self.webroot = Path(webroot).resolve()
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def translate_path(self, path: str) -> str:
        """Translate URL path to filesystem path."""
        path = unquote(path).split("?")[0].split("#")[0]
        path = os.path.normpath(path)
        words = [w for w in path.split("/") if w and w not in (".", "..")]
        return str(self.webroot.joinpath(*words)) if words else str(self.webroot)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/.mtimes":
            return self._serve_mtimes()
        if self.path == "/":
            return self._serve_index()
        if self.path.endswith((".html", ".htm")):
            return self._serve_html()
        return self._serve_file()

    def _serve_mtimes(self):
        """Return JSON with file modification times."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(get_mtime(str(self.webroot))).encode())

    def _serve_index(self):
        """Serve index.html or show default page."""
        for name in ("index.html", "index.htm"):
            if (self.webroot / name).is_file():
                self.path = f"/{name}"
                return self._serve_html()
        self._serve_html(content=DEFAULT_HTML)

    def _serve_html(self, content: str | None = None):
        """Serve HTML with reload script injected."""
        path = self.translate_path(self.path)
        if content is None:
            try:
                content = Path(path).read_text()
            except FileNotFoundError:
                return self.send_error(404)

        mtimes = get_mtime(str(self.webroot))
        script = RELOAD_SCRIPT.replace(
            "let mtimes = {}", f"let mtimes = {json.dumps(mtimes)}"
        )

        if "</body>" in content:
            content = content.replace("</body>", f"{script}</body>")
        else:
            content = content + script

        data = content.encode()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self):
        """Serve static files."""
        path = self.translate_path(self.path)
        try:
            data = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (FileNotFoundError, IsADirectoryError):
            self.send_error(404)


class ReloadServer:
    """Live reload HTTP server."""

    def __init__(self, port: int = 8080, webroot: str | Path = ".", log=None):
        self.port = port
        self.webroot = Path(webroot).resolve()
        self.log = log or sys.stdout
        self._server: socketserver.TCPServer | None = None
        self._pid_file: Path | None = None
        self._shutdown_event = threading.Event()

    def _handler_factory(self, *args, **kwargs):
        """Create handler with webroot preset."""
        return ReloadHandler(*args, webroot=str(self.webroot), **kwargs)

    def start(self, daemon: bool = False):
        """Start the server."""
        self._pid_file = get_pid_file()

        if daemon:
            if self._pid_file.exists():
                print(f"Error: PID file exists. Server running?", file=sys.stderr)
                sys.exit(1)
            print(f"Starting daemon...", file=sys.stdout)
            sys.stdout.flush()
            self._daemonize()
            # Write PID file AFTER daemonizing (grandchild process)
            self._pid_file.write_text(str(os.getpid()))

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)  # Ctrl+C
        signal.signal(signal.SIGTERM, self._shutdown)  # kill, systemctl stop
        signal.signal(signal.SIGHUP, self._shutdown)  # Terminal disconnect

        # Ignore SIGPIPE (broken pipe from client disconnect)
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

        socketserver.TCPServer.allow_reuse_address = True
        try:
            self._server = socketserver.TCPServer(
                ("", self.port), self._handler_factory
            )
            if not daemon:
                print(f"Server running on http://localhost:{self.port}", file=self.log)
                print(f"Webroot: {self.webroot}", file=self.log)
                print("Press Ctrl+C to stop", file=self.log)

            # Start server in a thread so we can respond to signals
            server_thread = threading.Thread(target=self._server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            # Wait for shutdown signal
            while not self._shutdown_event.is_set():
                time.sleep(0.1)

        except OSError as e:
            print(f"Error: Port {self.port} unavailable ({e})", file=self.log)
            if daemon and self._pid_file.exists():
                self._pid_file.unlink()
            sys.exit(1)

    def stop(self):
        """Stop the daemon."""
        self._pid_file = get_pid_file()
        if not self._pid_file.exists():
            print(f"No PID file found at {self._pid_file}", file=sys.stderr)
            raise SystemExit(1)

        pid = int(self._pid_file.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Daemon {pid} stopped", file=sys.stdout)
            self._pid_file.unlink()
        except ProcessLookupError:
            print(f"Process {pid} not found", file=sys.stderr)
            self._pid_file.unlink()
        except PermissionError:
            print(f"Permission denied to kill {pid}", file=sys.stderr)
            raise SystemExit(1)

    def _daemonize(self):
        """Double-fork daemonize."""
        try:
            if os.fork() > 0:
                sys.exit(0)
        except OSError as e:
            print(f"Fork failed: {e}", file=sys.stderr)
            sys.exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            if os.fork() > 0:
                sys.exit(0)
        except OSError as e:
            print(f"Fork failed: {e}", file=sys.stderr)
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        with open("/dev/null", "r") as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(os.devnull, "a+") as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())

    def _shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        print(f"\nReceived {sig_name}, shutting down gracefully...", file=self.log)

        # Signal the main loop to exit
        self._shutdown_event.set()

        # Clean shutdown
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
                print("Server stopped.", file=self.log)
            except Exception as e:
                print(f"Error during shutdown: {e}", file=self.log)

        # Clean up PID file if daemon
        if hasattr(self, "_pid_file") and self._pid_file and self._pid_file.exists():
            try:
                self._pid_file.unlink()
            except OSError:
                pass

        sys.exit(0)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Live reload HTTP server",
        usage="wacht [-h] [-p PORT] [-l LOG] [-d] [-s] [-v] [WEBROOT]",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Port (default: 8080)"
    )
    parser.add_argument(
        "WEBROOT", nargs="?", default=".", help="Web root directory (default: .)"
    )
    parser.add_argument(
        "-l", "--log", default="-", help="Log file (default: stdout, 'null' to disable)"
    )
    parser.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("-s", "--stop", action="store_true", help="Stop daemon")
    parser.add_argument(
        "-v", "--version", action="version", version=f"wacht {__version__}"
    )
    args = parser.parse_args()

    log = (
        open(os.devnull, "w")
        if args.log == "null"
        else (open(args.log, "w") if args.log != "-" else sys.stdout)
    )
    server = ReloadServer(port=args.port, webroot=args.WEBROOT, log=log)

    if args.stop:
        server.stop()
    else:
        server.start(daemon=args.daemon)


if __name__ == "__main__":
    main()
