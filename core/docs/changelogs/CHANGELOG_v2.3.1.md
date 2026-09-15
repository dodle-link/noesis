# Noesis v2.3.1 Changelog

**Release Date:** September 15, 2026

## Overview

This release updates the core runtime version to 2.3.1 and adds the latest self-state and emotion-handling improvements to the intent layer. The change set keeps the "soul is the permanent self" architecture intact while improving the persistence and emotional behavior of the system.

## Major Changes

- **Self State Management**: Added persistent self-state tracking to the core intent layer so identity, emotion and awareness metadata are maintained across sessions more reliably.
- **Emotion Handling**: Improved emotional state transitions and updates in the intent module so the system can reason with a richer, more consistent internal state model.
- **Version Alignment**: Bumped the Noesis runtime and helper scripts to v2.3.1 for consistent release metadata across the core package.
- **Documentation Refresh**: Updated the core README to reflect the new release version and latest commit information.

## Bug Fixes and Stability

- **State Consistency**: Prevented self-state data from being lost or overwritten in a way that disrupted the identity/awareness lifecycle.
- **Emotion State Updates**: Cleaned up the way emotion and intensity values are tracked so the system behaves more predictably during reflective or reactive intent processing.
- **Release Metadata**: Ensured the core version strings and changelog references all match the v2.3.1 release.

## Compatibility Notes

- Compatible with the current Noesis `.noe` state patterns and the existing `process_intent_api` contract.
- No breaking changes to the command interface or core subsystem boundaries.
- This release is intended as a small, focused maintenance bump over v2.3.0.
