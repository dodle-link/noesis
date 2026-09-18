# Noesis Pixel Website Experiment v1.4.0

This folder contains an experimental website mockup for exploring how the Noesis pixel can be integrated into a web experience.

## Purpose

- Test how Noesis pixel concepts can be presented in a website format
- Explore layout, navigation, and interaction ideas for a browser-based experience
- Provide a simple sandbox for experimentation only

## Important Notes

- All pages, text, images, and booking-style flows in this folder are mockups
- The content is for experimental and demonstration purposes only
- Nothing in this folder should be treated as production-ready or as real website content

## Noe Pixel

The web pages use a separate Noe pixel instance from the main `noe-ui/index.html`
page. The shared behavior is loaded through `js/noe-pixel.js`, which reuses
`../brain/limbric.js` and mounts the pixel in the shared footer.

The web pages do not load `brain/energy.js`, so this instance keeps the visual
pixel behavior without energy logic.

## Local Preview

Serve the `noe-ui` folder over HTTP so the manifest and shared pixel script can
load correctly. Opening `web/index.html` directly with `file://` will trigger
browser security and CORS errors.

From the repository root:

```bash
python3 -m http.server 8000 -d noe-ui
```

Then open:

```text
http://localhost:8000/web/index.html
```

## Folder Contents

- `index.html` and related pages for the mock website flow
- `css/` for styling
- `js/` for frontend interactions
- `img/` and favicon assets for visual presentation
