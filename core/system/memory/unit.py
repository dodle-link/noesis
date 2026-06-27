#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import time

MAX_MEMORIES = 1000
SHORT_TERM_LIMIT = 10
MID_TERM_LIMIT = 100

_memories = []
_short_term_start = 0
_mid_term_start = 0


def init_memory_system():
    global _memories, _short_term_start, _mid_term_start
    _memories = []
    _short_term_start = 0
    _mid_term_start = 0
    print("Memory system initialized")


def store_memory(content, importance=1):
    global _memories
    if not content:
        print("Cannot store empty memory")
        return False

    if len(_memories) >= MAX_MEMORIES:
        print("Memory capacity reached, consolidating...")
        consolidate_memories()

    _memories.append({
        "content": content,
        "timestamp": int(time.time()),
        "importance": int(importance),
        "access_count": 0,
    })
    print(f"Memory stored: {content} (importance: {importance})")
    return True


def retrieve_memory(query):
    if not query:
        print("Empty query")
        return None

    for i, mem in enumerate(_memories):
        if query in mem["content"]:
            _memories[i]["access_count"] += 1
            print(f"Memory #{i}: {mem['content']}")
            print(f"Importance: {mem['importance']}")
            print(f"Access count: {mem['access_count']}")
            return mem

    print("No matching memory found")
    return None


def consolidate_memories():
    global _memories
    half = len(_memories) // 2
    _memories = _memories[:half]
    print(f"Memory consolidation complete. Remaining memories: {len(_memories)}")
