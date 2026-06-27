# Changelog for v1.1.0

## Major Changes
- Updated version from v1.0.0 to v1.1.0
- Modified pixel behavior so energy level no longer affects movement speed

## Energy System Features
- Pixel's movement speed remains consistent regardless of energy level
- Visual effects (glow, pulsing, color changes) still respond to energy levels
- Maintained energy-seeking behavior when pixel's energy is low
- Preserved "fear of death" behavior when energy is critically low

## Other Improvements
- Updated directory reference in documentation from `/js-code` to `/brain`
- Optimized code for better performance
- Fixed minor visual glitches

## Previous Changes (v1.0.0)
- Added global energy system via `window.noeEnergy`
- Implemented energy transfer between cubes and pixel through proximity
- Added visual indicators (glow effects, connections) for energy transfer
- Added floating animation to energy cubes with orbital patterns
- Added death state visual and behavioral effects when energy reaches zero
- Energy decay rate set to approximately 1% per second
- Energy cube configuration using a single cube that floats freely across the website
- Enhanced visual feedback for energy states
- Added more organic movement patterns for energy cube
- Improved pixel responsiveness to energy levels
- Added feedback mechanisms for the energy system
