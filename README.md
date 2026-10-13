# 2×2 Cube Solver

A browser-based version of the Python 2×2 beginner-method solver. The solver logic in `cube2x2_solver.py` is reused; the Matplotlib desktop viewer is replaced by a Three.js web viewer.

## Run locally

Requirements: Python 3.10+ and Node.js/npm (for the Vercel CLI).

1. Install the Vercel CLI: `npm install -g vercel`
2. From this project folder, run: `vercel dev`
3. Open the local URL printed by Vercel.

The browser UI is in `public/`; the Python API endpoint is `api/solve.py`.

## Deploy

1. Create a GitHub repository and upload the contents of this folder (not the ZIP itself).
2. In Vercel, choose **Add New → Project** and import that repository.
3. Keep the default project settings and deploy. Vercel serves `public/` as static files and `api/solve.py` as a Python Function.
4. Open the generated `.vercel.app` URL.

## Notes

- The UI starts with a solved cube. Choose the colour for each of the 24 stickers, then click **Find solution**.
- The backend validates and solves using the existing beginner-method solver.
- The 3D viewer supports orbit/zoom and step-by-step playback. The sticker colours update at each move state; this version does not animate the physical quarter-turn between states.
- Three.js and Google Fonts are loaded from public CDNs, so the browser needs internet access.
