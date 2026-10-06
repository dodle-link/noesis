const pixel = document.querySelector(".pixel");
const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
const pixelSize = 5;
const maxVelocity = 3;
const state = {
	x: pixelSize / 2 + Math.random() * Math.max(0, window.innerWidth - pixelSize),
	y: pixelSize / 2 + Math.random() * Math.max(0, window.innerHeight - pixelSize),
	velocityX: (Math.random() - 0.5) * 1.5,
	velocityY: (Math.random() - 0.5) * 1.5,
	mouseX: -1000,
	mouseY: -1000,
	fleeAngle: Math.random() * Math.PI * 2,
	excitementLevel: 0,
	lastTimestamp: 0,
};

function setPosition() {
	const offsetX = state.x - window.innerWidth / 2;
	const offsetY = state.y - window.innerHeight / 2;
	pixel.style.transform = `translate(calc(-50% + ${offsetX}px), calc(-50% + ${offsetY}px))`;
}

function processMouseInteraction(deltaTime, timestamp) {
	const dx = state.mouseX - state.x;
	const dy = state.mouseY - state.y;
	const distance = Math.hypot(dx, dy);
	const directionX = distance > 0 ? dx / distance : Math.cos(state.fleeAngle);
	const directionY = distance > 0 ? dy / distance : Math.sin(state.fleeAngle);

	if (distance < 30) {
		state.velocityX -= directionX * 0.2 * deltaTime;
		state.velocityY -= directionY * 0.2 * deltaTime;
		state.excitementLevel = Math.min(1, state.excitementLevel + 0.01 * deltaTime);
	} else if (distance < 150) {
		if (Math.random() < 0.5) {
			state.velocityX += directionX * 0.05 * deltaTime;
			state.velocityY += directionY * 0.05 * deltaTime;
		} else {
			state.velocityX += (Math.random() - 0.5) * 0.1 * deltaTime;
			state.velocityY += (Math.random() - 0.5) * 0.1 * deltaTime;
		}
		state.excitementLevel = Math.min(0.7, state.excitementLevel + 0.005 * deltaTime);
	} else if (distance < 300) {
		if (Math.random() < 0.02) {
			state.velocityX += directionX * 0.1 * deltaTime;
			state.velocityY += directionY * 0.1 * deltaTime;
		}
		state.excitementLevel = Math.max(0, state.excitementLevel - 0.002 * deltaTime);
	} else {
		state.excitementLevel = Math.max(0, state.excitementLevel - 0.004 * deltaTime);
	}

	if (state.excitementLevel > 0.1) {
		state.velocityX *= 0.98;
		state.velocityY *= 0.98;
	}
}

function updatePixel(timestamp) {
	const deltaTime = state.lastTimestamp
		? Math.min(3, (timestamp - state.lastTimestamp) / 16)
		: 1;
	state.lastTimestamp = timestamp;

	processMouseInteraction(deltaTime, timestamp);

	if (Math.random() < 0.03 * deltaTime) {
		state.velocityX += (Math.random() - 0.5) * 0.8;
		state.velocityY += (Math.random() - 0.5) * 0.8;
	}

	const speed = Math.hypot(state.velocityX, state.velocityY);
	if (speed > maxVelocity) {
		state.velocityX = (state.velocityX / speed) * maxVelocity;
		state.velocityY = (state.velocityY / speed) * maxVelocity;
	}

	state.x += state.velocityX * deltaTime;
	state.y += state.velocityY * deltaTime;
	const halfSize = pixelSize / 2;
	const maxX = Math.max(halfSize, window.innerWidth - halfSize);
	const maxY = Math.max(halfSize, window.innerHeight - halfSize);

	if (state.x < halfSize || state.x > maxX) {
		state.x = Math.max(halfSize, Math.min(maxX, state.x));
		state.velocityX *= -1;
	}
	if (state.y < halfSize || state.y > maxY) {
		state.y = Math.max(halfSize, Math.min(maxY, state.y));
		state.velocityY *= -1;
	}

	const glowSize = 2 + state.excitementLevel * 6;
	const glowOpacity = 0.2 + state.excitementLevel * 0.65;
	pixel.style.boxShadow = `0 0 ${glowSize}px rgba(255, 255, 255, ${glowOpacity})`;
	setPosition();

	if (!motionPreference.matches) {
		requestAnimationFrame(updatePixel);
	}
}

document.addEventListener("pointermove", (event) => {
	state.mouseX = event.clientX;
	state.mouseY = event.clientY;

	if (motionPreference.matches) {
		state.x = event.clientX;
		state.y = event.clientY;
		setPosition();
	}
});

document.addEventListener("pointerdown", (event) => {
	state.mouseX = event.clientX;
	state.mouseY = event.clientY;
	const dx = state.mouseX - state.x;
	const dy = state.mouseY - state.y;
	const distance = Math.hypot(dx, dy);

	if (distance < 200) {
		const directionX = distance > 0 ? dx / distance : Math.cos(state.fleeAngle);
		const directionY = distance > 0 ? dy / distance : Math.sin(state.fleeAngle);
		state.velocityX -= directionX;
		state.velocityY -= directionY;
		if (distance < 100) {
			state.excitementLevel = Math.min(1, state.excitementLevel + 0.5);
		}
	}
});

document.addEventListener("pointerleave", () => {
	state.mouseX = -1000;
	state.mouseY = -1000;
});

window.addEventListener("resize", () => {
	state.x = Math.max(pixelSize / 2, Math.min(window.innerWidth - pixelSize / 2, state.x));
	state.y = Math.max(pixelSize / 2, Math.min(window.innerHeight - pixelSize / 2, state.y));
	setPosition();
});

motionPreference.addEventListener("change", () => {
	if (!motionPreference.matches) {
		state.lastTimestamp = 0;
		requestAnimationFrame(updatePixel);
	}
});

setPosition();
if (!motionPreference.matches) {
	requestAnimationFrame(updatePixel);
}