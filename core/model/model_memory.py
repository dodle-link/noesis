# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import copy
import functools
import math
import re

try:
    from .model_config import CONFIG
    from .model_utils import clamp, now, uuid_bytes
except ImportError:  # run as a script from core/model
    from model_config import CONFIG
    from model_utils import clamp, now, uuid_bytes


def _stem(token):
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


@functools.lru_cache(maxsize=4096)
def _tokenize(text):
    """Stemmed words plus adjacent-word pairs, so phrases outrank scattered words."""
    words = [_stem(word) for word in re.findall(r"\w+", text.casefold())]
    return frozenset(words) | frozenset(f"{first} {second}" for first, second in zip(words, words[1:]))


class MemoryStore:
    def __init__(self, memory=None):
        self.items = memory if memory is not None else []

    def add(self, memory):
        item = {
                "id": uuid_bytes(),
                "timestamp": now(),
                "input": memory.get("input"),
                "action": memory.get("action"),
                "result": memory.get("result"),
                "reward": memory.get("reward"),
                "importance": clamp(memory.get("importance", 50), 0, 100),
            }
        for key in ("previousState", "prediction", "outcome"):
            if key in memory:
                item[key] = copy.deepcopy(memory[key])
        self.items.append(item)
        self.limit()

    def _retention(self, index):
        item = self.items[index]
        reward = item.get("reward")
        reward_bonus = (
            clamp(reward, -1, 1) * 10
            if isinstance(reward, (int, float)) and not isinstance(reward, bool) and math.isfinite(reward)
            else 0
        )
        return item["importance"] + 20 * (index + 1) / len(self.items) + reward_bonus

    def limit(self):
        # Importance dominates; recency and reward keep a fresh item from being the first to go.
        while len(self.items) > CONFIG["MEMORY_LIMIT"]:
            weakest = min(range(len(self.items)), key=lambda index: (self._retention(index), index))
            self.items.pop(weakest)

    def get_recent(self, count=10):
        return self.items[-count:]

    def recall(self, input_value, count=3):
        text = input_value.get("value") if isinstance(input_value, dict) else None
        tokens = _tokenize(text) if isinstance(text, str) else frozenset()
        if not tokens:
            return []
        documents = []
        for index, item in enumerate(self.items):
            stored_input = item.get("input")
            stored_text = stored_input.get("value") if isinstance(stored_input, dict) else None
            if isinstance(stored_text, str):
                documents.append((index, item, _tokenize(stored_text)))
        weights = {
            token: 1 + math.log((len(documents) + 1) / (1 + sum(token in document for _, _, document in documents)))
            for token in sorted(tokens)
        }
        total_weight = sum(weights.values())
        matches = []
        for index, item, stored_tokens in documents:
            overlap = sum(weight for token, weight in weights.items() if token in stored_tokens)
            if not overlap:
                continue
            relevance = min(overlap / (total_weight + len(stored_tokens - tokens)), 1.0)
            recency = (index + 1) / max(len(self.items), 1)
            matches.append((relevance, recency, item))
        matches.sort(key=lambda match: (match[0], match[1]), reverse=True)
        return [
            {"episode": copy.deepcopy(item), "relevance": relevance,
             "recency": recency, "uncertainty": 1 - relevance}
            for relevance, recency, item in matches[:count]
        ]

    def clear(self):
        self.items.clear()


def evaluate_memory_retrieval(memory, queries, count=3):
    """Score labeled retrieval queries against an existing memory store."""
    if not isinstance(memory, MemoryStore):
        raise ValueError("memory must be a MemoryStore.")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer.")
    if not isinstance(queries, list) or not queries:
        raise ValueError("queries must be a non-empty list.")
    recall = 0.0
    reciprocal_rank = 0.0
    positive_queries = 0
    negative_queries = 0
    false_positives = 0
    for query in queries:
        if not isinstance(query, dict) or not isinstance(query.get("relevant_ids"), list):
            raise ValueError("Each query must have a relevant_ids list.")
        relevant = query["relevant_ids"]
        if any(not isinstance(identifier, str) or not identifier for identifier in relevant) or len(set(relevant)) != len(relevant):
            raise ValueError("Relevant IDs must be distinct non-empty strings.")
        known_ids = {item.get("id") for item in memory.items}
        if not set(relevant) <= known_ids:
            raise ValueError("Relevant IDs must exist in memory.")
        found = [match["episode"]["id"] for match in memory.recall(query.get("input"), count)]
        if not relevant:
            negative_queries += 1
            false_positives += bool(found)
            continue
        positive_queries += 1
        recall += len(set(found) & set(relevant)) / len(relevant)
        reciprocal_rank += next((1 / rank for rank, identifier in enumerate(found, 1) if identifier in relevant), 0)
    return {"queries": len(queries), "count": count,
            "recall": recall / positive_queries if positive_queries else None,
            "mrr": reciprocal_rank / positive_queries if positive_queries else None,
            "positive_queries": positive_queries, "negative_queries": negative_queries,
            "false_positive_rate": false_positives / negative_queries if negative_queries else None}
