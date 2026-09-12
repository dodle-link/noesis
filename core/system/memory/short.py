#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

MAX_DATA_ENTRIES = 1000

_store = {}


def init_data_storage():
    global _store
    _store = {}
    print("Data storage system initialized")


def store_data(key, value):
    if not key or value is None:
        print("Error: Key or value empty")
        return False

    verb = "Updated" if key in _store else "Stored"
    _store[key] = value
    print(f"{verb} data with key: {key}")
    return True


def retrieve_data(key):
    if not key:
        print("Error: Empty key")
        return None

    if key not in _store:
        print(f"Error: Key not found: {key}")
        return None

    return _store[key]


def delete_data(key):
    if not key:
        print("Error: Empty key")
        return False

    if key not in _store:
        print(f"Error: Key not found: {key}")
        return False

    del _store[key]
    print(f"Deleted data with key: {key}")
    return True


def list_data_keys():
    if not _store:
        print("No data stored")
        return []

    print("Stored data keys:")
    for k in _store:
        print(f"  {k}")
    return list(_store.keys())


def clear_data_storage():
    init_data_storage()
    print("Data storage cleared")
