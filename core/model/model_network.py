# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

from array import array
import math

try:
    from .model_config import CONFIG
    from .model_utils import Random, clamp
except ImportError:  # run as a script from core/model
    from model_config import CONFIG
    from model_utils import Random, clamp

_numpy_module = None


def _numpy():
    """Return NumPy when installed, else None; imported lazily so small networks never pay for it."""
    global _numpy_module
    if _numpy_module is None:
        try:
            import numpy
        except ImportError:
            numpy = False
        _numpy_module = numpy
    return _numpy_module or None


def softmax(values):
    peak = max(values)
    exponentials = [math.exp(value - peak) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


class TinyNetwork:
    def __init__(self, random=None, *, input_size=None, hidden_size=None, output_size=None):
        self.input_size = input_size or CONFIG["INPUT_SIZE"]
        self.hidden_size = hidden_size or CONFIG["HIDDEN_SIZE"]
        self.output_size = output_size or CONFIG["OUTPUT_SIZE"]
        self.weights1 = array("f", [0]) * (self.input_size * self.hidden_size)
        self.bias1 = array("f", [0]) * self.hidden_size
        self.weights2 = array("f", [0]) * (self.hidden_size * self.output_size)
        self.bias2 = array("f", [0]) * self.output_size
        self.initialize(random or Random())

    def initialize(self, random):
        # He-uniform for the ReLU layer, Glorot-uniform for the linear output layer.
        limit1 = math.sqrt(6 / self.input_size)
        limit2 = math.sqrt(6 / (self.hidden_size + self.output_size))
        for index in range(len(self.weights1)):
            self.weights1[index] = random.float(-limit1, limit1)
        for index in range(len(self.weights2)):
            self.weights2[index] = random.float(-limit2, limit2)
        self.bias1 = array("f", [0]) * self.hidden_size
        self.bias2 = array("f", [0]) * self.output_size

    @staticmethod
    def relu(value):
        return max(0, value)

    def _numpy_views(self):
        """Zero-copy float32 views of the weights, or None when the pure-Python path applies."""
        if self.input_size * self.hidden_size < CONFIG["NUMPY_MIN_WEIGHTS"]:
            return None
        arrays = (self.weights1, self.bias1, self.weights2, self.bias2)
        if any(not isinstance(values, array) or values.typecode != "f" for values in arrays):
            return None
        np = _numpy()
        if np is None:
            return None
        weights1, bias1, weights2, bias2 = (np.frombuffer(values, dtype=np.float32) for values in arrays)
        return (
            np,
            weights1.reshape(self.hidden_size, self.input_size),
            bias1,
            weights2.reshape(self.output_size, self.hidden_size),
            bias2,
        )

    def forward(self, input_vector):
        if len(input_vector) < self.input_size:
            raise ValueError("Input vector is shorter than the network input size.")
        views = self._numpy_views()
        if views is not None:
            np, weights1, bias1, weights2, bias2 = views
            inputs = np.asarray(input_vector[: self.input_size], dtype=np.float32)
            hidden = np.maximum(weights1 @ inputs + bias1, 0)
            output = weights2 @ hidden + bias2
            return {
                "hidden": array("f", hidden.astype(np.float32).tobytes()),
                "output": array("f", output.astype(np.float32).tobytes()),
            }
        input_size = self.input_size
        hidden_size = self.hidden_size
        inputs = input_vector[:input_size]
        hidden = array("f", [0]) * hidden_size
        output = array("f", [0]) * self.output_size
        for hidden_index in range(hidden_size):
            total = self.bias1[hidden_index]
            start = hidden_index * input_size
            for value, weight in zip(inputs, self.weights1[start : start + input_size]):
                total += value * weight
            hidden[hidden_index] = self.relu(total)
        for output_index in range(self.output_size):
            total = self.bias2[output_index]
            start = output_index * hidden_size
            for value, weight in zip(hidden, self.weights2[start : start + hidden_size]):
                total += value * weight
            output[output_index] = total
        return {"hidden": hidden, "output": output}

    def probabilities(self, input_vector):
        return softmax(self.forward(input_vector)["output"])

    def learn(self, input_vector, target, learning_rate, *, loss="mse", weight_decay=0.0, grad_clip=None):
        """One SGD step; loss is "mse" on raw outputs or "cross_entropy" on softmax(outputs)."""
        if loss not in ("mse", "cross_entropy"):
            raise ValueError("loss must be 'mse' or 'cross_entropy'.")
        result = self.forward(input_vector)
        hidden = result["hidden"]
        output = result["output"]
        predicted = softmax(output) if loss == "cross_entropy" else output
        output_errors = [target[index] - predicted[index] for index in range(self.output_size)]
        if grad_clip is not None:
            output_errors = [clamp(error, -grad_clip, grad_clip) for error in output_errors]
        decay = learning_rate * weight_decay

        views = self._numpy_views()
        if views is not None:
            np, weights1, bias1, weights2, bias2 = views
            inputs = np.asarray(input_vector[: self.input_size], dtype=np.float32)
            errors = np.asarray(output_errors, dtype=np.float32)
            hidden_values = np.frombuffer(hidden, dtype=np.float32)
            hidden_errors = (weights2.T @ errors) * (hidden_values > 0)
            if grad_clip is not None:
                hidden_errors = np.clip(hidden_errors, -grad_clip, grad_clip)
            if decay:
                weights1 *= 1 - decay
                weights2 *= 1 - decay
            weights2 += learning_rate * np.outer(errors, hidden_values)
            weights1 += learning_rate * np.outer(hidden_errors, inputs)
            np.clip(weights1, CONFIG["MIN_WEIGHT"], CONFIG["MAX_WEIGHT"], out=weights1)
            np.clip(weights2, CONFIG["MIN_WEIGHT"], CONFIG["MAX_WEIGHT"], out=weights2)
            bias2 += learning_rate * errors
            bias1 += learning_rate * hidden_errors
            return

        hidden_errors = array("f", [0]) * self.hidden_size
        for hidden_index in range(self.hidden_size):
            if hidden[hidden_index] <= 0:
                continue
            for output_index in range(self.output_size):
                hidden_errors[hidden_index] += (
                    output_errors[output_index]
                    * self.weights2[output_index * self.hidden_size + hidden_index]
                )
        if grad_clip is not None:
            for hidden_index in range(self.hidden_size):
                hidden_errors[hidden_index] = clamp(hidden_errors[hidden_index], -grad_clip, grad_clip)

        for output_index in range(self.output_size):
            output_error = output_errors[output_index]
            start = output_index * self.hidden_size
            for hidden_index in range(self.hidden_size):
                index = start + hidden_index
                weight = self.weights2[index]
                if decay:
                    weight -= decay * weight
                self.weights2[index] = clamp(
                    weight + learning_rate * output_error * hidden[hidden_index],
                    CONFIG["MIN_WEIGHT"],
                    CONFIG["MAX_WEIGHT"],
                )
            self.bias2[output_index] += learning_rate * output_error

        for hidden_index in range(self.hidden_size):
            error = hidden_errors[hidden_index]
            start = hidden_index * self.input_size
            for input_index in range(self.input_size):
                index = start + input_index
                weight = self.weights1[index]
                if decay:
                    weight -= decay * weight
                self.weights1[index] = clamp(
                    weight + learning_rate * error * input_vector[input_index],
                    CONFIG["MIN_WEIGHT"],
                    CONFIG["MAX_WEIGHT"],
                )
            self.bias1[hidden_index] += learning_rate * error
