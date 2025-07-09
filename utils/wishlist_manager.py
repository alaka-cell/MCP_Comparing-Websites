import json, os

WISHLIST_PATH = "wishlist.json"

def load_wishlist():
    if not os.path.exists(WISHLIST_PATH):
        return []
    with open(WISHLIST_PATH, "r") as f:
        return json.load(f)

def save_wishlist(wishlist):
    with open(WISHLIST_PATH, "w") as f:
        json.dump(wishlist, f, indent=2)

def add_to_wishlist(product):
    wishlist = load_wishlist()
    if not any(p["link"] == product["link"] for p in wishlist):
        wishlist.append(product)
        save_wishlist(wishlist)

def remove_from_wishlist(link):
    wishlist = load_wishlist()
    wishlist = [p for p in wishlist if p["link"] != link]
    save_wishlist(wishlist)
