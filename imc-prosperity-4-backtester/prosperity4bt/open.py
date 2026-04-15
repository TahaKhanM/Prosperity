import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

def _find_visualizer_dist() -> Path:
    """Locate the visualizer dist directory.

    Searches from the current working directory upward for the repo structure,
    since __file__ may point to site-packages rather than the source tree.
    """
    # Strategy 1: look relative to CWD (common when running from the repo)
    for base in [Path.cwd(), Path(__file__).resolve().parent.parent]:
        # Check if the visualizer is a sibling directory
        candidate = base / "imc-prosperity-4-visualizer" / "dist"
        if candidate.is_dir():
            return candidate
        # Check parent (backtester is a subfolder of the repo)
        candidate = base.parent / "imc-prosperity-4-visualizer" / "dist"
        if candidate.is_dir():
            return candidate

    # Strategy 2: walk up from CWD looking for the repo root
    current = Path.cwd()
    for _ in range(10):
        candidate = current / "imc-prosperity-4-visualizer" / "dist"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    # Fallback: return a path that won't exist, triggering the warning
    return Path(__file__).resolve().parent.parent.parent / "imc-prosperity-4-visualizer" / "dist"


_VISUALIZER_DIST = _find_visualizer_dist()


class VisualizerHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves both the visualizer app and the backtest log file.

    URL routing:
      /imc-prosperity-4-visualizer/*  → visualizer dist/ directory
      /logs/<filename>                → the backtest output file
      /                               → redirect to visualizer with ?open= param
    """

    # Set by open_visualizer() before the server starts
    log_file_path: Path = Path()
    log_file_name: str = ""
    server_port: int = 0

    def do_GET(self) -> None:
        prefix = "/imc-prosperity-4-visualizer/"

        if self.path == "/":
            # Redirect root to the visualizer with the log file URL
            log_url = f"http://localhost:{self.server_port}/logs/{self.log_file_name}"
            self.send_response(302)
            self.send_header("Location", f"{prefix}?open={log_url}")
            self.end_headers()
            return

        if self.path.startswith("/logs/"):
            # Serve the backtest log file
            self._serve_file(self.log_file_path)
            # After the log is fetched, signal shutdown
            self.server.shutdown_flag = True  # type: ignore[attr-defined]
            return

        if self.path.startswith(prefix):
            # Serve visualizer dist files
            relative = self.path[len(prefix):]
            if not relative or relative == "":
                relative = "index.html"

            file_path = _VISUALIZER_DIST / relative.split("?")[0]
            if file_path.is_file():
                self._serve_file(file_path)
                return

            # SPA fallback: serve index.html for unknown paths (React Router)
            self._serve_file(_VISUALIZER_DIST / "index.html")
            return

        self.send_error(404)

    def _serve_file(self, file_path: Path) -> None:
        try:
            data = file_path.read_bytes()
        except (FileNotFoundError, PermissionError):
            self.send_error(404)
            return

        content_type = self._guess_type(file_path)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _guess_type(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        types = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".ico": "image/x-icon",
            ".map": "application/json",
            ".log": "text/plain; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }
        return types.get(ext, "application/octet-stream")

    def end_headers(self) -> None:
        # Only add CORS if not already added by _serve_file
        if not any(k.lower() == "access-control-allow-origin" for k, v in self._headers_buffer_list()):
            self.send_header("Access-Control-Allow-Origin", "*")
        return super().end_headers()

    def _headers_buffer_list(self) -> list[tuple[str, str]]:
        """Parse headers already in the buffer."""
        pairs = []
        for line in self._headers_buffer:
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            if ":" in decoded:
                k, v = decoded.split(":", 1)
                pairs.append((k.strip(), v.strip()))
        return pairs

    def log_message(self, format: str, *args: Any) -> None:
        return


class CustomHTTPServer(HTTPServer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.shutdown_flag = False


def open_visualizer(output_file: Path) -> None:
    if not _VISUALIZER_DIST.is_dir():
        print(f"Warning: Visualizer dist not found at {_VISUALIZER_DIST}")
        print("Build it with: cd imc-prosperity-4-visualizer && pnpm install && pnpm build")
        print("Falling back to file-only mode (drag the log file into the visualizer manually).")
        return

    http_server = CustomHTTPServer(("localhost", 0), VisualizerHTTPRequestHandler)
    port = http_server.server_port

    # Configure the handler class with the log file details
    VisualizerHTTPRequestHandler.log_file_path = output_file
    VisualizerHTTPRequestHandler.log_file_name = output_file.name
    VisualizerHTTPRequestHandler.server_port = port

    url = f"http://localhost:{port}/"
    print(f"Opening visualizer at {url}")
    webbrowser.open(url)

    while not http_server.shutdown_flag:
        http_server.handle_request()
