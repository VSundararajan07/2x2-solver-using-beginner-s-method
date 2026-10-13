import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Ensure the project root is importable in Vercel's Python function runtime.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cube2x2_solver import Cube, FACE_ORDER, Solver  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            faces = payload.get("faces")
            if not isinstance(faces, dict):
                raise ValueError("Missing cube faces.")

            # Normalize and validate the 6 face grids.
            normalized = {}
            for face in FACE_ORDER:
                grid = faces.get(face)
                if not isinstance(grid, list) or len(grid) != 2:
                    raise ValueError(f"{face} must contain 2 rows.")
                if any(not isinstance(row, list) or len(row) != 2 for row in grid):
                    raise ValueError(f"{face} must be a 2x2 grid.")
                normalized[face] = [[str(c).strip().upper() for c in row] for row in grid]

            cube = Cube.from_faces(normalized)
            initial = cube.copy()
            stages = Solver(cube).solve()
            steps = [(stage, move) for stage, moves in stages.items() for move in moves]

            states = [initial.to_faces()]
            working = initial.copy()
            for _stage, move in steps:
                working.apply(move)
                states.append(working.to_faces())

            result = {
                "stages": [{"name": name, "moves": moves} for name, moves in stages.items()],
                "steps": [{"stage": stage, "move": move} for stage, move in steps],
                "states": states,
                "solved": working.is_solved(),
                "alreadySolved": len(steps) == 0,
                "totalMoves": sum(1 for _, move in steps if move[0] != "y"),
            }
            self._send(200, result)
        except (ValueError, RuntimeError, KeyError, StopIteration, TypeError) as exc:
            self._send(400, {"error": str(exc) or "Invalid cube input."})
        except Exception:
            self._send(500, {"error": "Unexpected server error while solving the cube."})

    def do_GET(self):
        self._send(200, {"status": "ok", "message": "2x2 cube solver API is running."})

    def _send(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
