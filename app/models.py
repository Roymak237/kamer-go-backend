"""
app/models.py

Data models and file I/O helpers.

All persistent data is stored in JSON files under the /data directory.
  - data/users.json       – registered users
  - data/itineraries.json – user itineraries
  - data/destinations.json – static destination catalogue (seed data)
  - data/shares.json      – shared itinerary records
"""
import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")

USERS_FILE = os.path.join(DATA_DIR, "users.json")
ITINERARIES_FILE = os.path.join(DATA_DIR, "itineraries.json")
DESTINATIONS_FILE = os.path.join(DATA_DIR, "destinations.json")
SHARES_FILE = os.path.join(DATA_DIR, "shares.json")


def _read_json(filepath: str) -> list:
    """Read *filepath* and return its contents as a list."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as fh:
        content = fh.read().strip()
        if not content:
            return []
        return json.loads(content)


def _write_json(filepath: str, data: list) -> None:
    """Serialise *data* and write it to *filepath*."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# User helpers

def get_all_users() -> list:
    return _read_json(USERS_FILE)


def get_user_by_username(username: str) -> dict | None:
    users = get_all_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None


def save_user(user: dict) -> None:
    users = get_all_users()
    users.append(user)
    _write_json(USERS_FILE, users)


def update_user(username: str, updates: dict) -> dict | None:
    users = get_all_users()
    for index, user in enumerate(users):
        if user.get("username") == username:
            updated = {**user, **updates}
            users[index] = updated
            _write_json(USERS_FILE, users)
            return updated
    return None


def update_username_references(old_username: str, new_username: str) -> dict | None:
    """Rename a user and preserve their itinerary/share relationships."""
    users = get_all_users()
    user = next(
        (entry for entry in users if entry.get("username") == old_username),
        None,
    )
    if user is None:
        return None

    renamed_user = {**user, "username": new_username}
    users[users.index(user)] = renamed_user
    _write_json(USERS_FILE, users)

    itineraries = get_all_itineraries()
    for itinerary in itineraries:
        if itinerary.get("username") == old_username:
            itinerary["username"] = new_username
    _write_json(ITINERARIES_FILE, itineraries)

    shares = get_all_shares()
    for share in shares:
        if share.get("owner") == old_username:
            share["owner"] = new_username
        if share.get("shared_with") == old_username:
            share["shared_with"] = new_username
    _write_json(SHARES_FILE, shares)

    return renamed_user


def delete_user_account(username: str) -> bool:
    """Delete a user and cascade their owned travel data and shares."""
    users = get_all_users()
    remaining_users = [user for user in users if user.get("username") != username]
    if len(remaining_users) == len(users):
        return False
    _write_json(USERS_FILE, remaining_users)

    itineraries = get_all_itineraries()
    deleted_itinerary_ids = {
        itinerary.get("id")
        for itinerary in itineraries
        if itinerary.get("username") == username
    }
    remaining_itineraries = [
        itinerary
        for itinerary in itineraries
        if itinerary.get("username") != username
    ]
    _write_json(ITINERARIES_FILE, remaining_itineraries)

    shares = get_all_shares()
    remaining_shares = [
        share
        for share in shares
        if share.get("owner") != username
        and share.get("shared_with") != username
        and share.get("itinerary_id") not in deleted_itinerary_ids
    ]
    _write_json(SHARES_FILE, remaining_shares)
    return True


# Destination helpers

def get_all_destinations() -> list:
    return _read_json(DESTINATIONS_FILE)


def get_destination_by_id(dest_id: str) -> dict | None:
    for dest in get_all_destinations():
        if dest.get("id") == dest_id:
            return dest
    return None


# Itinerary helpers

def get_all_itineraries() -> list:
    return _read_json(ITINERARIES_FILE)


def get_itineraries_for_user(username: str) -> list:
    return [it for it in get_all_itineraries() if it.get("username") == username]


def get_itinerary_by_id(itinerary_id: str) -> dict | None:
    for it in get_all_itineraries():
        if it.get("id") == itinerary_id:
            return it
    return None


def save_itinerary(itinerary: dict) -> None:
    itineraries = get_all_itineraries()
    itineraries.append(itinerary)
    _write_json(ITINERARIES_FILE, itineraries)


def update_itinerary(itinerary_id: str, updates: dict) -> dict | None:
    itineraries = get_all_itineraries()
    for idx, it in enumerate(itineraries):
        if it.get("id") == itinerary_id:
            updated = {**it, **updates}
            itineraries[idx] = updated
            _write_json(ITINERARIES_FILE, itineraries)
            return updated
    return None


def delete_itinerary(itinerary_id: str) -> bool:
    itineraries = get_all_itineraries()
    new_itineraries = [it for it in itineraries if it.get("id") != itinerary_id]
    if len(new_itineraries) == len(itineraries):
        return False
    _write_json(ITINERARIES_FILE, new_itineraries)
    return True


# Share helpers

def get_all_shares() -> list:
    return _read_json(SHARES_FILE)


def get_shares_for_itinerary(itinerary_id: str) -> list:
    return [s for s in get_all_shares() if s.get("itinerary_id") == itinerary_id]


def save_share(share: dict) -> None:
    shares = get_all_shares()
    shares.append(share)
    _write_json(SHARES_FILE, shares)


def delete_share(share_id: str) -> bool:
    shares = get_all_shares()
    new_shares = [s for s in shares if s.get("id") != share_id]
    if len(new_shares) == len(shares):
        return False
    _write_json(SHARES_FILE, new_shares)
    return True
