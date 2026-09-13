# Changelog for v1.2.0

## Major Changes
- Updated version from v1.1.0 to v1.2.0
- Added the "Noe's Energy Surge" arcade game (`game/`), a synthetic-survival
  mini-game featuring Noe's pixel, energy cubes, rainbow power-ups, and
  entropy glitches

## Game Page Fixes
- Removed the page scrollbar on the game screen by locking `html`/`body`
  overflow and switching the layout to a fixed `100vh` height
- Prevented arrow keys, `WASD`, and `Space` from scrolling the browser
  window while playing, so gameplay input no longer fights the page
- Made the game header and modal screens wrap gracefully on narrow
  viewports instead of overflowing
- Added responsive breakpoints for small phones and short/landscape
  viewports, and adjusted the play field aspect ratio for portrait phones

## Other Improvements
- Refactored game and GitHub links in `index.html` for improved readability

## Previous Changes (v1.1.0)
- Modified pixel behavior so energy level no longer affects movement speed
- Visual effects (glow, pulsing, color changes) still respond to energy levels
- Maintained energy-seeking behavior when pixel's energy is low
- Preserved "fear of death" behavior when energy is critically low
- Updated directory reference in documentation from `/js-code` to `/brain`
- Optimized code for better performance
- Fixed minor visual glitches
