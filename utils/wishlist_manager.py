import json, os

WISHLIST_DIR = "wishlists"

def _get_path(username):
    os.makedirs(WISHLIST_DIR, exist_ok=True)
    return os.path.join(WISHLIST_DIR, f"{username}.json")

def load_wishlist(username):
    path = _get_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_wishlist(wishlist, username):
    with open(_get_path(username), "w") as f:
        json.dump(wishlist, f, indent=2)

def add_to_wishlist(product, username):
    wishlist = load_wishlist(username)
    if not any(p["link"] == product["link"] for p in wishlist):
        wishlist.append(product)
        save_wishlist(wishlist, username)

def remove_from_wishlist(link, username):
    wishlist = load_wishlist(username)
    wishlist = [p for p in wishlist if p["link"] != link]
    save_wishlist(wishlist, username)