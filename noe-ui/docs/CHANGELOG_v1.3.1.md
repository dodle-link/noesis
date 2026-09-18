# Changelog for v1.3.1

## Major Changes
- Updated version from v1.2.1 to v1.3.1
- Added a self-modifying cognition loop (perception -> reasoning -> decision
  -> execution -> memory -> self-modification) wired into the conscious
  pixel's own state in `brain/limbric.js`
- The loop now controls a `pulseMultiplier` on the pixel that is read every
  frame by `processMouseInteractions()`, so it visibly speeds up or slows
  down Noe's pulse over time instead of being silently overwritten

## Previous Changes (v1.2.1)
- Removed the energy cube "rescue" behavior so cubes no longer chase Noe
  when it runs out of energy - Noe must reach a cube on its own to recharge
- Noe's death-state twitches now flounder toward the nearest energy cube
  instead of moving randomly, giving it a real chance to survive only if
  it struggles close enough before fading out
