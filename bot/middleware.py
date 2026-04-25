# telegram/middleware.py

PREMIUM_USERS = set()  # In memory for now, move to DB later

def is_premium(user_id: int) -> bool:
    return user_id in PREMIUM_USERS

def grant_premium(user_id: int):
    PREMIUM_USERS.add(user_id)

def revoke_premium(user_id: int):
    PREMIUM_USERS.discard(user_id)