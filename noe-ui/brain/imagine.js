/**
 * Imagination module for Noe.
 * Energy.js owns the cube lifecycle; this module owns energy reaction visuals.
 */
(function initializeImagination() {
  const ENERGY_COLOR = 'rgba(57, 255, 186, 0.8)';

  function createEnergyBurst(x, y) {
  const burst = document.createElement('div');
  burst.className = 'energy-burst';
  burst.style.cssText = `
    position: absolute;
    width: 5px;
    height: 5px;
    background-color: transparent;
    border-radius: 50%;
    left: ${x}px;
    top: ${y}px;
    z-index: 899;
    box-shadow: 0 0 30px 20px ${ENERGY_COLOR};
    animation: burstAnimation 0.5s ease-out forwards;
    pointer-events: none;
  `;

    ensureBurstAnimation();
  
  // Add to document and remove after animation
  document.body.appendChild(burst);
    setTimeout(() => burst.remove(), 500);
  }

  function ensureBurstAnimation() {
    if (document.getElementById('burst-animation')) return;

    const style = document.createElement('style');
    style.id = 'burst-animation';
    style.textContent = `
      @keyframes burstAnimation {
        0% { transform: scale(0.2); opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  window.noeImagine = Object.freeze({ createEnergyBurst });
  })();
