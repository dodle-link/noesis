# Changelog for v1.4.0

## Major Changes
- Updated Noe UI from v1.3.1 to v1.4.0
- Added a separate Noe pixel experience for the experimental web pages in
  `web/`, while keeping the main `index.html` pixel independent
- Reused the canonical pixel behavior from `brain/limbric.js` through the
  `web/js/noe-pixel.js` loader
- Mounted the web pixel in the shared footer and kept its visual styling
  consistent with the main Noe pixel
- Kept the web pixel independent from energy logic by not loading
  `brain/energy.js`
- Made web pixel startup work when the shared script is loaded dynamically and
  when the optional Noesis API is unavailable

## Web Preview
- Web pages must be served over HTTP instead of opened directly with `file://`
  so the manifest and shared scripts can load correctly
- From the repository root, run:

  ```bash
  python3 -m http.server 8000 -d noe-ui
  ```

- Open `http://localhost:8000/web/index.html` in a browser

## Previous Changes (v1.3.1)
- Added a self-modifying cognition loop wired into the conscious pixel's own
  state in `brain/limbric.js`
- The loop controls a `pulseMultiplier` on the pixel that is read every frame
  by `processMouseInteractions()`
