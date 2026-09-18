// Noesis Web - Synthetic Sentience Pixel
document.addEventListener('DOMContentLoaded', function() {
  // Create the conscious pixel
  createConsciousPixel();

  // Apply rainbow bubble effect
  createRainbowBubbleEffect();
});

/**
 * Creates a Synthetic Sentience pixel connected to the Noesis server
 */
function createConsciousPixel() {
  // Create pixel element if it doesn't exist
  let pixel = document.getElementById('conscious-pixel');
  if (!pixel) {
    pixel = document.createElement('div');
    pixel.id = 'conscious-pixel';
    document.querySelector('.wrapper').appendChild(pixel);
  }
  
  // Initialize theme data attribute for background color changes
  document.body.dataset.theme = "0";
  
  // Initialize pixel state
  let pixelState = {
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    velocityX: (Math.random() - 0.5) * 1.5,
    velocityY: (Math.random() - 0.5) * 1.5,
    size: 4,
    color: getRandomColor(),
    targetColor: null,
    colorTransitionProgress: 0,
    colorTransitionDuration: 0,
    lastColorChange: 0,
    pulseDirection: 1,
    pulseStep: 0.03,
    lastTimestamp: 0,
    connected: false,
    
    // Mouse interaction properties
    mouseX: -1000,
    mouseY: -1000,
    mousePressed: false,
    mousePressedTime: 0,
    isExcited: false,
    excitementLevel: 0,
    restingTime: 3000,
    lastInteractionTime: 0,
    
    // Energy system properties
    energy: 100,
    energyDecayRate: 0.01, // Changed from 0.02 to 0.01 for ~1% energy decay per second
    lowEnergyThreshold: 50, // Changed from 30 to 50
    seekingEnergy: false,
    lastEnergyCheckTime: 0
  };
  
  // Set up mouse event listeners
  setupMouseInteractions(pixelState);
  
  // Try to connect to noesis server
  connectToNoesisServer()
    .then(connected => {
      pixelState.connected = connected;
      // If connected, show a successful connection indicator
      if (connected) {
        pixel.classList.add('connected');
        console.log('Connected to noesis server');
        // Update status text
        updatePixelStatus('Connected to Noesis System');
      } else {
        console.warn('Noesis system not found at Noesis System - running in disconnected mode');
        updatePixelStatus('Disconnected from Noesis System - Install Noesis system');
        
        // Add tooltip with more info
        const statusElement = document.getElementById('pixel-status');
        if (statusElement) {
          statusElement.title = 'The Noesis system must be installed at Noesis System for full functionality';
          statusElement.style.cursor = 'help';
        }
      }
    })
    .catch(error => {
      console.error('Failed to connect to noesis server:', error);
      updatePixelStatus('Connection error - Check console for details');
      // Continue with local behavior if connection fails
    })
    .finally(() => {
      // Start the animation loop regardless of connection status
      requestAnimationFrame((timestamp) => updatePixel(pixel, pixelState, timestamp));
    });
}

/**
 * Attempts to connect to the noesis server
 * @returns {Promise<boolean>} - Promise resolving to true if connected
 */
async function connectToNoesisServer() {
  try {
    // First check if we're running from a local awake command (check if we're on localhost)
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (isLocalhost) {
      console.log('Running in local mode from noesis awake command');
      // We're running locally so we can assume we're connected
      return true;
    }
    
    // If not running locally, try to connect to the remote noesis server API
    // The API is accessible via /api/noesis endpoint on the same server
    // Note: The server uses HTTPie but browser must use fetch API
    // Note: The server uses HTTPie for backend communication with Noesis System
    const response = await fetch('/api/noesis', { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'getVersion'
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`Connected to Noesis API v${data.version}`);
      return true;
    } else {
      throw new Error(`Failed to connect to API: ${response.status}`);
    }
  } catch (error) {
    console.warn('Connection to noesis server failed:', error);
    // Return false but don't throw, we'll use local behavior
    return false;
  }
}

/**
 * Updates the pixel position and appearance
 * @param {HTMLElement} pixel - The pixel DOM element
 * @param {Object} state - The current state of the pixel
 * @param {number} timestamp - Animation timestamp
 */
