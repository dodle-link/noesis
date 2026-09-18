// Noesis Audio Player
// Plays random music tracks from the sounds folder in an infinite loop

/**
 * Audio player system for Noesis project
 * Features:
 * - Plays music from the sounds folder
 * - Automatically changes to a random song when each song finishes
 * - Creates an infinite random playback loop
 * - Plays a click sound when mouse interacts with the pixel
 */

document.addEventListener('DOMContentLoaded', function() {
  // Audio tracks configuration
  const audioTracks = [
    'sounds/8-bit-music-1.mp3',
    'sounds/8-bit-music-2.mp3',
    'sounds/8-bit-music-3.mp3',
    'sounds/8-bit-music-4.mp3'
  ];
  
  // Sound effects configuration
  const clickSound = 'sounds/click.mp3';
  let clickSoundPlayer = null;
  
  // Audio player variables
  let audioPlayer = null;
  let currentTrackIndex = -1;
  let isPlaying = false;
  
  // Create and configure the audio player
  function initAudioPlayer() {
    audioPlayer = new Audio();
    
    // Set up event listeners
    audioPlayer.addEventListener('ended', playNextRandomTrack);
    audioPlayer.addEventListener('error', handleAudioError);
    
    // Initialize click sound player
    clickSoundPlayer = new Audio(clickSound);
    clickSoundPlayer.volume = 0.3;
    clickSoundPlayer.preload = 'auto';
    
    // Get the toggle switch
    const crtToggle = document.getElementById('crt-toggle');
    if (crtToggle) {
      // Ensure toggle is UNCHECKED by default (sound off)
      crtToggle.checked = false;
      
      // Set up event listener for toggle changes
      crtToggle.addEventListener('change', function() {
        if (this.checked) {
          // Toggle is ON - play sound
          if (!isPlaying) {
            playNextRandomTrack();
          } else {
            audioPlayer.play();
          }
        } else {
          // Toggle is OFF - pause sound
          if (audioPlayer && isPlaying) {
            audioPlayer.pause();
            isPlaying = false;
          }
        }
      });
    } else {
      console.warn('CRT toggle not found for audio control');
    }
    
    // Set up click sound (now only for toggle clicks)
    setupClickSound();
  }
  
  // Set up click sound for toggle interaction
  function setupClickSound() {
    const crtToggle = document.getElementById('crt-toggle');
    if (!crtToggle) {
      console.warn('CRT toggle not found for sound effect');
      return;
    }
    
    // Play click sound when toggle is clicked AND switched ON
    crtToggle.addEventListener('change', () => {
      // Only play click sound if toggle is being turned ON
      if (crtToggle.checked) {
        playClickSound();
      }
    });
  }
  
  // Play the click sound when toggle is used
  function playClickSound() {
    // First check if toggle is off - if so, don't play sound
    const crtToggle = document.getElementById('crt-toggle');
    if (!crtToggle || !crtToggle.checked) {
      // Toggle is off or not found, don't play sound
      return;
    }
    
    if (!clickSoundPlayer) {
      console.warn('Click sound player not initialized');
      return;
    }
    
    // Create a new Audio instance each time
    const soundInstance = new Audio(clickSound);
    soundInstance.volume = 0.3;
    
    soundInstance.play().catch(error => {
      console.warn('Could not play click sound:', error);
    });
  }
  
  // Play a random track, ensuring it's different from the current one if possible
  function playNextRandomTrack() {
    if (audioTracks.length === 0) {
      console.error('No audio tracks available');
      return;
    }
    
    let nextTrackIndex;
    
    // If we have more than one track, make sure we pick a different one
    if (audioTracks.length > 1) {
      do {
        nextTrackIndex = Math.floor(Math.random() * audioTracks.length);
      } while (nextTrackIndex === currentTrackIndex);
    } else {
      nextTrackIndex = 0;
    }
    
    currentTrackIndex = nextTrackIndex;
    playTrack(audioTracks[currentTrackIndex]);
  }
  
  // Play a specific track
  function playTrack(trackSrc) {
    if (!audioPlayer) return;
    
    // Update the audio source and play
    audioPlayer.src = trackSrc;
    
    // Play the track and update state
    const playPromise = audioPlayer.play();
    
    // Handle play() promise to catch any autoplay restrictions
    if (playPromise !== undefined) {
      playPromise
        .then(() => {
          isPlaying = true;
          console.log(`Now playing: ${trackSrc}`);
          // Show a small status indicator that fades out
          showMusicStatusIndicator(trackSrc);
        })
        .catch(error => {
          console.error('Playback prevented due to browser autoplay policy:', error);
          isPlaying = false;
          
          // Create a user interaction notice if autoplay is blocked
          showAutoplayNotice();
        });
    }
  }
  
  // Show a small status indicator when a new track starts
  function showMusicStatusIndicator(trackSrc) {
    // Create the status indicator element
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'music-status-indicator';
    statusIndicator.style.position = 'fixed';
    statusIndicator.style.top = '10px';
    statusIndicator.style.right = '10px';
    statusIndicator.style.background = 'rgba(0,0,0,0.6)';
    statusIndicator.style.color = 'white';
    statusIndicator.style.padding = '8px 12px';
    statusIndicator.style.borderRadius = '5px';
    statusIndicator.style.fontSize = '12px';
    statusIndicator.style.zIndex = '1000';
    statusIndicator.style.opacity = '0';
    statusIndicator.style.transition = 'opacity 0.5s';
    
    // Add to the page
    document.body.appendChild(statusIndicator);
  }
  
  // Handle audio playback errors
  function handleAudioError(error) {
    console.error('Audio playback error:', error);
    // Try to play the next track if there's an error
    setTimeout(playNextRandomTrack, 1000);
  }
  
  // Show a notice when autoplay is blocked
  function showAutoplayNotice() {
    // Get position of status bar for proper placement
    const statusBar = document.getElementById('pixel-status');
    const statusBarRect = statusBar ? statusBar.getBoundingClientRect() : { bottom: 40, left: 10 };
    
    // Create notice element
    const notice = document.createElement('div');
    notice.className = 'sound-status';
    notice.style.position = 'fixed';
    notice.style.bottom = 8 + 'px'; // Place 5px below status bar
    notice.style.left = statusBarRect.left + 'px'; // Align with left edge of status bar
    notice.style.background = 'rgba(255, 255, 255, 0.5)'; // Match status bar background
    notice.style.color = 'black'; // Match status bar text color
    notice.style.padding = '5px 10px'; // Match status bar padding
    notice.style.borderRadius = '4px'; // Match status bar border radius
    notice.style.zIndex = '999'; // Just below status bar z-index
    notice.style.fontSize = '13px'; // Match status bar font size
    notice.style.fontFamily = 'var(--font-family)'; // Match status bar font
    notice.style.cursor = 'pointer';
    notice.style.display = 'flex';
    notice.style.alignItems = 'center';
    notice.style.gap = '8px';
    
    notice.innerHTML = '<span>Use the "Play Sound" toggle to enable audio</span>';
    
    document.body.appendChild(notice);
    
    // Adjust status bar position
    if (statusBar) {
      statusBar.style.transition = 'transform 0.3s ease';
      statusBar.style.transform = 'translateY(-' + (notice.offsetHeight + 5) + 'px)';
    }
    
    // Function to handle sound toggle and remove notice
    const crtToggle = document.getElementById('crt-toggle');
    if (crtToggle) {
      const handleSoundToggle = function() {
        if (crtToggle.checked) {
          // Try to play the music
          playTrack(audioTracks[currentTrackIndex]);
          
          // Restore status bar position
          const statusBar = document.getElementById('pixel-status');
          if (statusBar) {
            statusBar.style.transform = 'translateY(0)';
          }
          
          // Remove notice
          if (document.body.contains(notice)) {
            document.body.removeChild(notice);
          }
          
          // Remove event listener
          crtToggle.removeEventListener('change', handleSoundToggle);
        }
      };
      
      // Enable playback on toggle change
      crtToggle.addEventListener('change', handleSoundToggle);
    }
    
    // Auto-hide notice after 10 seconds
    setTimeout(() => {
      if (document.body.contains(notice)) {
        // Restore status bar position
        if (statusBar) {
          statusBar.style.transform = 'translateY(0)';
        }
        
        // Remove notice
        document.body.removeChild(notice);
      }
    }, 10000);
  }
  
  // Initialize the audio player
  initAudioPlayer();
});
