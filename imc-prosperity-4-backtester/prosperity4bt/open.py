import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional


def _find_visualizer_dist(anchor: Optional[Path] = None) -> Optional[Path]:
    """Locate the visualizer dist/ directory by searching upward from anchor paths.

    The visualizer lives at <repo>/imc-prosperity-4-visualizer/dist/.
    We search upward from multiple starting points to find it.
    """
    start_dirs = [Path.cwd()]
    if anchor is not None:
        start_dirs.insert(0, anchor if anchor.is_dir() else anchor.parent)

    for start in start_dirs:
        current = start.resolve()
        for _ in range(10):
            candidate = current / "imc-prosperity-4-visualizer" / "dist"
            if candidate.is_dir() and (candidate / "index.html").is_file():
                return candidate
            if current.parent == current:
                break
            current = current.parent

    return None


class VisualizerHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves both the visualizer app and the backtest log file.

    URL routing:
      /imc-prosperity-4-visualizer/*  -> visualizer dist/ directory
      /logs/<filename>                -> the backtest output file
      /                               -> redirect to visualizer with ?open= param
    """

    # Set by open_visualizer() before the server starts
    log_file_path: Path = Path()
    log_file_name: str = ""
    server_port: int = 0
    visualizer_dist: Path = Path()

    def do_GET(self) -> None:
        prefix = "/imc-prosperity-4-visualizer/"

        if self.path == "/":
            log_url = f"http://localhost:{self.server_port}/logs/{self.log_file_name}"
            self.send_response(302)
            self.send_header("Location", f"{prefix}?open={log_url}")
            self.end_headers()
            return

        if self.path.startswith("/logs/"):
            self._serve_file(self.log_file_path)
            self.server.shutdown_flag = True  # type: ignore[attr-defined]
            return

        if self.path.startswith(prefix):
            relative = self.path[len(prefix):]
            if not relative:
                relative = "index.html"

            # Strip query string
            relative = relative.split("?")[0]
            file_path = self.visualizer_dist / relative
            if file_path.is_file():
                self._serve_file(file_path)
                return

            # SPA fallback for React Router
            self._serve_file(self.visualizer_dist / "index.html")
            return

        self.send_error(404)

    def _serve_file(self, file_path: Path) -> None:
        try:
            data = file_path.read_bytes()
        except (FileNotFoundError, PermissionError):
            self.send_error(404)
            return

        content_type = self._guess_content_type(file_path)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _guess_content_type(file_path: Path) -> str:
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
        self.send_header("Access-Control-Allow-Origin", "*")
        return super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        return


class CustomHTTPServer(HTTPServer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.shutdown_flag = False


def open_visualizer(output_file: Path) -> None:
    # Search from the output file location and CWD
    dist = _find_visualizer_dist(anchor=output_file)

    if dist is None:
        print("Warning: Visualizer dist/ not found.")
        print("Build it with: cd imc-prosperity-4-visualizer && pnpm install && pnpm build")
        print(f"Then re-run with --vis, or drag {output_file} into the visualizer manually.")
        return

    http_server = CustomHTTPServer(("localhost", 0), VisualizerHTTPRequestHandler)
    port = http_server.server_port

    VisualizerHTTPRequestHandler.log_file_path = output_file
    VisualizerHTTPRequestHandler.log_file_name = output_file.name
    VisualizerHTTPRequestHandler.server_port = port
    VisualizerHTTPRequestHandler.visualizer_dist = dist

    url = f"http://localhost:{port}/"
    print(f"Opening visualizer at {url}")
    webbrowser.open(url)

    while not http_server.shutdown_flag:
        http_server.handle_request()
