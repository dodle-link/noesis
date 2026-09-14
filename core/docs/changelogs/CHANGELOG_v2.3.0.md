# Noesis v2.3.0 Changelog

**Release Date:** September 14, 2026

## Overview

This release aligns the `core/soul` and `core/system` layers with the "soul is the
permanent self, system is the body" design principle, removes duplicated
functionality between them, and fixes several consciousness-theory alignment
bugs uncovered while doing so.

## Major Changes

- **Soul / System Separation**: `soul/intent.py` is now strictly the permanent
  self — identity, the logic/reasoning engine, self-narrative and the
  `process_intent_api` entry point. All body-orchestration logic (booting
  subsystems, the interactive REPL, the quantum shell, command routing) moved
  to the new `system/control/orchestrator.py`, so the soul no longer knows how
  to boot or drive the body's subsystems.
- **Shared Console Helpers**: Added `system/control/console.py`, consolidating
  color codes, timestamped logging, error handling and command-history helpers
  that were previously duplicated across `run.py` and `soul/intent.py`.
- **`run.py` Simplified**: Now delegates to `console.py` and
  `system/control/orchestrator.py` instead of maintaining its own duplicate
  logging/history implementation.

## Bug Fixes

- **Consciousness Command Wiring**: `ai consciousness status|model|level|...`
  previously read consciousness state off the AI unit module instead of the
  consciousness module, so status always reported "unknown" / level 0.
  `intent_shell.py` now receives an explicit `consciousness_module` reference.
- **Missing Consciousness Theories**: `consciousness_process_perception` and
  `consciousness_emotion_integration` only special-cased IIT, GWT and HOT.
  Added the missing AST, GNW and PPT branches so all six declared theories
  (IIT, GWT, HOT, AST, GNW, PPT) behave consistently across perception,
  emotion and self-reflection.
- **Consciousness Module Never Loaded**: `system/cognition/unit.py` declared
  `_consciousness_module` but never populated it, so `init_consciousness()`
  never ran during AI system initialization. Added the missing loader.
- **Perception API Module Loading**: `system/perception/api.py` computed its
  base directory one level too shallow, so `_memory`, `_perception`,
  `_emotion`, `_intent` and `_data_storage` were silently `None`. Fixed the
  path and wired the consciousness module into perception/emotion processing.

## Compatibility Notes

- No changes to the `.noe` state file format or `process_intent_api` contract.
- Backward compatible with v2.2.x configuration and state files.
