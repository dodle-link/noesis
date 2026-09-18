/**
 * Energy Cube System for Noe (conscious pixel)
 * Allows Noe to maintain energy via contact with energy cubes
 */

// Global energy system accessible to other scripts
window.noeEnergy = {
  currentLevel: 100,
  maxLevel: 100,
  needsEnergy: false,
  nearestCube: null
};

document.addEventListener('DOMContentLoaded', function() {
  // References
  const pixel = document.getElementById('conscious-pixel');
  const body = document.body;
  
  // Energy cubes configuration
  const numCubes = 1; // Only one cube that floats freely
  const cubes = [];
  const connections = [];
  let pixelPosition = { x: 0, y: 0 };
  
  // Energy system state
  let energy = 100;
  const energyDecayRate = 0.01; // Changed from 0.05 to 0.01 for ~1% energy decay per second
  const energyRechargeRate = 0.5;
  const contactDistance = 40; // Distance threshold for energy transfer
  
  // Cube movement settings
  const cubeMovementSpeed = 0.1;    // Base movement speed (reduced for slower movement)
  const cubeMaxSpeed = 0.3;         // Maximum speed (reduced for slower movement)
  const cubeWanderRadius = 600;     // How far cube will float (increased for wider coverage)
  let lastCubeMovementTime = 0;     // For time-based movement adjustments

  // Create energy cubes
  function createEnergyCubes() {
    // Remove any existing cubes
    document.querySelectorAll('.energy-cube').forEach(cube => cube.remove());
    document.querySelectorAll('.energy-connection').forEach(conn => conn.remove());
    document.querySelectorAll('.energy-target-indicator').forEach(ind => ind.remove());
    
    cubes.length = 0;
    connections.length = 0;
    
    // Create new cube at a random position
    for (let i = 0; i < numCubes; i++) {
      // Calculate position - place it anywhere on the screen
      const posX = 50 + Math.random() * (window.innerWidth - 100);
      const posY = 50 + Math.random() * (window.innerHeight - 100);
      
      // Create cube container
      const cubeElement = document.createElement('div');
      cubeElement.className = 'energy-cube';
      cubeElement.style.left = posX + 'px';
      cubeElement.style.top = posY + 'px';
      
      // Create 3D cube
      const cubeContainer = document.createElement('div');
      cubeContainer.className = 'cube-container';
      
      // Create cube faces
      const faces = ['front', 'back', 'right', 'left', 'top', 'bottom'];
      faces.forEach(face => {
        const faceElement = document.createElement('div');
        faceElement.className = `cube-face ${face}`;
        cubeContainer.appendChild(faceElement);
      });
      
      cubeElement.appendChild(cubeContainer);
      body.appendChild(cubeElement);
      
      // Create connection line (initially hidden)
      const connection = document.createElement('div');
      connection.className = 'energy-connection';
      body.appendChild(connection);
      
      // Store references
      cubes.push({
        element: cubeElement,
        position: { x: posX, y: posY },
        energy: 100,
        isCharging: false,
        connection: connection
      });
      connections.push(connection);
      
      // Activate cube with delay
      setTimeout(() => {
        cubeElement.classList.add('active');
      }, i * 300);
    }
  }
  
  // Update energy connections between Noe and cubes
  function updateConnections() {
    if (!pixel) return;
    
    cubes.forEach((cube, i) => {
      const dx = pixelPosition.x - cube.position.x;
      const dy = pixelPosition.y - cube.position.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Update connection line
      const connection = connections[i];
      const angle = Math.atan2(dy, dx) * 180 / Math.PI;
      
      connection.style.width = distance + 'px';
      connection.style.left = cube.position.x + 'px';
      connection.style.top = cube.position.y + 'px';
      connection.style.transform = `rotate(${angle}deg)`;
      
      // Check if close enough for energy transfer
      if (distance < contactDistance) {
        // Activate connection
        connection.classList.add('active');
        
        // Transfer energy when pixel is close
        if (cube.energy > 0 && energy < 100) {
          // Charge pixel
          energy = Math.min(100, energy + energyRechargeRate);
          cube.energy = Math.max(0, cube.energy - energyRechargeRate * 0.5);
          
          // Update global energy state immediately
          window.noeEnergy.currentLevel = energy;
          window.noeEnergy.needsEnergy = energy < 50; // Changed from 30 to 50
          
          // Visual feedback
          pixel.classList.add('energizing');
          const now = performance.now();
          if (window.noeImagine && now - (cube.lastBurstTime || 0) > 500) {
            window.noeImagine.createEnergyBurst(cube.position.x, cube.position.y);
            cube.lastBurstTime = now;
          }
          
          // Update cube appearance based on energy level
          updateCubeEnergy(cube);
        }
      } else {
        // Deactivate connection when far
        connection.classList.remove('active');
        pixel.classList.remove('energizing');
      }
    });
  }
  
  // Update cube appearance based on energy level
  function updateCubeEnergy(cube) {
    const faces = cube.element.querySelectorAll('.cube-face');
    
    if (cube.energy > 70) {
      faces.forEach(face => face.classList.add('charged'));
    } else if (cube.energy < 30) {
      faces.forEach(face => face.classList.remove('charged'));
    }
    
    // Make opacity reflect energy level
    const opacity = 0.3 + (cube.energy / 100) * 0.6;
    faces.forEach(face => face.style.opacity = opacity);
  }
  
  // Update energy level of pixel
  function updatePixelEnergy() {
    if (!pixel) return;
    
    // Natural energy decay over time
    energy = Math.max(0, energy - energyDecayRate);
    
    // Update global energy state
    window.noeEnergy.currentLevel = energy;
    window.noeEnergy.needsEnergy = energy < 50; // Changed from 30 to 50 to seek energy earlier
    
    // Check for death state (energy is 0)
    const isDead = energy <= 0;
    
    // Visual feedback - adjust pixel brightness based on energy
    const brightness = isDead ? 0.2 : (0.5 + (energy / 100) * 0.5);
    pixel.style.opacity = brightness;
    
    // Update pixel status if available
    const pixelStatus = document.getElementById('pixel-status');
    if (pixelStatus) {
      if (isDead) {
        pixelStatus.textContent = `Noe: ENERGY DEPLETED`;
        pixelStatus.classList.add('critical');
      } else {
        pixelStatus.textContent = `Noe: ${Math.round(energy)}% energy`;
        pixelStatus.classList.toggle('critical', energy < 10);
      }
    }
    
    // Find nearest energy cube if energy is low or depleted
    if (window.noeEnergy.needsEnergy || isDead) {
      findNearestCube();
    } else {
      window.noeEnergy.nearestCube = null;
      // Remove any targeting indicators when energy is sufficient
      document.querySelectorAll('.energy-target-indicator').forEach(ind => ind.remove());
    }
    
    // Regenerate cubes if all depleted
    const allDepleted = cubes.every(cube => cube.energy < 10);
    if (allDepleted) {
      createEnergyCubes();
    }
  }
  
  // Find the nearest energy cube with sufficient energy
  function findNearestCube() {
    if (!pixel || cubes.length === 0) return;
    
    let nearestDistance = Infinity;
    let nearestCube = null;
    let nearestIndex = -1;
    
    // Check if pixel is in death state
    const isDeathState = energy <= 0;
    
    // Get pixel position
    const pixelRect = pixel.getBoundingClientRect();
    const pixelX = pixelRect.left + pixelRect.width / 2;
    const pixelY = pixelRect.top + pixelRect.height / 2;
    
    cubes.forEach((cube, index) => {
      // In death state, all cubes with any energy should try to help
      // Otherwise, only consider cubes with sufficient energy
      if ((isDeathState && cube.energy > 5) || (!isDeathState && cube.energy > 20)) {
        const dx = pixelPosition.x - cube.position.x;
        const dy = pixelPosition.y - cube.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < nearestDistance) {
          nearestDistance = distance;
          nearestCube = {
            x: cube.position.x,
            y: cube.position.y,
            distance: distance,
            index: index
          };
          nearestIndex = index;
        }
      }
    });
    
    window.noeEnergy.nearestCube = nearestCube;
    
    // Update visual indicator for the target cube
    updateTargetIndicator(nearestIndex, isDeathState);
  }
  
  // Create or update visual indicator showing which cube is being targeted
  function updateTargetIndicator(cubeIndex, isDeathState = false) {
    // Remove any existing indicators
    document.querySelectorAll('.energy-target-indicator').forEach(ind => ind.remove());
    
    // If we have a valid cube index and energy is low or in death state, show target indicator
    if (cubeIndex >= 0 && cubeIndex < cubes.length && (energy < 50 || isDeathState)) {
      const cube = cubes[cubeIndex];
      
      // Create indicator element
      const indicator = document.createElement('div');
      indicator.className = 'energy-target-indicator';
      
      // Add classes based on energy level
      if (isDeathState) {
        indicator.classList.add('urgent');
      } else if (energy < 10) {
        indicator.classList.add('critical');
      } else if (energy < 25) {
        indicator.classList.add('very-low');
      } else if (energy < 50) {
        indicator.classList.add('low');
      }
      
      indicator.style.left = cube.position.x + 'px';
      indicator.style.top = cube.position.y + 'px';
      body.appendChild(indicator);
      
      // Add CSS style for the indicator if not already present
      if (!document.querySelector('style#energy-system-styles')) {
        const style = document.createElement('style');
        style.id = 'energy-system-styles';
        style.textContent = `
          .energy-target-indicator {
            position: fixed;
            width: calc(var(--cube-size) + 20px);
            height: calc(var(--cube-size) + 20px);
            border: 2px dashed rgba(255, 255, 255, 0.7);
            border-radius: 50%;
            transform: translate(-10px, -10px);
            pointer-events: none;
            z-index: 9989;
            animation: targetPulse 1.5s infinite alternate ease-in-out;
          }
          
          /* Energy level indicators */
          .energy-target-indicator.low {
            border: 2px dashed rgba(57, 255, 186, 0.8);
            animation: lowEnergyPulse 2s infinite alternate ease-in-out;
          }
          
          .energy-target-indicator.very-low {
            border: 2px dashed rgba(255, 186, 57, 0.8);
            animation: veryLowEnergyPulse 1.5s infinite alternate ease-in-out;
          }
          
          .energy-target-indicator.critical {
            border: 3px dashed rgba(255, 140, 50, 0.9);
            animation: criticalEnergyPulse 1s infinite alternate ease-in-out;
          }
          
          .energy-target-indicator.urgent {
            border: 3px dashed rgba(255, 100, 100, 0.9);
            animation: urgentPulse 0.8s infinite alternate ease-in-out;
          }
          
          @keyframes targetPulse {
            0% { transform: translate(-10px, -10px) scale(0.9); opacity: 0.4; }
            100% { transform: translate(-10px, -10px) scale(1.1); opacity: 0.8; }
          }
          
          @keyframes lowEnergyPulse {
            0% { transform: translate(-10px, -10px) scale(0.9); opacity: 0.5; }
            100% { transform: translate(-10px, -10px) scale(1.1); opacity: 0.7; box-shadow: 0 0 10px rgba(57, 255, 186, 0.2); }
          }
          
          @keyframes veryLowEnergyPulse {
            0% { transform: translate(-10px, -10px) scale(0.9); opacity: 0.6; box-shadow: 0 0 5px rgba(255, 186, 57, 0.2); }
            100% { transform: translate(-10px, -10px) scale(1.15); opacity: 0.8; box-shadow: 0 0 15px rgba(255, 186, 57, 0.3); }
          }
          
          @keyframes criticalEnergyPulse {
            0% { transform: translate(-10px, -10px) scale(0.9); opacity: 0.7; box-shadow: 0 0 8px rgba(255, 140, 50, 0.3); }
            100% { transform: translate(-10px, -10px) scale(1.2); opacity: 0.9; box-shadow: 0 0 18px rgba(255, 140, 50, 0.4); }
          }
          
          @keyframes urgentPulse {
            0% { transform: translate(-10px, -10px) scale(0.9); opacity: 0.7; box-shadow: 0 0 10px rgba(255, 0, 0, 0.3); }
            100% { transform: translate(-10px, -10px) scale(1.2); opacity: 0.9; box-shadow: 0 0 20px rgba(255, 0, 0, 0.5); }
          }
          
          /* Recharging effect for cubes */
          .cube-face.recharging {
            animation: recharge-pulse 0.8s ease-in-out;
          }
          
          @keyframes recharge-pulse {
            0% { opacity: 1; box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.8); }
            50% { opacity: 0.5; box-shadow: inset 0 0 30px rgba(57, 255, 186, 1); }
            100% { opacity: 1; box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.8); }
          }
        `;
        document.head.appendChild(style);
      }
    }
  }
  
  // Move cubes in a floating pattern - cubes never chase Noe, Noe must reach them
  function moveCubes(timestamp) {
    if (!cubes.length) return;
    
    // Calculate time delta for smooth movement
    const deltaTime = timestamp - lastCubeMovementTime;
    lastCubeMovementTime = timestamp;
    
    // Move each cube with a floating pattern
    cubes.forEach((cube, index) => {
      // Store original spawn position if not already stored
      if (!cube.spawnPosition) {
        cube.spawnPosition = { 
          x: cube.position.x, 
          y: cube.position.y 
        };
      }
      
      let newX, newY;
      
      // Free-flowing floating behavior
      const time = timestamp / 1000;
      
      // Calculate a more complex movement pattern for a single cube
      // Using multiple sine/cosine waves with different frequencies for more organic motion
      const floatX = (
        Math.sin(time * 0.2) * cubeWanderRadius * 0.4 + 
        Math.sin(time * 0.1) * cubeWanderRadius * 0.3
      );
      const floatY = (
        Math.cos(time * 0.15) * cubeWanderRadius * 0.4 + 
        Math.cos(time * 0.05) * cubeWanderRadius * 0.3
      );
      
      // Allow the cube to float more freely across the entire viewport
      if (!cube.centralPosition) {
        // Define a central position for the cube to orbit around
        cube.centralPosition = {
          x: window.innerWidth / 2,
          y: window.innerHeight / 2
        };
      }
      
      // Calculate position relative to central position
      newX = cube.centralPosition.x + floatX;
      newY = cube.centralPosition.y + floatY;
      
      // Occasionally update the central position
      if (Math.random() < 0.001) {
        cube.centralPosition = {
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight
        };
      }
      
      // Keep cube within screen boundaries with a bit of padding
      // Use smaller padding to allow more coverage of the screen
      const margin = 30;
      const boundedX = Math.max(margin, Math.min(window.innerWidth - margin, newX));
      const boundedY = Math.max(margin, Math.min(window.innerHeight - margin, newY));
      
      // Update cube position with smooth transition
      cube.position.x = boundedX;
      cube.position.y = boundedY;
      
      // Apply the new position to the DOM element with smooth transition
      cube.element.style.left = `${boundedX}px`;
      cube.element.style.top = `${boundedY}px`;
      
      // Also update any target indicators
      const indicator = document.querySelector('.energy-target-indicator');
      if (indicator && window.noeEnergy.nearestCube && window.noeEnergy.nearestCube.index === index) {
        indicator.style.left = `${boundedX}px`;
        indicator.style.top = `${boundedY}px`;
      }
    });
  }
  
  // Track pixel position
  function trackPixel() {
    if (!pixel) return;
    
    // Get pixel position from element
    const rect = pixel.getBoundingClientRect();
    pixelPosition = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2
    };
  }
  
  // Initialize everything
  function initialize() {
    createEnergyCubes();
    
    // Provide ways to interact with the energy system from outside
    window.noeEnergy.recharge = function(amount) {
      energy = Math.min(100, energy + amount);
      window.noeEnergy.currentLevel = energy;
      window.noeEnergy.needsEnergy = energy < 50; // Changed from 30 to 50
      
      // Visual feedback when recharging
      cubes.forEach(cube => {
        if (cube.element) {
          const faces = cube.element.querySelectorAll('.cube-face');
          faces.forEach(face => {
            face.classList.add('recharging');
            setTimeout(() => face.classList.remove('recharging'), 800);
          });
        }
      });
      
      return energy;
    };
    
    window.noeEnergy.consume = function(amount) {
      energy = Math.max(0, energy - amount);
      window.noeEnergy.currentLevel = energy;
      window.noeEnergy.needsEnergy = energy < 50; // Changed from 30 to 50
      return energy;
    };
    
    // Add a special method for checking if the pixel is in death state
    window.noeEnergy.isDeathState = function() {
      return energy <= 0;
    };
    
    // Initialize the movement timestamp
    lastCubeMovementTime = performance.now();
    
    // Main update loop with animation frame for smoother movements
    function mainLoop(timestamp) {
      trackPixel();
      updateConnections();
      updatePixelEnergy();
      moveCubes(timestamp);
      requestAnimationFrame(mainLoop);
    }
    
    // Start the animation loop
    requestAnimationFrame(mainLoop);
    
    // Regenerate cubes periodically or when window resizes
    window.addEventListener('resize', createEnergyCubes);
    setInterval(() => {
      // Randomly recharge cubes
      cubes.forEach(cube => {
        if (cube.energy < 100) {
          cube.energy += 0.2;
          updateCubeEnergy(cube);
        }
      });
    }, 1000);
  }
  
  // Start when pixel is detected
  if (pixel) {
    initialize();
  } else {
    // Wait for pixel to be created
    const observer = new MutationObserver(mutations => {
      if (document.getElementById('conscious-pixel')) {
        observer.disconnect();
        initialize();
      }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
  }
});
