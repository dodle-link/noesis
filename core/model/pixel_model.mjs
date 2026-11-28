const maxModelSize = 1024 * 1024;
const maxPixelHiddenSize = 128;

// Input order shared with PIXEL_FEATURES in me.py and createModelInputs() in me.js.
export const PIXEL_FEATURES = [
	"x",
	"y",
	"velocityX",
	"velocityY",
	"pointerDx",
	"pointerDy",
	"hasPointer",
	"excitement",
];

function readFloatArray(view, offset, length) {
	const values = new Float32Array(length);
	for (let index = 0; index < length; index++) {
		values[index] = view.getFloat32(offset + index * 4, true);
		if (!Number.isFinite(values[index])) {
			throw new Error("DODL model contains a non-finite value.");
		}
	}
	return values;
}

export function parsePixelModel(buffer) {
	if (buffer.byteLength > maxModelSize) {
		throw new Error("DODL model exceeds the 1 MiB size limit.");
	}
	const bytes = new Uint8Array(buffer);
	if (bytes.byteLength < 16 || String.fromCharCode(...bytes.subarray(0, 4)) !== "DODL") {
		throw new Error("Invalid DODL model header.");
	}

	const view = new DataView(buffer);
	const formatVersion = view.getUint16(4, true);
	const metadataSize = view.getUint32(8, true);
	const networkSize = view.getUint32(12, true);
	if (formatVersion !== 2 || 16 + metadataSize + networkSize !== buffer.byteLength) {
		throw new Error("Unsupported or corrupt DODL model.");
	}

	const metadata = JSON.parse(
		new TextDecoder().decode(new Uint8Array(buffer, 16, metadataSize)),
	);
	const { inputSize, hiddenSize, outputSize } = metadata.networkShape;
	if (
		inputSize !== PIXEL_FEATURES.length ||
		!Number.isSafeInteger(hiddenSize) ||
		hiddenSize < 1 ||
		hiddenSize > maxPixelHiddenSize ||
		outputSize !== 2
	) {
		throw new Error(
			`Expected a pixel model with ${PIXEL_FEATURES.length} inputs, 2 outputs, and at most 128 hidden units.`,
		);
	}
	const lengths = [inputSize * hiddenSize, hiddenSize, hiddenSize * outputSize, outputSize];
	if (networkSize !== lengths.reduce((total, length) => total + length * 4, 0)) {
		throw new Error("DODL network dimensions do not match its data.");
	}

	let offset = 16 + metadataSize;
	const arrays = lengths.map((length) => {
		const values = readFloatArray(view, offset, length);
		offset += length * 4;
		return values;
	});
	return {
		inputSize,
		hiddenSize,
		outputSize,
		weights1: arrays[0],
		bias1: arrays[1],
		weights2: arrays[2],
		bias2: arrays[3],
		hiddenScratch: new Float32Array(hiddenSize),
		outputScratch: new Float32Array(outputSize),
	};
}

export async function loadPixelModel(url = "./noe-pixel-model.dodl") {
	const response = await fetch(url, { cache: "no-cache" });
	if (!response.ok) {
		throw new Error(`Model request failed: ${response.status}`);
	}
	return parsePixelModel(await response.arrayBuffer());
}

export function runPixelModel(model, inputs) {
	const hidden = model.hiddenScratch;
	const outputs = model.outputScratch;
	for (let hiddenIndex = 0; hiddenIndex < model.hiddenSize; hiddenIndex++) {
		let total = model.bias1[hiddenIndex];
		const start = hiddenIndex * model.inputSize;
		for (let inputIndex = 0; inputIndex < model.inputSize; inputIndex++) {
			total += inputs[inputIndex] * model.weights1[start + inputIndex];
		}
		hidden[hiddenIndex] = Math.max(0, total);
	}
	for (let outputIndex = 0; outputIndex < model.outputSize; outputIndex++) {
		let total = model.bias2[outputIndex];
		const start = outputIndex * model.hiddenSize;
		for (let hiddenIndex = 0; hiddenIndex < model.hiddenSize; hiddenIndex++) {
			total += hidden[hiddenIndex] * model.weights2[start + hiddenIndex];
		}
		outputs[outputIndex] = total;
	}
	return outputs;
}