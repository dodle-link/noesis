/**
 * Noe's Energy Surge - Synthetic Sentience Arcade Game Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // Canvas & Context setup
  const canvas = document.getElementById('game-canvas');
  const ctx = canvas.getContext('2d');

  // DOM UI Elements
  const energyFill = document.getElementById('energy-fill');
  const scoreVal = document.getElementById('score-val');
  const highscoreVal = document.getElementById('highscore-val');
  const waveVal = document.getElementById('wave-val');

  const startModal = document.getElementById('start-modal');
  const pauseModal = document.getElementById('pause-modal');
  const gameoverModal = document.getElementById('gameover-modal');

  const startBtn = document.getElementById('start-btn');
  const resumeBtn = document.getElementById('resume-btn');
  const restartBtn = document.getElementById('restart-btn');

  const finalScoreEl = document.getElementById('final-score');
  const bestScoreEl = document.getElementById('best-score');
  const finalCubesEl = document.getElementById('final-cubes');
  const finalWaveEl = document.getElementById('final-wave');

  const musicToggle = document.getElementById('music-toggle');
  const sfxToggle = document.getElementById('sfx-toggle');
  const crtToggle = document.getElementById('crt-toggle');
  const crtOverlay = document.getElementById('crt-overlay');

  // Game States: 'MENU', 'PLAYING', 'PAUSED', 'GAMEOVER'
  let gameState = 'MENU';

  // Audio Engine
  let audioCtx = null;
  let bgMusic = null;
  const bgTracks = [
    '../sounds/8-bit-music-1.mp3',
    '../sounds/8-bit-music-2.mp3',
    '../sounds/8-bit-music-3.mp3',
    '../sounds/8-bit-music-4.mp3'
  ];
  let currentTrackIdx = 0;

  // High Score Storage
  let highCore = parseInt(localStorage.getItem('noe_game_highscore') || '0', 10);
  highscoreVal.textContent = highCore.toLocaleString();

  // Resize canvas to viewport resolution
  function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // Web Audio SFX Synthesizer
  function initAudioContext() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  function playSynthSound(type) {
    if (!sfxToggle.checked) return;
    initAudioContext();
    if (!audioCtx) return;

    const now = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === 'pickup') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.exponentialRampToValueAtTime(1046.50, now + 0.12); // C6
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.linearRampToValueAtTime(0, now + 0.12);
      osc.start(now);
      osc.stop(now + 0.12);
    } else if (type === 'powerup') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(554.37, now + 0.08);
      osc.frequency.setValueAtTime(659.25, now + 0.16);
      osc.frequency.setValueAtTime(880, now + 0.24);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.linearRampToValueAtTime(0, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === 'hit') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(40, now + 0.2);
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.linearRampToValueAtTime(0, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    } else if (type === 'dash') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.1);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.linearRampToValueAtTime(0, now + 0.1);
      osc.start(now);
      osc.stop(now + 0.1);
    }
  }

  // Background Music Manager
  function initMusic() {
    if (!bgMusic) {
      bgMusic = new Audio();
      bgMusic.loop = false;
      bgMusic.volume = 0.4;
      bgMusic.addEventListener('ended', () => {
        currentTrackIdx = (currentTrackIdx + 1) % bgTracks.length;
        bgMusic.src = bgTracks[currentTrackIdx];
        if (musicToggle.checked && gameState === 'PLAYING') {
          bgMusic.play().catch(() => {});
        }
      });
    }
    bgMusic.src = bgTracks[currentTrackIdx];
  }

  function updateMusicState() {
    if (!bgMusic) initMusic();
    if (musicToggle.checked && gameState === 'PLAYING') {
      bgMusic.play().catch(() => {});
    } else if (bgMusic) {
      bgMusic.pause();
    }
  }

  musicToggle.addEventListener('change', updateMusicState);

  // CRT Overlay Toggle
  crtToggle.addEventListener('change', () => {
    if (crtToggle.checked) {
      crtOverlay.classList.remove('hidden');
    } else {
      crtOverlay.classList.add('hidden');
    }
  });

  // Game Variables
  let score = 0;
  let wave = 1;
  let energy = 100;
  let totalCubesCollected = 0;
  let lastTimestamp = 0;
  let waveTimer = 0;

  // Key state tracking
  const keys = {
    w: false, a: false, s: false, d: false,
    ArrowUp: false, ArrowLeft: false, ArrowDown: false, ArrowRight: false,
    Space: false
  };

  // Keys that control gameplay and would otherwise trigger the browser's
  // default scrolling behavior (arrows/space scroll the page vertically).
  const scrollBlockedCodes = new Set([
    'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space',
    'KeyW', 'KeyA', 'KeyS', 'KeyD'
  ]);

  window.addEventListener('keydown', (e) => {
    if (scrollBlockedCodes.has(e.code)) {
      e.preventDefault();
    }

    if (e.code === 'KeyP' || e.code === 'Escape') {
      if (gameState === 'PLAYING') pauseGame();
      else if (gameState === 'PAUSED') resumeGame();
      return;
    }

    if (e.code === 'Space' && gameState === 'PLAYING') {
      triggerDash();
    }

    if (e.key in keys) keys[e.key] = true;
    if (e.code in keys) keys[e.code] = true;
  }, { passive: false });

  window.addEventListener('keyup', (e) => {
    if (e.key in keys) keys[e.key] = false;
    if (e.code in keys) keys[e.code] = false;
  });

  // Touch / Pointer Direct Controls
  let targetPointer = null;

  canvas.addEventListener('pointerdown', (e) => {
    if (gameState !== 'PLAYING') return;
    const rect = canvas.getBoundingClientRect();
    targetPointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  });

  canvas.addEventListener('pointermove', (e) => {
    if (gameState !== 'PLAYING' || !targetPointer) return;
    const rect = canvas.getBoundingClientRect();
    targetPointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  });

  window.addEventListener('pointerup', () => {
    targetPointer = null;
  });

  // Entities
  let player = null;
  let cubes = [];
  let glitches = [];
  let particles = [];
  let floatingTexts = [];

  class Player {
    constructor() {
      this.radius = 16;
      this.x = canvas.width / 2;
      this.y = canvas.height / 2;
      this.vx = 0;
      this.vy = 0;
      this.speed = 350; // px/sec
      this.friction = 0.88;
      this.dashTimer = 0;
      this.dashDuration = 0.15; // sec
      this.dashCooldown = 0;
      this.shieldTimer = 0;
      this.magnetTimer = 0;
      this.trail = [];
      this.hue = 160; // Greenish
    }

    update(dt) {
      // Handle Dash Cooldowns & Timers
      if (this.dashTimer > 0) this.dashTimer -= dt;
      if (this.dashCooldown > 0) this.dashCooldown -= dt;
      if (this.shieldTimer > 0) this.shieldTimer -= dt;
      if (this.magnetTimer > 0) this.magnetTimer -= dt;

      let moveX = 0;
      let moveY = 0;

      // WASD / Arrow movement
      if (keys.w || keys.ArrowUp) moveY -= 1;
      if (keys.s || keys.ArrowDown) moveY += 1;
      if (keys.a || keys.ArrowLeft) moveX -= 1;
      if (keys.d || keys.ArrowRight) moveX += 1;

      if (moveX !== 0 || moveY !== 0) {
        const len = Math.hypot(moveX, moveY);
        moveX /= len;
        moveY /= len;

        const currentSpeed = this.dashTimer > 0 ? this.speed * 2.5 : this.speed;
        this.vx += moveX * currentSpeed * dt * 10;
        this.vy += moveY * currentSpeed * dt * 10;
      }

      // Pointer / Touch movement fallback
      if (targetPointer) {
        const dx = targetPointer.x - this.x;
        const dy = targetPointer.y - this.y;
        const dist = Math.hypot(dx, dy);
        if (dist > 5) {
          const moveSpeed = this.dashTimer > 0 ? this.speed * 2.5 : this.speed;
          this.vx += (dx / dist) * moveSpeed * dt * 8;
          this.vy += (dy / dist) * moveSpeed * dt * 8;
        }
      }

      // Physics integration
      this.vx *= this.friction;
      this.vy *= this.friction;

      this.x += this.vx * dt;
      this.y += this.vy * dt;

      // Canvas boundary limits
      this.x = Math.max(this.radius, Math.min(canvas.width - this.radius, this.x));
      this.y = Math.max(this.radius, Math.min(canvas.height - this.radius, this.y));

      // Trail updating
      this.trail.push({ x: this.x, y: this.y, alpha: 1 });
      if (this.trail.length > (this.dashTimer > 0 ? 12 : 6)) {
        this.trail.shift();
      }
      this.trail.forEach(t => t.alpha -= dt * 3);

      // Rainbow color effect if shield active
      if (this.shieldTimer > 0) {
        this.hue = (this.hue + dt * 360) % 360;
      } else {
        this.hue = 160; // default green
      }
    }

    draw() {
      // Trail
      this.trail.forEach((t) => {
        if (t.alpha <= 0) return;
        ctx.beginPath();
        ctx.arc(t.x, t.y, this.radius * (t.alpha * 0.8), 0, Math.PI * 2);
        ctx.fillStyle = this.shieldTimer > 0
          ? `hsla(${this.hue}, 100%, 70%, ${t.alpha * 0.4})`
          : `rgba(57, 255, 186, ${t.alpha * 0.3})`;
        ctx.fill();
      });

      // Magnet Field Aura
      if (this.magnetTimer > 0) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, 160, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 230, 0, ${0.15 + Math.sin(Date.now() * 0.01) * 0.05})`;
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 6]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Shield Aura
      if (this.shieldTimer > 0) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius + 10, 0, Math.PI * 2);
        ctx.strokeStyle = `hsla(${this.hue}, 100%, 65%, 0.9)`;
        ctx.lineWidth = 4;
        ctx.shadowColor = `hsl(${this.hue}, 100%, 65%)`;
        ctx.shadowBlur = 15;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // Main Noe Body (Glowing Bubble)
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = this.shieldTimer > 0 ? `hsl(${this.hue}, 100%, 60%)` : '#39ffba';
      ctx.shadowColor = this.shieldTimer > 0 ? `hsl(${this.hue}, 100%, 60%)` : '#39ffba';
      ctx.shadowBlur = 20;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Inner Highlight
      ctx.beginPath();
      ctx.arc(this.x - this.radius * 0.3, this.y - this.radius * 0.3, this.radius * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.fill();
    }
  }

  function triggerDash() {
    if (!player || player.dashCooldown > 0) return;
    player.dashTimer = player.dashDuration;
    player.dashCooldown = 0.8; // seconds
    playSynthSound('dash');

    // Create burst particles
    for (let i = 0; i < 10; i++) {
      particles.push(new Particle(player.x, player.y, '#00ddff', 120, 2.5));
    }
  }

  // Energy Cube Class
  class EnergyCube {
    constructor(type = 'REGULAR') {
      this.type = type; // 'REGULAR', 'GOLDEN', 'RAINBOW'
      this.radius = type === 'REGULAR' ? 8 : 11;
      const margin = 35;
      this.x = margin + Math.random() * (canvas.width - margin * 2);
      this.y = margin + Math.random() * (canvas.height - margin * 2);
      this.rotation = Math.random() * Math.PI;
      this.pulse = 0;

      if (type === 'REGULAR') {
        this.color = '#39ffba';
        this.energyVal = 15;
        this.scoreVal = 100;
      } else if (type === 'GOLDEN') {
        this.color = '#ffe600';
        this.energyVal = 30;
        this.scoreVal = 300;
      } else {
        this.color = '#f857e7';
        this.energyVal = 25;
        this.scoreVal = 500;
      }
    }

    update(dt) {
      this.rotation += dt * 2;
      this.pulse = Math.sin(Date.now() * 0.005) * 2;

      // Magnet attraction if player has magnet active
      if (player && player.magnetTimer > 0) {
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 180) {
          this.x += (dx / dist) * 260 * dt;
          this.y += (dy / dist) * 260 * dt;
        }
      }
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.rotation);

      const size = (this.radius + this.pulse) * 1.5;
      ctx.fillStyle = this.color;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 12;

      ctx.fillRect(-size / 2, -size / 2, size, size);

      ctx.restore();
    }
  }

  // Glitch Enemy Class
  class GlitchEnemy {
    constructor(speedMult = 1) {
      this.radius = 10 + Math.random() * 6;
      // Spawn near edges
      if (Math.random() < 0.5) {
        this.x = Math.random() < 0.5 ? -20 : canvas.width + 20;
        this.y = Math.random() * canvas.height;
      } else {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() < 0.5 ? -20 : canvas.height + 20;
      }

      this.speed = (80 + Math.random() * 70) * speedMult;
      this.color = '#ff3b5c';
      this.vx = (Math.random() - 0.5) * this.speed;
      this.vy = (Math.random() - 0.5) * this.speed;
      this.intent = 'WANDER';
      this.intentTimer = 0;
      this.focus = { x: this.x, y: this.y };
      this.focusCube = null;
      this.orbitAngle = Math.random() * Math.PI * 2;
      this.pulseTime = Math.random() * Math.PI * 2;
      this.pulse = 0;
      this.blinkTimer = 0.8 + Math.random() * 1.2;
      this.blinkDuration = 0;
      this.lookX = 0;
      this.lookY = 0;
    }

    chooseIntent() {
      this.focusCube = null;

      if (!player) {
        if (cubes.length > 0 && Math.random() < 0.6) {
          this.intent = 'CURIOUS';
          this.focusCube = cubes[Math.floor(Math.random() * cubes.length)];
          this.focus.x = this.focusCube.x;
          this.focus.y = this.focusCube.y;
        } else {
          this.intent = 'WANDER';
          this.focus.x = this.radius + Math.random() * (canvas.width - this.radius * 2);
          this.focus.y = this.radius + Math.random() * (canvas.height - this.radius * 2);
        }
        return;
      }

      const roll = Math.random();
      if (energy < 30 || roll < 0.45) {
        this.intent = 'HUNT';
        this.focus.x = player.x;
        this.focus.y = player.y;
      } else if (roll < 0.75) {
        this.intent = 'OBSERVE';
        this.orbitAngle = Math.random() * Math.PI * 2;
      } else if (cubes.length > 0) {
        this.intent = 'CURIOUS';
        this.focusCube = cubes[Math.floor(Math.random() * cubes.length)];
        this.focus.x = this.focusCube.x;
        this.focus.y = this.focusCube.y;
      } else {
        this.intent = 'WANDER';
        this.focus.x = this.radius + Math.random() * (canvas.width - this.radius * 2);
        this.focus.y = this.radius + Math.random() * (canvas.height - this.radius * 2);
      }
    }

    update(dt) {
      this.intentTimer -= dt;
      if (this.intentTimer <= 0) {
        this.chooseIntent();
        this.intentTimer = 0.6 + Math.random() * 1.2;
      }

      if (this.intent === 'HUNT' && player) {
        this.focus.x = player.x;
        this.focus.y = player.y;
      } else if (this.intent === 'OBSERVE' && player) {
        this.orbitAngle += dt * (1.4 + this.speed / 220);
        const orbitRadius = 70 + this.radius * 3;
        this.focus.x = player.x + Math.cos(this.orbitAngle) * orbitRadius;
        this.focus.y = player.y + Math.sin(this.orbitAngle) * orbitRadius;
      } else if (this.intent === 'CURIOUS') {
        if (!this.focusCube || !cubes.includes(this.focusCube)) {
          if (cubes.length > 0) {
            this.focusCube = cubes[Math.floor(Math.random() * cubes.length)];
          } else {
            this.intent = 'WANDER';
            this.focus.x = this.radius + Math.random() * (canvas.width - this.radius * 2);
            this.focus.y = this.radius + Math.random() * (canvas.height - this.radius * 2);
          }
        }
        if (this.focusCube) {
          this.focus.x = this.focusCube.x;
          this.focus.y = this.focusCube.y;
        }
      } else if (this.intent === 'WANDER') {
        const focusDist = Math.hypot(this.focus.x - this.x, this.focus.y - this.y);
        if (focusDist < 20) {
          this.focus.x = this.radius + Math.random() * (canvas.width - this.radius * 2);
          this.focus.y = this.radius + Math.random() * (canvas.height - this.radius * 2);
        }
      }

      const dx = this.focus.x - this.x;
      const dy = this.focus.y - this.y;
      const dist = Math.hypot(dx, dy) || 1;

      const steerPower = this.intent === 'HUNT'
        ? 120
        : this.intent === 'OBSERVE'
          ? 80
          : 65;

      this.vx += (dx / dist) * steerPower * dt;
      this.vy += (dy / dist) * steerPower * dt;

      // Small autonomous drift to avoid robotic movement
      this.vx += (Math.random() - 0.5) * 16 * dt;
      this.vy += (Math.random() - 0.5) * 16 * dt;

      const curSpeed = Math.hypot(this.vx, this.vy);
      if (curSpeed > this.speed) {
        this.vx = (this.vx / curSpeed) * this.speed;
        this.vy = (this.vy / curSpeed) * this.speed;
      }

      this.x += this.vx * dt;
      this.y += this.vy * dt;

      // Bounce off boundaries
      if (this.x < this.radius || this.x > canvas.width - this.radius) {
        this.vx *= -0.9;
        this.x = Math.max(this.radius, Math.min(canvas.width - this.radius, this.x));
      }
      if (this.y < this.radius || this.y > canvas.height - this.radius) {
        this.vy *= -0.9;
        this.y = Math.max(this.radius, Math.min(canvas.height - this.radius, this.y));
      }

      this.pulseTime += dt * 5.5;
      this.pulse = Math.sin(this.pulseTime) * 1.8;
      this.lookX += ((dx / dist) - this.lookX) * Math.min(1, dt * 7);
      this.lookY += ((dy / dist) - this.lookY) * Math.min(1, dt * 7);

      this.blinkTimer -= dt;
      if (this.blinkTimer <= 0) {
        this.blinkDuration = 0.05 + Math.random() * 0.08;
        this.blinkTimer = 1.2 + Math.random() * 2.2;
      }
      if (this.blinkDuration > 0) {
        this.blinkDuration -= dt;
      }
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(Math.atan2(this.vy, this.vx) * 0.25);

      const bodyW = this.radius * 1.35 + this.pulse;
      const bodyH = this.radius * 0.9 + this.pulse * 0.4;

      ctx.fillStyle = this.color;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 12;
      ctx.fillRect(-bodyW / 2, -bodyH / 2, bodyW, bodyH);
      ctx.shadowBlur = 0;

      const eyeOffsetX = this.lookX * (bodyW * 0.2);
      const eyeOffsetY = this.lookY * (bodyH * 0.22);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      if (this.blinkDuration > 0) {
        ctx.fillRect(-2 + eyeOffsetX, -0.5 + eyeOffsetY, 4, 1.2);
      } else {
        ctx.fillRect(-1.8 + eyeOffsetX, -1.8 + eyeOffsetY, 3.6, 3.6);
      }

      ctx.strokeStyle = 'rgba(255, 160, 180, 0.9)';
      ctx.lineWidth = 1;
      ctx.strokeRect(-bodyW / 2, -bodyH / 2, bodyW, bodyH);

      ctx.restore();
    }
  }

  // Particle Effect
  class Particle {
    constructor(x, y, color, speed = 100, life = 1) {
      this.x = x;
      this.y = y;
      this.color = color;
      this.radius = 2 + Math.random() * 3;
      const angle = Math.random() * Math.PI * 2;
      const spd = (0.3 + Math.random() * 0.7) * speed;
      this.vx = Math.cos(angle) * spd;
      this.vy = Math.sin(angle) * spd;
      this.life = life;
      this.maxLife = life;
    }

    update(dt) {
      this.x += this.vx * dt;
      this.y += this.vy * dt;
      this.life -= dt;
    }

    draw() {
      if (this.life <= 0) return;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius * (this.life / this.maxLife), 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
  }

  // Floating Text Popup
  class FloatingText {
    constructor(x, y, text, color = '#39ffba') {
      this.x = x;
      this.y = y;
      this.text = text;
      this.color = color;
      this.life = 0.8;
      this.maxLife = 0.8;
    }

    update(dt) {
      this.y -= 30 * dt;
      this.life -= dt;
    }

    draw() {
      if (this.life <= 0) return;
      ctx.save();
      ctx.font = 'bold 16px "HKGrotesk-Bold", monospace';
      ctx.fillStyle = this.color;
      ctx.globalAlpha = this.life / this.maxLife;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 6;
      ctx.fillText(this.text, this.x - 15, this.y);
      ctx.restore();
    }
  }

  // Start Game initialization
  function startGame() {
    score = 0;
    wave = 1;
    energy = 100;
    totalCubesCollected = 0;
    waveTimer = 0;

    player = new Player();
    cubes = [];
    glitches = [];
    particles = [];
    floatingTexts = [];

    // Initial Spawns
    for (let i = 0; i < 4; i++) spawnCube();
    for (let i = 0; i < 2; i++) glitches.push(new GlitchEnemy(1));

    updateHUD();

    startModal.classList.add('hidden');
    pauseModal.classList.add('hidden');
    gameoverModal.classList.add('hidden');

    gameState = 'PLAYING';
    lastTimestamp = performance.now();
    updateMusicState();

    requestAnimationFrame(gameLoop);
  }

  function spawnCube() {
    if (cubes.length >= 7) return;
    const rand = Math.random();
    let type = 'REGULAR';
    if (rand < 0.15) type = 'RAINBOW';
    else if (rand < 0.35) type = 'GOLDEN';

    cubes.push(new EnergyCube(type));
  }

  function pauseGame() {
    if (gameState !== 'PLAYING') return;
    gameState = 'PAUSED';
    pauseModal.classList.remove('hidden');
    updateMusicState();
  }

  function resumeGame() {
    if (gameState !== 'PAUSED') return;
    gameState = 'PLAYING';
    pauseModal.classList.add('hidden');
    lastTimestamp = performance.now();
    updateMusicState();
    requestAnimationFrame(gameLoop);
  }

  function gameOver() {
    gameState = 'GAMEOVER';
    playSynthSound('hit');
    updateMusicState();

    if (score > highCore) {
      highCore = score;
      localStorage.setItem('noe_game_highscore', highCore.toString());
      highscoreVal.textContent = highCore.toLocaleString();
    }

    finalScoreEl.textContent = score.toLocaleString();
    bestScoreEl.textContent = highCore.toLocaleString();
    finalCubesEl.textContent = totalCubesCollected;
    finalWaveEl.textContent = wave;

    gameoverModal.classList.remove('hidden');
  }

  function updateHUD() {
    energyFill.style.width = `${Math.max(0, energy)}%`;

    if (energy > 50) {
      energyFill.className = 'energy-fill';
    } else if (energy > 25) {
      energyFill.className = 'energy-fill warning';
    } else {
      energyFill.className = 'energy-fill critical';
    }

    scoreVal.textContent = score.toLocaleString();
    waveVal.textContent = wave;
  }

  // Main Game Loop
  function gameLoop(timestamp) {
    if (gameState !== 'PLAYING') return;

    const dt = Math.min((timestamp - lastTimestamp) / 1000, 0.1);
    lastTimestamp = timestamp;

    // 1. Logic Updates
    waveTimer += dt;

    // Wave Progression
    if (waveTimer > 18) {
      waveTimer = 0;
      wave++;
      playSynthSound('powerup');
      floatingTexts.push(new FloatingText(canvas.width / 2, canvas.height / 2, `WAVE ${wave} SURGE!`, '#00ddff'));
      // Spawn new glitch
      glitches.push(new GlitchEnemy(1 + wave * 0.15));
    }

    // Energy Drain over time (Base rate + Wave scaling)
    const drainRate = 3.0 + wave * 0.3; // % per sec
    energy -= drainRate * dt;

    if (energy <= 0) {
      energy = 0;
      updateHUD();
      gameOver();
      return;
    }

    // Update Player
    player.update(dt);

    // Maintain Energy Cubes population
    if (cubes.length < 3 + Math.floor(wave / 2)) {
      if (Math.random() < dt * 1.5) spawnCube();
    }

    // Update Cubes & Player Collisions
    for (let i = cubes.length - 1; i >= 0; i--) {
      const c = cubes[i];
      c.update(dt);

      const dx = player.x - c.x;
      const dy = player.y - c.y;
      const dist = Math.hypot(dx, dy);

      if (dist < player.radius + c.radius) {
        // Collect Cube!
        energy = Math.min(100, energy + c.energyVal);
        score += c.scoreVal * wave;
        totalCubesCollected++;

        if (c.type === 'GOLDEN') {
          player.magnetTimer = 8; // 8 seconds magnet
          playSynthSound('powerup');
          floatingTexts.push(new FloatingText(c.x, c.y, `+${c.scoreVal} MAGNET!`, '#ffe600'));
        } else if (c.type === 'RAINBOW') {
          player.shieldTimer = 6; // 6 seconds invincibility
          playSynthSound('powerup');
          floatingTexts.push(new FloatingText(c.x, c.y, `+${c.scoreVal} SHIELD!`, '#f857e7'));
        } else {
          playSynthSound('pickup');
          floatingTexts.push(new FloatingText(c.x, c.y, `+${c.scoreVal}`, '#39ffba'));
        }

        // Particle burst
        for (let p = 0; p < 12; p++) {
          particles.push(new Particle(c.x, c.y, c.color, 120, 0.5));
        }

        cubes.splice(i, 1);
      }
    }

    // Update Glitches & Collisions
    for (let i = glitches.length - 1; i >= 0; i--) {
      const g = glitches[i];
      g.update(dt);

      const dx = player.x - g.x;
      const dy = player.y - g.y;
      const dist = Math.hypot(dx, dy);

      if (dist < player.radius + g.radius) {
        if (player.shieldTimer > 0 || player.dashTimer > 0) {
          // Destroy glitch with shield/dash
          playSynthSound('hit');
          score += 150;
          floatingTexts.push(new FloatingText(g.x, g.y, `GLITCH CLEARED!`, '#ff3b5c'));
          for (let p = 0; p < 15; p++) {
            particles.push(new Particle(g.x, g.y, '#ff3b5c', 160, 0.6));
          }
          glitches.splice(i, 1);
          // Respawn after short delay
          setTimeout(() => glitches.push(new GlitchEnemy(1 + wave * 0.1)), 3000);
        } else {
          // Take Damage
          energy -= 20;
          playSynthSound('hit');
          floatingTexts.push(new FloatingText(player.x, player.y, `-20% ENERGY`, '#ff3b5c'));

          for (let p = 0; p < 15; p++) {
            particles.push(new Particle(player.x, player.y, '#ff3b5c', 180, 0.6));
          }

          // Knockback
          player.vx += (dx / dist) * 450;
          player.vy += (dy / dist) * 450;

          // Relocate glitch slightly away
          g.x = Math.random() < 0.5 ? 20 : canvas.width - 20;
          g.y = Math.random() < 0.5 ? 20 : canvas.height - 20;
        }
      }
    }

    // Update Particles
    for (let i = particles.length - 1; i >= 0; i--) {
      particles[i].update(dt);
      if (particles[i].life <= 0) particles.splice(i, 1);
    }

    // Update Floating Texts
    for (let i = floatingTexts.length - 1; i >= 0; i--) {
      floatingTexts[i].update(dt);
      if (floatingTexts[i].life <= 0) floatingTexts.splice(i, 1);
    }

    updateHUD();

    // 2. Rendering Pass
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Subtle background grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw Entities
    cubes.forEach(c => c.draw());
    glitches.forEach(g => g.draw());
    particles.forEach(p => p.draw());
    player.draw();
    floatingTexts.forEach(t => t.draw());

    // Next frame
    requestAnimationFrame(gameLoop);
  }

  // Event Listeners for Game Buttons
  startBtn.addEventListener('click', startGame);
  resumeBtn.addEventListener('click', resumeGame);
  restartBtn.addEventListener('click', startGame);
});
