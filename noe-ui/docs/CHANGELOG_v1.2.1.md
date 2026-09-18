# Changelog for v1.2.1

## Major Changes
- Updated version from v1.2.0 to v1.2.1
- Removed the energy cube "rescue" behavior so cubes no longer chase Noe
  when it runs out of energy - Noe must reach a cube on its own to recharge
- Noe's death-state twitches now flounder toward the nearest energy cube
  instead of moving randomly, giving it a real chance to survive only if
  it struggles close enough before fading out

## Previous Changes (v1.2.0)
- Added the "Noe's Energy Surge" arcade game (`game/`), a synthetic-survival
  mini-game featuring Noe's pixel, energy cubes, rainbow power-ups, and
  entropy glitches
- Removed the page scrollbar on the game screen by locking `html`/`body`
  overflow and switching the layout to a fixed `100vh` height
- Prevented arrow keys, `WASD`, and `Space` from scrolling the browser
  window while playing, so gameplay input no longer fights the page
- Made the game header and modal screens wrap gracefully on narrow
  viewports instead of overflowing
- Added responsive breakpoints for small phones and short/landscape
  viewports, and adjusted the play field aspect ratio for portrait phones
- Refactored game and GitHub links in `index.html` for improved readability