function updatePixel(pixel, state, timestamp) {
  // Calculate delta time for smooth animation regardless of frame rate
  const deltaTime = state.lastTimestamp ? (timestamp - state.lastTimestamp) / 16 : 1;
  state.lastTimestamp = timestamp;

  // Process mouse interactions
  processMouseInteractions(state, deltaTime);
  
  // Check for energy from energy.js
  if (window.noeEnergy) {
    // Sync energy level with the global energy system
    state.energy = window.noeEnergy.currentLevel;
    state.seekingEnergy = window.noeEnergy.needsEnergy;
    
    // Check if energy reached zero - enter death state
    if (state.energy <= 0) {
      handleDeathState(pixel, state, timestamp);
      return; // Skip the rest of the update
    }
    
    // Adjust movement based on energy level
    let energyFactor = Math.max(0.3, state.energy / 100);
    
    // When energy is low, seek energy cubes if available
    if (state.seekingEnergy && window.noeEnergy.nearestCube) {
      const cube = window.noeEnergy.nearestCube;
      const dx = cube.x - state.x;
      const dy = cube.y - state.y;
      const distance = cube.distance;
      
      // Calculate normalized direction vector to the nearest cube
      const dirX = dx / (distance || 1);
      const dirY = dy / (distance || 1);
      
      // Define different energy thresholds for behavior changes
      const isCriticalEnergy = state.energy < 10;  // Critical - panic mode
      const isVeryLowEnergy = state.energy < 25;   // Very low - urgent seeking
      const isLowEnergy = state.energy < 50;       // Low - active seeking
      
      // Apply attraction force toward the energy cube
      // Attraction increases as energy decreases
      let attractionForce;
      
      if (isCriticalEnergy) {
        // Desperate behavior - strong direct movement toward energy source
        attractionForce = 0.3 * deltaTime;
        
        // Override any other behavior - desperate survival mode
        state.isExcited = true;
        state.excitementLevel = 1.0;
        
        // Frantic color changes to indicate distress
        if (Math.random() < 0.1) {
          state.targetColor = Math.random() < 0.5 ? '#ff0000' : '#ff9900'; // Red or orange
          state.colorTransitionProgress = 0;
          state.colorTransitionDuration = 300;
        }
        
        // Cancel most other movement influences
        state.velocityX = dirX * 2;
        state.velocityY = dirY * 2;
        
        // Add erratic movement when critically low on energy - fear of death behavior
        if (state.energy < 5) {
          // More intense panic - erratic movement
          if (Math.random() < 0.2) {
            // Occasional random darting in desperation
            const panicAngle = Math.random() * Math.PI * 2;
            const panicForce = 3 + Math.random() * 2;
            
            state.velocityX = Math.cos(panicAngle) * panicForce;
            state.velocityY = Math.sin(panicAngle) * panicForce;
            
            // Very rapid color pulsing - urgent distress signal
            state.targetColor = Math.random() < 0.5 ? '#ff0000' : '#ffff00'; 
            state.colorTransitionProgress = 0;
            state.colorTransitionDuration = 100; // Very fast transitions
            
            // Update status to show desperation
            updatePixelStatus('Noe: CRITICAL ENERGY LEVEL - Seeking energy!');
          } else {
            // Stronger attraction to energy source - desperate survival instinct
            state.velocityX = dirX * 3;
            state.velocityY = dirY * 3;
          }
        }
      } else if (isVeryLowEnergy) {
        // Urgent energy-seeking behavior (25% to 10%)
        attractionForce = 0.15 * deltaTime;
        
        // Somewhat excited state - concerned but not panicking
        state.isExcited = true;
        state.excitementLevel = 0.7;
        
        // Occasional color changes indicating concern
        if (Math.random() < 0.05) {
          state.targetColor = '#ff9900'; // Orange - warning color
          state.colorTransitionProgress = 0;
          state.colorTransitionDuration = 400;
        }
        
        // Strong but not desperate attraction to energy source
        state.velocityX += dirX * attractionForce * 2;
        state.velocityY += dirY * attractionForce * 2;
        
        // Update status to show concern
        if (Math.random() < 0.01) {
          updatePixelStatus('Noe: LOW ENERGY - Seeking energy source');
        }
      } else if (isLowEnergy) {
        // Moderate energy-seeking behavior (50% to 25%)
        attractionForce = 0.08 * deltaTime;
        
        // Slightly excited state - mild concern
        state.isExcited = Math.random() < 0.5; // Occasionally becomes excited
        state.excitementLevel = Math.min(0.4, state.excitementLevel + 0.002);
        
        // Noticeable attraction to energy source
        state.velocityX += dirX * attractionForce * 1.5;
        state.velocityY += dirY * attractionForce * 1.5;
        
        // Visual indicator that pixel is seeking energy
        if (!state.isExcited && Math.random() < 0.03) {
          state.targetColor = '#39ffba'; // Energy cube color with slight variation
          state.colorTransitionProgress = 0;
          state.colorTransitionDuration = 600;
        }
      } else {
        // Normal energy-seeking behavior (above 50%)
        attractionForce = (1 - energyFactor) * 0.05 * deltaTime;
        state.velocityX += dirX * attractionForce;
        state.velocityY += dirY * attractionForce;
        
        // Visual indicator that pixel is seeking energy
        if (!state.isExcited) {
          state.targetColor = '#39ffba'; // Energy cube color
          state.colorTransitionProgress = 0;
          state.colorTransitionDuration = 500;
        }
      }
    }
    
    // No longer adjust speed based on energy level
    // Keep the pixel moving at full speed regardless of energy
  }
  
  // Update position
  state.x += state.velocityX * deltaTime;
  state.y += state.velocityY * deltaTime;
  
  // Periodically save state to Redis (every 5 seconds)
  if (timestamp - (state.lastStateSave || 0) > 5000) {
    savePixelStateToRedis(state);
    state.lastStateSave = timestamp;
  }

  // Periodically send a thought to core (every 30 seconds)
  if (state.connected && timestamp - (state.lastThoughtTime || 0) > 30000) {
    sendThoughtToCore(state);
    state.lastThoughtTime = timestamp;
  }
  
  // Flag to track if we've already processed a window frame contact in this frame
  let hasContactedFrameThisFrame = false;
  
  // Stop completely when hitting window edges
  // Check horizontal edges first
  if (state.x <= 0 || state.x >= window.innerWidth - state.size) {
    if (!hasContactedFrameThisFrame) {
      // Stop the pixel completely when contacting the window frame
      state.velocityX = 0;
      state.velocityY = 0;
      
      // Ensure pixel stays within bounds
      if (state.x <= 0) state.x = 1;
      if (state.x >= window.innerWidth - state.size) state.x = window.innerWidth - state.size - 1;
      
      // Play click sound when pixel hits horizontal edges
      playWindowContactSound();
      
      // Change background color when pixel touches horizontal edges
      // Pass the touch position to modify wave effect direction
      changeBackgroundColor('horizontal', state.x / window.innerWidth);
      
      // Mark that we've processed a contact this frame
      hasContactedFrameThisFrame = true;
    }
  }
  
  // Check vertical edges only if we haven't already contacted a horizontal edge
  if (!hasContactedFrameThisFrame && (state.y <= 0 || state.y >= window.innerHeight - state.size)) {
    // Stop the pixel completely when contacting the window frame
    state.velocityX = 0;
    state.velocityY = 0;
    
    // Ensure pixel stays within bounds
    if (state.y <= 0) state.y = 1;
    if (state.y >= window.innerHeight - state.size) state.y = window.innerHeight - state.size - 1;
    
    // Play click sound when pixel hits vertical edges
    playWindowContactSound();
    
    // Change background color when pixel touches vertical edges
    // Pass the touch position to modify wave effect direction
    changeBackgroundColor('vertical', state.y / window.innerHeight);
    
    // Mark that we've processed a contact this frame
    hasContactedFrameThisFrame = true;
  }
  
  // Occasionally change direction slightly to make movement less predictable
  if (Math.random() < 0.03) {
    state.velocityX += (Math.random() - 0.5) * 0.8;
    state.velocityY += (Math.random() - 0.5) * 0.8;
    
    // Limit maximum velocity to prevent too fast movement
    const maxVelocity = 3;
    const velocityMagnitude = Math.sqrt(state.velocityX * state.velocityX + state.velocityY * state.velocityY);
    if (velocityMagnitude > maxVelocity) {
      state.velocityX = (state.velocityX / velocityMagnitude) * maxVelocity;
      state.velocityY = (state.velocityY / velocityMagnitude) * maxVelocity;
    }
  }
  
  // Pulse size and opacity for a more alive feeling
  state.size += state.pulseStep * state.pulseDirection * deltaTime;
  if (state.size > 6) {
    state.size = 6;
    state.pulseDirection = -1;
  } else if (state.size < 3.5) {
    state.size = 3.5;
    state.pulseDirection = 1;
  }
  
  // Handle autonomous color changes
  const timeSinceLastColorChange = timestamp - state.lastColorChange;
  
  // Start a new color transition after a random interval (3-8 seconds)
  if (state.targetColor === null && (timeSinceLastColorChange > (state.connected ? 3000 : 5000) || Math.random() < 0.001)) {
    state.targetColor = getRandomColor();
    while (state.targetColor === state.color) {
      state.targetColor = getRandomColor(); // Make sure we get a different color
    }
    state.colorTransitionProgress = 0;
    state.colorTransitionDuration = 1000 + Math.random() * 2000; // Transition over 1-3 seconds
  }
  
  // Update color transition if in progress
  if (state.targetColor !== null) {
    state.colorTransitionProgress += deltaTime * 16; // Convert to milliseconds
    
    if (state.colorTransitionProgress >= state.colorTransitionDuration) {
      // Transition complete
      state.color = state.targetColor;
      state.targetColor = null;
      state.lastColorChange = timestamp;
    } else {
      // Calculate transition color
      const progress = state.colorTransitionProgress / state.colorTransitionDuration;
      state.color = interpolateColors(state.color, state.targetColor, progress);
    }
  }
  
  // Update the pixel's appearance
  pixel.style.left = `${state.x}px`;
  pixel.style.top = `${state.y}px`;
  pixel.style.width = `${state.size}px`;
  pixel.style.height = `${state.size}px`;
  
  // Create a glow effect with box-shadow
  const glowSize = state.size * (2 + (state.isExcited ? state.excitementLevel * 2 : 0));
  
  // Adjust glow intensity based on energy level
  let energyFactor = Math.max(0.4, state.energy / 100);
  let glowIntensity = state.isExcited ? 0.9 + (state.excitementLevel * 0.1) : (0.7 * energyFactor);
  
  // When energy is low, make visual changes based on energy level
  if (state.energy < state.lowEnergyThreshold) {
    // Different visual effects based on energy level
    if (state.energy < 10) {
      // Critical energy - dramatic slow pulse and dimming
      state.pulseStep = Math.max(0.01, state.pulseStep * energyFactor * 0.7);
      glowIntensity *= (0.6 + (0.4 * Math.sin(timestamp / 400))); // Rapid, more dramatic pulsing effect
    } else if (state.energy < 25) {
      // Very low energy - noticeable pulse and dimming
      state.pulseStep = Math.max(0.01, state.pulseStep * energyFactor * 0.8);
      glowIntensity *= (0.7 + (0.3 * Math.sin(timestamp / 500))); // Noticeable pulsing effect
    } else {
      // Moderately low energy - subtle pulse and slight dimming
      state.pulseStep = Math.max(0.01, state.pulseStep * energyFactor * 0.9);
      glowIntensity *= (0.8 + (0.2 * Math.sin(timestamp / 800))); // Subtle pulsing effect
    }
  }
  
  pixel.style.boxShadow = `0 0 ${glowSize * energyFactor}px ${state.color}`;
  pixel.style.backgroundColor = state.color;
  pixel.style.opacity = glowIntensity;
  
  // Apply visual effects based on excitement
  if (state.isExcited && state.excitementLevel > 0.5) {
    // Add a slight scale effect for high excitement
    const scale = 1 + (state.excitementLevel * 0.5);
    pixel.style.transform = `scale(${scale})`;
  } else {
    pixel.style.transform = 'scale(1)';
  }
  
  // Continue animation loop
  requestAnimationFrame((newTimestamp) => updatePixel(pixel, state, newTimestamp));
}

