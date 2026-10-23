# 2×2 Cube Solver

A browser-based version of the Python 2×2 beginner-method solver. The solver logic in `cube2x2_solver.py` is reused; the Matplotlib desktop viewer is replaced by a Three.js web viewer.

## Notes

- The UI starts with a solved cube. Choose the colour for each of the 24 stickers, then click **Find solution**.
- The backend validates and solves using the existing beginner-method solver.
- The 3D viewer supports orbit/zoom and step-by-step playback. The sticker colours update at each move state; this version does not animate the physical quarter-turn between states.
- Three.js and Google Fonts are loaded from public CDNs, so the browser needs internet access.
