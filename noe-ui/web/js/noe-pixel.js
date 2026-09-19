window.noeWebPixel = true;

export async function loadNoePixel() {
  await import('../../brain/limbric.js');
}

loadNoePixel().catch((error) => {
  console.error('Failed to load the Noe pixel:', error);
});