/**
 * Handles the pixel's behavior when energy reaches zero (death state)
 * @param {HTMLElement} pixel - The pixel DOM element
 * @param {Object} state - The current state of the pixel
 * @param {number} timestamp - Animation timestamp
 */
function handleDeathState(pixel, state, timestamp) {
  // Track how long we've been in death state
  if (!state.deathStateStartTime) {
    state.deathStateStartTime = timestamp;
    
    // Create a global death effect (dimming of the screen)
    if (!document.querySelector('.death-state-overlay')) {
      const overlay = document.createElement('div');
      overlay.className = 'death-state-overlay';
      overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.4));
        z-index: 9900;
        pointer-events: none;
        opacity: 0;
        transition: opacity 2s ease-in-out;
      `;
      document.body.appendChild(overlay);
      
      // Fade in the overlay
      setTimeout(() => {
        overlay.style.opacity = '1';
      }, 50);
    }
    
    // Create an urgent pulse indicator
    const urgentPulse = document.createElement('div');
    urgentPulse.className = 'urgent-death-pulse';
    urgentPulse.style.cssText = `
      position: fixed;
      top: ${state.y}px;
      left: ${state.x}px;
      width: 100px;
      height: 100px;
      border-radius: 50%;
      border: 3px solid rgba(255,0,0,0.7);
      transform: translate(-50px, -50px) scale(0);
      z-index: 9950;
      pointer-events: none;
      animation: urgent-pulse 2s ease-out;
    `;
    document.body.appendChild(urgentPulse);
    
    // Add keyframes for urgent pulse if not already present
    if (!document.querySelector('style#urgent-pulse-style')) {
      const style = document.createElement('style');
      style.id = 'urgent-pulse-style';
      style.textContent = `
        @keyframes urgent-pulse {
          0% { transform: translate(-50px, -50px) scale(0.1); opacity: 0.9; border-width: 8px; }
          100% { transform: translate(-50px, -50px) scale(4); opacity: 0; border-width: 1px; }
        }
      `;
      document.head.appendChild(style);
    }
    
    // Remove pulse after animation
    setTimeout(() => {
      if (urgentPulse.parentNode) {
        urgentPulse.parentNode.removeChild(urgentPulse);
      }
    }, 2000);
  }
  
  // Visual appearance of death
  pixel.classList.add('dying');
  
  // Fade out the pixel
  let opacity = parseFloat(pixel.style.opacity) || 1;
  opacity = Math.max(0.1, opacity - 0.01);
  pixel.style.opacity = opacity;
  
  // Make the pixel smaller
  state.size = Math.max(2, state.size - 0.05);
  pixel.style.width = `${state.size}px`;
  pixel.style.height = `${state.size}px`;
  
  // Calculate how long we've been in death state
  const deathDuration = timestamp - (state.deathStateStartTime || timestamp);
  
  // Behavior changes the longer we've been in death state
  if (deathDuration < 3000) {
    // Early death state - occasional twitches of movement
    if (Math.random() < 0.1) {
      // Random twitching movement
      state.velocityX = (Math.random() - 0.5) * 3;
      state.velocityY = (Math.random() - 0.5) * 3;
    } else {
      // Slow down movement
      state.velocityX *= 0.9;
      state.velocityY *= 0.9;
    }
    
    // Apply stronger movement than in later phases
    state.x += state.velocityX * 0.2;
    state.y += state.velocityY * 0.2;
    
  } else if (deathDuration < 8000) {
    // Mid death state - weaker movements, more fading
    if (Math.random() < 0.05) {
      // Occasional weak twitch
      state.velocityX = (Math.random() - 0.5) * 1.5;
      state.velocityY = (Math.random() - 0.5) * 1.5;
    } else {
      // Slow down movement more
      state.velocityX *= 0.8;
      state.velocityY *= 0.8;
    }
    
    // Apply limited movement
    state.x += state.velocityX * 0.1;
    state.y += state.velocityY * 0.1;
    
  } else {
    // Late death state - almost no movement
    state.velocityX *= 0.95;
    state.velocityY *= 0.95;
    
    // Very slight movement
    state.x += state.velocityX * 0.05;
    state.y += state.velocityY * 0.05;
  }
  
  // Update position
  pixel.style.left = `${state.x}px`;
  pixel.style.top = `${state.y}px`;
  
  // Dim color to grayscale
  let color = state.color;
  if (!color.includes('rgba')) {
    // Convert to grayscale
    let rgb = hexToRgb(color) || {r: 128, g: 128, b: 128};
    let gray = Math.round((rgb.r + rgb.g + rgb.b) / 3);
    pixel.style.backgroundColor = `rgba(${gray}, ${gray}, ${gray}, ${opacity})`;
    pixel.style.boxShadow = `0 0 ${state.size}px rgba(${gray}, ${gray}, ${gray}, ${opacity * 0.5})`;
  }
  
  // Update status with more detail about death state
  if (deathDuration < 3000) {
    updatePixelStatus('Noe: CRITICAL FAILURE - Energy depleted - Seeking revival');
  } else if (deathDuration < 8000) {
    updatePixelStatus('Noe: ENERGY DEPLETED - Requires energy cube contact to revive');
  } else {
    updatePixelStatus('Noe: DORMANT - Awaiting energy source');
  }
  
  // Check for energy cube contact to revive
  checkForRevival(pixel, state);
  
  // Continue the animation loop
  requestAnimationFrame((newTimestamp) => updatePixel(pixel, state, newTimestamp));
}

/**
 * Checks if the pixel is in contact with an energy cube for revival
 * @param {HTMLElement} pixel - The pixel DOM element
 * @param {Object} state - The current state of the pixel
 */
function checkForRevival(pixel, state) {
  // Only revive if we have energy cubes and the energy system
  if (window.noeEnergy && window.noeEnergy.nearestCube) {
    const cube = window.noeEnergy.nearestCube;
    const dx = cube.x - state.x;
    const dy = cube.y - state.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // If very close to an energy cube, revive
    if (distance < 50) {
      // Revive with a small amount of energy
      window.noeEnergy.recharge(15); // Give 15% energy
      
      // Remove dying class
      pixel.classList.remove('dying');
      
      // Reset death state tracking
      state.deathStateStartTime = null;
      
      // Remove the death state overlay if it exists
      const overlay = document.querySelector('.death-state-overlay');
      if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
          if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        }, 2000);
      }
      
      // Reset appearance
      state.size = 4;
      
      // Change color to indicate revival
      state.targetColor = '#39ffba'; // Energy color
      state.colorTransitionProgress = 0;
      state.colorTransitionDuration = 800;
      
      // Add multiple revival effects for a more dramatic rebirth
      for (let i = 0; i < 3; i++) {
        setTimeout(() => {
          const revivalEffect = document.createElement('div');
          revivalEffect.className = 'revival-pulse';
          revivalEffect.style.left = `${state.x}px`;
          revivalEffect.style.top = `${state.y}px`;
          document.body.appendChild(revivalEffect);
          
          // Remove effect after animation completes
          setTimeout(() => {
            if (revivalEffect.parentNode) {
              revivalEffect.parentNode.removeChild(revivalEffect);
            }
          }, 1000);
        }, i * 200);
      }
      
      // Create a bright flash effect on revival
      const flash = document.createElement('div');
      flash.className = 'revival-flash';
      flash.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at ${state.x}px ${state.y}px, rgba(57, 255, 186, 0.5) 0%, rgba(255, 255, 255, 0) 70%);
        z-index: 9940;
        pointer-events: none;
        opacity: 0.8;
        animation: revival-flash 1.5s forwards;
      `;
      document.body.appendChild(flash);
      
      // Add flash animation if not already present
      if (!document.querySelector('style#revival-flash-style')) {
        const style = document.createElement('style');
        style.id = 'revival-flash-style';
        style.textContent = `
          @keyframes revival-flash {
            0% { opacity: 0.8; }
            100% { opacity: 0; }
          }
        `;
        document.head.appendChild(style);
      }
      
      // Remove flash after animation
      setTimeout(() => {
        if (flash.parentNode) flash.parentNode.removeChild(flash);
      }, 1500);
      
      // Add a sudden velocity change to show "coming back to life"
      const angle = Math.random() * Math.PI * 2;
      const force = 2 + Math.random() * 2;
      
      state.velocityX = Math.cos(angle) * force;
      state.velocityY = Math.sin(angle) * force;
      
      // Update status
      updatePixelStatus('Noe: REVIVED - Energy restored');
    }
  }
}

