"""
Lightweight demo server for the live demo slide in presentation.html.

Runs the claims agent on demand and returns JSON output to the browser.
The presentation makes fetch() calls to this server when the Run buttons are clicked.

Usage:
    source .env
    .venv/bin/python scripts/demo_server.py        # default port 7331
    .venv/bin/python scripts/demo_server.py 8080   # custom port

Then open presentation.html and click any "▶ Run" button on slide 05.

Owner: Track A (Fabio)
"""
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7331
ROOT = Path(__file__).parent.parent          # repo root
PYTHON = ROOT / ".venv" / "bin" / "python"  # venv python


class DemoHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self._cors()
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._json({"status": "ok", "port": PORT})
            return

        if parsed.path == "/run":
            claim_id = parse_qs(parsed.query).get("claim", ["CLM-001"])[0]
            # Basic validation — only allow known claim_id patterns
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

    def log_message(self, fmt, *args):
        claim = args[0].split("claim=")[-1].split(" ")[0] if "claim=" in args[0] else ""
        tag = f"  [{claim}]" if claim else ""
        print(f"  {args[1]}{tag}")


if __name__ == "__main__":
    if not PYTHON.exists():
        print(f"ERROR: venv not found at {PYTHON}")
        print("Run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'")
        sys.exit(1)
    server = HTTPServer(("localhost", PORT), DemoHandler)
    print(f"Demo server → http://localhost:{PORT}")
    print(f"  /run?claim=CLM-001   process a claim")
    print(f"  /health              check server is alive")
    print("  Ctrl-C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
