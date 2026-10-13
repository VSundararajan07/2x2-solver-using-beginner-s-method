
import json
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from cube2x2_solver import Cube, FACE_ORDER, Solver

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    allowed_files = {"app.js", "style.css"}
    if filename in allowed_files:
        return send_from_directory(ROOT, filename)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/solve", methods=["GET", "POST"])
def solve():
    if request.method == "GET":
        return jsonify({
            "status": "ok",
            "message": "2x2 cube solver API is running."
        })

    try:
        payload = request.get_json(force=True)
        faces = payload.get("faces")

        if not isinstance(faces, dict):
            raise ValueError("Missing cube faces.")

        normalized = {}
        for face in FACE_ORDER:
            grid = faces.get(face)
            if not isinstance(grid, list) or len(grid) != 2:
                raise ValueError(f"{face} must contain 2 rows.")
            if any(not isinstance(row, list) or len(row) != 2 for row in grid):
                raise ValueError(f"{face} must be a 2x2 grid.")
            normalized[face] = [
                [str(c).strip().upper() for c in row]
                for row in grid
            ]

        cube = Cube.from_faces(normalized)
        initial = cube.copy()
        stages = Solver(cube).solve()
        steps = [
            (stage, move)
            for stage, moves in stages.items()
            for move in moves
        ]

        states = [initial.to_faces()]
        working = initial.copy()

        for _stage, move in steps:
            working.apply(move)
            states.append(working.to_faces())

        result = {
            "stages": [
                {"name": name, "moves": moves}
                for name, moves in stages.items()
            ],
            "steps": [
                {"stage": stage, "move": move}
                for stage, move in steps
            ],
            "states": states,
            "solved": working.is_solved(),
            "alreadySolved": len(steps) == 0,
            "totalMoves": sum(
                1 for _, move in steps if move[0] != "y"
            ),
        }
        return jsonify(result)

    except (ValueError, RuntimeError, KeyError, StopIteration, TypeError) as exc:
        return jsonify({"error": str(exc) or "Invalid cube input."}), 400
    except Exception:
        app.logger.exception("Unexpected solver error")
        return jsonify({
            "error": "Unexpected server error while solving the cube."
        }), 500
