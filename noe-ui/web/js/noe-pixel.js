(function loadNoePixel() {
  window.noeWebPixel = true;
  const script = document.createElement('script');
  script.src = '../brain/limbric.js';
  script.defer = true;
  script.onload = () => window.initializeNoePixel();
  document.head.appendChild(script);
})();