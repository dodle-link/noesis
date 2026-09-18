(function loadNoePixel() {
  window.noeWebPixel = true;
  const script = document.createElement('script');
  script.src = '../brain/limbric.js';
  script.defer = true;
  document.head.appendChild(script);
})();