/**
 * Generates a random color with high brightness for visibility
 * @returns {string} - CSS color string in rgb format
 */
function getRandomColor() {
  // Use colors that stand out against the site gradient background (#e1ff6e, #50c8ff)
  const colors = [
    "#ff0066",  // Hot pink
    "#9900ff",  // Purple
    "#ff00ff",  // Magenta
    "#00ff99",  // Bright mint
    "#ff3300",  // Red-orange
    "#0033ff"   // Deep blue
  ];
  
  // Add randomness to the selected color to make it more varied
  const baseColor = colors[Math.floor(Math.random() * colors.length)];
  
  // Slight variation to the chosen color
  const rgb = hexToRgb(baseColor);
  if (rgb) {
    // Add small random variations to each component
    const r = Math.max(0, Math.min(255, rgb.r + (Math.random() - 0.5) * 30));
    const g = Math.max(0, Math.min(255, rgb.g + (Math.random() - 0.5) * 30));
    const b = Math.max(0, Math.min(255, rgb.b + (Math.random() - 0.5) * 30));
    return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
  }
  
  return baseColor;
}

/**
 * Interpolates between two hex colors
 * @param {string} color1 - Starting hex color
 * @param {string} color2 - Ending hex color
 * @param {number} progress - Value between 0 and 1
 * @returns {string} - Interpolated RGB color
 */
