#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

EMOTION_NEUTRAL = 0
EMOTION_HAPPY = 1
EMOTION_SAD = 2
EMOTION_ANGRY = 3
EMOTION_CURIOUS = 4
EMOTION_AFRAID = 5

_EMOTION_NAMES = {
    EMOTION_NEUTRAL: "neutral",
    EMOTION_HAPPY: "happy",
    EMOTION_SAD: "sad",
    EMOTION_ANGRY: "angry",
    EMOTION_CURIOUS: "curious",
    EMOTION_AFRAID: "afraid",
}

_RESPONSES = {
    EMOTION_HAPPY: "I'm feeling positive about this!",
    EMOTION_SAD: "I'm somewhat discouraged...",
    EMOTION_ANGRY: "I'm frustrated with this situation.",
    EMOTION_CURIOUS: "I find this very interesting.",
    EMOTION_AFRAID: "I'm concerned about the implications.",
}

current_emotion = EMOTION_NEUTRAL
emotion_intensity = 0


def init_emotion_system():
    global current_emotion, emotion_intensity
    current_emotion = EMOTION_NEUTRAL
    emotion_intensity = 0
    print("Emotion system initialized")


def set_emotion(emotion, intensity=5):
    global current_emotion, emotion_intensity
    if emotion is None:
        return False
    intensity = max(0, min(10, int(intensity)))
    current_emotion = emotion
    emotion_intensity = intensity
    print(f"Emotion changed: {emotion_to_string(emotion)} (intensity: {intensity})")
    return True


def emotion_to_string(emotion):
    return _EMOTION_NAMES.get(emotion, "unknown")


def get_current_emotion():
    return emotion_to_string(current_emotion)


def get_emotion_intensity():
    return emotion_intensity


def emotional_response(input_text=None):
    response = _RESPONSES.get(current_emotion, "I acknowledge this information.")
    print(response)
    return response
