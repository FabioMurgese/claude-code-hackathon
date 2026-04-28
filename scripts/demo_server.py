"""
Lightweight demo server for the live demo slide.

Serves presentation.html at / AND runs claims on demand at /run.
Opening http://localhost:7331 eliminates all browser CORS/file:// issues.

Usage:
    source .env
    .venv/bin/python scripts/demo_server.py        # default port 7331
    .venv/bin/python scripts/demo_server.py 8080   # custom port

Then open:  http://localhost:7331

Owner: Track A (Fabio)
"""
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT   = int(sys.argv[1]) if len(sys.argv) > 1 else 7331
ROOT   = Path(__file__).parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"
HTML   = ROOT / "presentation.html"


class DemoHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        # Serve the presentation
        if parsed.path in ("/", "/presentation.html"):
            if not HTML.exists():
                self._text("presentation.html not found — run: python scripts/build_presentation.py", 404)
                return
            body = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Health check
        if parsed.path == "/health":
            self._json({"status": "ok", "port": PORT})
            return

        # Run a claim through the agent
        if parsed.path == "/run":
            claim_id = parse_qs(parsed.query).get("claim", ["CLM-001"])[0]
            if not claim_id.replace("-", "").replace("_", "").isalnum():
                self._json({"error": "invalid claim_id"}, status=400)
                return
            try:
                result = subprocess.run(
                    [str(PYTHON), "-m", "src.agent", "ingest", claim_id],
                    capture_output=True, text=True, cwd=str(ROOT), timeout=120,
                )
                output = result.stdout.strip()
                try:
                    parsed_output = json.loads(output)
                except json.JSONDecodeError:
                    parsed_output = None
                self._json({
                    "claim_id": claim_id,
                    "raw": output,
                    "parsed": parsed_output,
                    "stderr": result.stderr.strip()[-500:] if result.stderr else "",
                    "returncode": result.returncode,
                })
            except subprocess.TimeoutExpired:
                self._json({"error": "timeout — agent took > 120s"}, status=504)
            except Exception as exc:
                self._json({"error": str(exc)}, status=500)
            return

        self._json({"error": "not found"}, status=404)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, msg: str, status: int = 200):
        body = msg.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        path = args[0].split(" ")[1] if " " in args[0] else args[0]
        print(f"  {args[1]}  {path}")


if __name__ == "__main__":
    if not PYTHON.exists():
        print(f"ERROR: .venv not found — run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'")
        sys.exit(1)
    server = HTTPServer(("localhost", PORT), DemoHandler)
    print(f"\n  Demo server ready")
    print(f"  ┌─────────────────────────────────────────┐")
    print(f"  │  Open:  http://localhost:{PORT}            │")
    print(f"  └─────────────────────────────────────────┘")
    print(f"\n  Routes:")
    print(f"    /                   → presentation.html")
    print(f"    /run?claim=CLM-001  → run agent on a claim")
    print(f"    /health             → server status")
    print(f"\n  Ctrl-C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