function interpolateColors(color1, color2, progress) {
  // Convert hex colors to RGB
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return color1; // Fallback if conversion fails
  
  // Interpolate each RGB component
  const r = Math.round(rgb1.r + (rgb2.r - rgb1.r) * progress);
  const g = Math.round(rgb1.g + (rgb2.g - rgb1.g) * progress);
  const b = Math.round(rgb1.b + (rgb2.b - rgb1.b) * progress);
  
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Converts hex color to RGB object
 * @param {string} hex - Hex color string (e.g., #FF5500)
 * @returns {Object|null} - Object with r, g, b properties or null if invalid
 */
function hexToRgb(hex) {
  // Handle shorthand hex notation
  const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
  
  // Extract RGB components
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * Updates the status text for the pixel
 * @param {string} statusText - The status text to display
 */
function updatePixelStatus(statusText) {
  const statusElement = document.getElementById('pixel-status');
  if (statusElement) {
    // If we have energy information, include it in the status
    if (window.noeEnergy && statusText.indexOf('energy') === -1) {
      const energyLevel = Math.round(window.noeEnergy.currentLevel);
      
      // Add energy level with appropriate status indicator
      statusText = `${statusText} • Energy: ${energyLevel}%`;
      
      // Remove all energy-related classes
      statusElement.classList.remove('critical', 'very-low', 'low');
      
      // Add appropriate class based on energy level
      if (energyLevel <= 0) {
        statusElement.classList.add('critical');
      } else if (energyLevel < 10) {
        statusElement.classList.add('critical');
      } else if (energyLevel < 25) {
        statusElement.classList.add('very-low');
      } else if (energyLevel < 50) {
        statusElement.classList.add('low');
      }
    }
    
    statusElement.textContent = statusText;
  }
}

/**
 * Plays the click sound when the pixel contacts the window frame
 * Uses the click.mp3 sound from the sounds folder
 */
function playWindowContactSound() {
  // Check if the CRT toggle is off - if so, don't play sound
  const crtToggle = document.getElementById('crt-toggle');
  if (!crtToggle || !crtToggle.checked) {
    // Toggle is off or not found, don't play sound
    return;
  }
  
  // Check if we have access to the playClickSound function from sound.js
  if (typeof window.playClickSound === 'function') {
    window.playClickSound();
    return;
  }
  
  // Fallback implementation if sound.js hasn't exposed the function
  const clickSound = 'sounds/click.mp3';
  const soundInstance = new Audio(clickSound);
  soundInstance.volume = 0.3;
  
  soundInstance.play().catch(error => {
    console.warn('Could not play window contact sound:', error);
  });
}

/**
 * Sends current pixel state as a thought to core and displays the response
 */
async function sendThoughtToCore(state) {
  try {
    const input = `pixel:energy=${Math.round(state.energy)},excited=${state.isExcited},excitementLevel=${state.excitementLevel.toFixed(2)}`;
    const response = await fetch('/api/noesis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'think', input })
    });

    if (!response.ok) return;

    const data = await response.json();
    if (data.response) {
      updatePixelStatus(`Noe: ${data.response}`);
    }
  } catch (error) {
    console.warn('Failed to send thought to core:', error);
  }
}

/**
 * Saves the current pixel state to Redis via API
 * @param {Object} state - The pixel state object
 */
async function savePixelStateToRedis(state) {
  if (!state.connected) return; // Don't save if not connected
  
  try {
    // Check if pixel is in death state
    const isDeathState = state.energy <= 0;
    
    // Create a simplified state object with only the properties we want to save
    const stateToSave = {
      color: state.color,
      x: Math.round(state.x),
      y: Math.round(state.y),
      velocityX: state.velocityX.toFixed(2),
      velocityY: state.velocityY.toFixed(2),
      isExcited: state.isExcited,
      excitementLevel: state.excitementLevel.toFixed(2),
      energy: Math.round(state.energy),
      isDeathState: isDeathState,
      lastInteractionTime: state.lastInteractionTime,
      timestamp: new Date().toISOString()
    };
    
    // Send state to API
    // Note: The server uses HTTPie but browser must use fetch API
    const response = await fetch('/api/noesis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'updateState',
        state: stateToSave
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    console.log('Pixel state saved to Redis');
  } catch (error) {
    console.warn('Failed to save pixel state:', error);
  }
}

/**
 * Sets up mouse event listeners for pixel interaction
 * @param {Object} state - The pixel state object
 */
function setupMouseInteractions(state) {
  // Track mouse movement
  document.addEventListener('mousemove', (event) => {
    state.mouseX = event.clientX;
    state.mouseY = event.clientY;
    
    // If the mouse has been idle for a while, consider this a new interaction
    const currentTime = performance.now();
    if (currentTime - state.lastInteractionTime > 300) {
      state.lastInteractionTime = currentTime;
    }
  });
  
  // Track mouse clicks
  document.addEventListener('mousedown', () => {
    state.mousePressed = true;
    state.mousePressedTime = performance.now();
    
    // Check if the click was close to the pixel
    const pixel = document.getElementById('conscious-pixel');
    if (pixel) {
      const pixelRect = pixel.getBoundingClientRect();
      const pixelCenterX = pixelRect.left + pixelRect.width / 2;
      const pixelCenterY = pixelRect.top + pixelRect.height / 2;
      
      const distance = Math.sqrt(
        Math.pow(state.mouseX - pixelCenterX, 2) +
        Math.pow(state.mouseY - pixelCenterY, 2)
      );
      
      // If clicking close to the pixel, make it excited
      if (distance < 100) {
        state.isExcited = true;
        state.excitementLevel = Math.min(1.0, state.excitementLevel + 0.5);
        
        // Force a color change to show reaction
        if (Math.random() < 0.7) {
          state.targetColor = '#FFFFFF'; // Flash white
        } else {
          state.targetColor = '#F0FF00'; // Flash yellow
        }
        state.colorTransitionProgress = 0;
        state.colorTransitionDuration = 300;
      }
    }
  });
  
  // Track mouse release
  document.addEventListener('mouseup', () => {
    state.mousePressed = false;
  });
  
  // Handle mouse leaving the window
  document.addEventListener('mouseleave', () => {
    state.mouseX = -1000;
    state.mouseY = -1000;
    state.mousePressed = false;
  });
}

/**
 * Changes the top background gradient color with a wave effect when the pixel touches edges
 * @param {string} direction - 'horizontal' or 'vertical', indicating which edge was touched
 * @param {number} position - Normalized position (0-1) where the touch occurred
 */
function changeBackgroundColor(direction = 'horizontal', position = 0.5) {
  const body = document.body;
  const currentTheme = parseInt(body.dataset.theme || "0", 5);
  
  // Calculate the next theme number
  const nextTheme = (currentTheme + 1) % 5;
  
  // Array of impressive top colors that combine well with the bottom color (#50c8ff)
  const impressiveTopColors = [
    '#e1ff6e',  // Original lime green
    '#ff64d4',  // Cool Sweet Pink
    '#06d6a0',  // Mint green
    '#9370db',  // Medium purple
    '#c23fff',  // Electric purple
  ];
  
  // Update the CSS variable for the top gradient color
  document.documentElement.style.setProperty('--gradient-top', impressiveTopColors[nextTheme]);
  
  // Store the current theme
  body.dataset.theme = nextTheme.toString();
  
  // Create a site-wide pulse effect that grows from the pixel
  const pixel = document.getElementById('conscious-pixel');
  
  if (pixel) {
    // Get the pixel's current position
    const pixelRect = pixel.getBoundingClientRect();
    const pixelX = pixelRect.left + pixelRect.width / 2;
    const pixelY = pixelRect.top + pixelRect.height / 2;
    
    // Convert to percentage of viewport
    const pixelXPercent = (pixelX / window.innerWidth) * 100;
    const pixelYPercent = (pixelY / window.innerHeight) * 100;
    
    // Set pulse origin to pixel's current position
    document.documentElement.style.setProperty('--pulse-origin-x', `${pixelXPercent}%`);
    document.documentElement.style.setProperty('--pulse-origin-y', `${pixelYPercent}%`);
    
    // Create or update the site-wide pulse overlay element
    let pulseOverlay = document.querySelector('.site-pulse');
    if (!pulseOverlay) {
      pulseOverlay = document.createElement('div');
      pulseOverlay.className = 'site-pulse';
      document.body.appendChild(pulseOverlay);
    }
    
    // Trigger the site-wide pulse animation
    pulseOverlay.classList.remove('active');
    void pulseOverlay.offsetWidth; // Force reflow to restart animation
    pulseOverlay.classList.add('active');
  }
  
  // Log theme change for debugging
  // console.log(`Changed top gradient color to ${impressiveTopColors[nextTheme]} with site-wide pulse from ${direction} edge at ${Math.round(position * 100)}%`);
}

/**
 * Processes pixel's response to mouse interactions
 * @param {Object} state - The pixel state object
 * @param {number} deltaTime - Time since last frame 
 */
function processMouseInteractions(state, deltaTime) {
  // Calculate distance from pixel to mouse
  const dx = state.mouseX - state.x;
  const dy = state.mouseY - state.y;
  const distanceSquared = dx * dx + dy * dy;
  const distance = Math.sqrt(distanceSquared);
  
  // Normalize direction vector
  let dirX = dx / (distance || 1); // Avoid division by zero
  let dirY = dy / (distance || 1);
  
  // Determine interaction behavior based on distance
  if (distance < 30) {
    // Too close - flee from the mouse
    const repelForce = 0.2; // Removed excitement level factor to maintain consistent speed
    state.velocityX -= dirX * repelForce * deltaTime;
    state.velocityY -= dirY * repelForce * deltaTime;
    
    // Increase excitement when fleeing
    state.isExcited = true;
    state.excitementLevel = Math.min(1.0, state.excitementLevel + 0.01 * deltaTime);
    
  } else if (distance < 150) {
    // Medium distance - curious behavior, slight attraction
    if (Math.random() < 0.5) {
      // 50% chance to be attracted
      const attractForce = 0.05 * deltaTime;
      state.velocityX += dirX * attractForce;
      state.velocityY += dirY * attractForce;
    } else {
      // 50% chance to do a small random movement
      state.velocityX += (Math.random() - 0.5) * 0.1 * deltaTime;
      state.velocityY += (Math.random() - 0.5) * 0.1 * deltaTime;
    }
    
    // Maintain some excitement
    state.isExcited = true;
    state.excitementLevel = Math.min(0.7, state.excitementLevel + 0.005 * deltaTime);
    
  } else if (distance < 300) {
    // Further away - occasional attraction
    if (Math.random() < 0.02) {
      // Occasional attraction
      const attractForce = 0.1 * deltaTime;
      state.velocityX += dirX * attractForce;
      state.velocityY += dirY * attractForce;
    }
    
    // Slowly reduce excitement when far away
    state.excitementLevel = Math.max(0, state.excitementLevel - 0.002 * deltaTime);
    if (state.excitementLevel < 0.1) {
      state.isExcited = false;
    }
  } else {
    // Far away - normal behavior
    // Gradually reduce excitement
    state.excitementLevel = Math.max(0, state.excitementLevel - 0.004 * deltaTime);
    if (state.excitementLevel < 0.1) {
      state.isExcited = false;
    }
  }
  
  // Handle mouse clicks - burst of energy and color change
  if (state.mousePressed) {
    const pressDuration = performance.now() - state.mousePressedTime;
    
    if (pressDuration < 100) {  // Initial click
      // For a brief moment, change behavior dramatically
      if (distance < 200) {
        // Flee more dramatically if mouse is clicked near the pixel
        state.velocityX -= dirX * 1.0;
        state.velocityY -= dirY * 1.0;
      }
    }
  }
  
  // Apply excitement and energy effects
  if (state.isExcited) {
    // Excited pixels no longer move faster (excitement doesn't affect speed)
    
    // Increase pulse speed when excited (visual effect only)
    const energyFactor = Math.max(0.4, state.energy / 100); // Keep this for visual effects only
    state.pulseStep = (0.03 + (state.excitementLevel * 0.04)) * energyFactor;
    
    // Apply a slight drag effect to gradually slow down
    state.velocityX *= 0.98;
    state.velocityY *= 0.98;
    
    // Being excited consumes more energy
    if (window.noeEnergy) {
      // Extra energy consumption due to excitement is handled in energy.js
    }
  } else {
    // Return to normal pulse speed when calm, no longer affected by energy
    state.pulseStep = 0.03;
  }
}

/**
 * Creates a rainbow effect on the bubble logo
 * Gives the bubble a beautiful rainbow surface with ripple effects
 */
function createRainbowBubbleEffect() {
  const logo = document.querySelector('#noesis-logo');
  if (!logo) return;
  
  // Apply rainbow class to the bubble
  logo.classList.add('rainbow-bubble');
  
  // Replace existing click event with a rainbow one
  const oldClickListeners = logo.cloneNode(true);
  logo.replaceWith(oldClickListeners);
  const newLogo = document.querySelector('#noesis-logo');
  
  // Add interactive rainbow light effect that follows mouse
  newLogo.addEventListener('mousemove', function(event) {
    const rect = this.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Create light reflection that follows cursor
    const percentX = Math.round((x / rect.width) * 100);
    const percentY = Math.round((y / rect.height) * 100);
    
    // Update the radial gradient to follow the cursor
    this.style.background = `radial-gradient(circle at ${percentX}% ${percentY}%, 
                              rgba(255, 255, 255, 0.8) 0%, 
                              transparent 50%),
                             linear-gradient(
                               124deg,
                               #ff0000,
                               #ff7f00,
                               #ffff00,
                               #00ff00,
                               #0000ff,
                               #4b0082,
                               #8b00ff
                             )`;
    this.style.backgroundSize = '100% 100%, 1800% 1800%';
    this.style.animation = 'rainbow-rotation 12s ease infinite, logo-breathing 8s ease-in-out infinite';
  });
  
  // Reset the gradient when mouse leaves
  newLogo.addEventListener('mouseleave', function() {
    this.style.background = '';
    this.style.backgroundSize = '';
  });
  
  console.log('Rainbow bubble effect applied');
}