/**
 * CRT Effect for Synthetic Conscious Pixel
 * This script adds CRT (Cathode Ray Tube) visual effects to the pixel
 */

document.addEventListener('DOMContentLoaded', () => {
  // Get the noesis logo element
  const pixel = document.getElementById('noesis-logo');
  
  // Add CRT container and effect elements
  setupCrtEffect(pixel);
  
  // Initialize the CRT effect with startup animation
  initializeCrtEffect();
  
  // Set up toggle switch functionality
  setupToggleSwitch();
});

/**
 * Sets up the CRT effect structure for the pixel
 * @param {HTMLElement} pixelElement - The pixel element to apply CRT effect to
 */
function setupCrtEffect(pixelElement) {
  // Store original content
  const originalContent = pixelElement.innerHTML;
  
  // Create CRT structure
  pixelElement.innerHTML = `
    <div class="crt-screen"></div>
    <div class="crt-scanlines"></div>
    <div class="crt-vignette"></div>
    <div class="crt-rgb-shift"></div>
    ${originalContent}
  `;
  
  // Add CRT classes
  pixelElement.classList.add('crt-enabled');
  pixelElement.classList.add('crt-startup');
  
  // Remove startup class after animation completes
  setTimeout(() => {
    pixelElement.classList.remove('crt-startup');
  }, 2000);
}

/**
 * Initializes the CRT effect with RGB shift and occasional glitches
 */
function initializeCrtEffect() {
  // Apply RGB shift effect
  applyRgbShift();
  
  // Add occasional glitches
  setInterval(triggerRandomGlitch, 8000 + Math.random() * 10000);
}

/**
 * Applies RGB color shift effect (chromatic aberration)
 */
function applyRgbShift() {
  const rgbShiftElement = document.querySelector('.crt-rgb-shift');
  if (!rgbShiftElement) return;
  
  // Initial RGB shift
  updateRgbShift(rgbShiftElement);
  
  // Continuously update RGB shift
  setInterval(() => {
    updateRgbShift(rgbShiftElement);
  }, 100 + Math.random() * 200);
}

/**
 * Updates the RGB shift effect with small random variations
 * @param {HTMLElement} element - The RGB shift element to update
 */
function updateRgbShift(element) {
  // Get small random shift amounts
  const redShift = (Math.random() * 2 - 1) * 2;  // -2px to 2px
  const greenShift = (Math.random() * 2 - 1) * 2;
  const blueShift = (Math.random() * 2 - 1) * 2;
  
  // Apply shadow filter for RGB shift
  element.style.boxShadow = `
    ${redShift}px 0 2px rgba(255, 0, 0, 0.5),
    ${greenShift}px 0 2px rgba(0, 255, 0, 0.5),
    ${blueShift}px 0 2px rgba(0, 0, 255, 0.5)
  `;
}

/**
 * Triggers a random CRT glitch effect
 */
function triggerRandomGlitch() {
  const pixel = document.getElementById('noesis-logo');
  if (!pixel) return;
  
  // Determine glitch type
  const glitchType = Math.floor(Math.random() * 3);
  
  switch (glitchType) {
    case 0:
      // Horizontal shift glitch
      horizontalShiftGlitch(pixel);
      break;
    case 1:
      // Vertical sync glitch
      verticalSyncGlitch(pixel);
      break;
    case 2:
      // Flicker glitch
      flickerGlitch(pixel);
      break;
  }
}

/**
 * Creates a horizontal shift glitch effect
 * @param {HTMLElement} element - The element to apply the glitch to
 */
function horizontalShiftGlitch(element) {
  // Add glitch class
  element.classList.add('h-glitch');
  
  // Set random shift amount
  element.style.transform = `translateX(${(Math.random() * 10 - 5)}px)`;
  
  // Remove glitch after short duration
  setTimeout(() => {
    element.classList.remove('h-glitch');
    element.style.transform = '';
  }, 120 + Math.random() * 80);
}

/**
 * Creates a vertical sync glitch effect
 * @param {HTMLElement} element - The element to apply the glitch to
 */
function verticalSyncGlitch(element) {
  // Add more pronounced scanlines temporarily
  const scanlines = document.querySelector('.crt-scanlines');
  if (scanlines) {
    scanlines.style.opacity = '0.9';
    scanlines.style.backgroundSize = '100% 3px';
    
    // Return to normal after glitch
    setTimeout(() => {
      scanlines.style.opacity = '0.7';
      scanlines.style.backgroundSize = '';
    }, 200 + Math.random() * 100);
  }
  
  // Add vertical shift
  element.style.transform = `translateY(${(Math.random() * 8 - 4)}px)`;
  
  // Remove vertical shift
  setTimeout(() => {
    element.style.transform = '';
  }, 150 + Math.random() * 50);
}

/**
 * Creates a flicker glitch effect
 * @param {HTMLElement} element - The element to apply the glitch to
 */
function flickerGlitch(element) {
  let flickerCount = 3 + Math.floor(Math.random() * 3);
  let flickerDelay = 50;
  
  // Create flicker effect by toggling opacity
  const flickerInterval = setInterval(() => {
    element.style.opacity = (flickerCount % 2 === 0) ? '0.7' : '1';
    flickerCount--;
    
    if (flickerCount <= 0) {
      clearInterval(flickerInterval);
      element.style.opacity = '';
    }
  }, flickerDelay);
}

/**
 * Sets up the CRT effect toggle switch functionality
 */
function setupToggleSwitch() {
  const toggleSwitch = document.getElementById('crt-toggle');
  if (!toggleSwitch) return;
  
  // Handle toggle change
  toggleSwitch.addEventListener('change', function() {
    // Reverse the logic - CRT effect is ON when toggle is OFF
    toggleCrtEffect(!this.checked);
  });
  
  // Initialize with CRT effect ON by default (since toggle is OFF by default)
  toggleCrtEffect(true);
}

/**
 * Toggles the CRT effect on or off
 * @param {boolean} enabled - Whether the CRT effect should be enabled
 */
function toggleCrtEffect(enabled) {
  const pixel = document.getElementById('noesis-logo');
  const wrapper = document.querySelector('.wrapper');
  
  if (enabled) {
    // Enable CRT effect
    pixel.classList.add('crt-enabled');
    wrapper.classList.add('crt-container');
    
    // Add startup animation
    pixel.classList.add('crt-startup');
    setTimeout(() => {
      pixel.classList.remove('crt-startup');
    }, 2000);
    
    // Show CRT elements
    document.querySelectorAll('.crt-screen, .crt-scanlines, .crt-vignette, .crt-rgb-shift').forEach(element => {
      if (element) element.style.display = '';
    });
    
    // Note: Audio will be handled by audio-player.js via the toggle's change event
    
  } else {
    // Disable CRT effect
    pixel.classList.remove('crt-enabled');
    wrapper.classList.remove('crt-container');
    
    // Hide CRT elements
    document.querySelectorAll('.crt-screen, .crt-scanlines, .crt-vignette, .crt-rgb-shift').forEach(element => {
      if (element) element.style.display = 'none';
    });
    
    // Note: Audio will be handled by audio-player.js via the toggle's change event
  }
}
