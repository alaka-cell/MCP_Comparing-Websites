import streamlit as st
import random
import hashlib
import re
import os
import requests
from dotenv import load_dotenv
from utils.logger import logger
from mcp_client import MCPClient
from utils.wishlist_manager import load_wishlist, add_to_wishlist, remove_from_wishlist
from utils.ai_suggestor import generate_suggestions, compare_products
from requests.exceptions import RequestException

st.set_page_config(page_title="GLAM — Beauty Price Comparator", layout="wide", page_icon="🌸")
load_dotenv()

# 🧼 Hide default Streamlit sidebar page selector
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🎨 Custom Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&family=Playfair+Display:wght@400;500;600;700;800&display=swap');

:root {
    --rose:        #C8385A;
    --rose-dark:   #9B1D3A;
    --rose-mid:    #E05070;
    --rose-soft:   #F2AABB;
    --blush:       #FAE8EE;
    --blush-deep:  #F5D0DC;
    --cream:       #FDF6F8;
    --ink:         #1C0D12;
    --ink-mid:     #4A2530;
    --ink-light:   #7A4555;
    --white:       #FFFFFF;
    --border:      rgba(200, 56, 90, 0.18);
    --shadow-soft: 0 4px 24px rgba(200, 56, 90, 0.10);
    --shadow-card: 0 2px 12px rgba(28, 13, 18, 0.08);
}

*, *::before, *::after {
    box-sizing: border-box;
}

html, body, .stApp {
    font-family: 'DM Sans', sans-serif;
    font-style: normal !important;
    color: var(--ink);
    background-color: var(--cream);
}

em, i { font-style: normal !important; }

h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', serif;
    font-style: normal !important;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.3px;
}

/* ── Streamlit overrides ── */
.stApp > header { background: transparent !important; }

section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1.5px solid var(--border);
}

section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--rose) !important;
    border: none !important;
    border-radius: 6px !important;
    color: var(--white) !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    letter-spacing: 0.6px !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    transition: background 0.2s ease, transform 0.15s ease !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: var(--rose-dark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(200, 56, 90, 0.25) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox select {
    border-radius: 6px !important;
    border: 1.5px solid var(--blush-deep) !important;
    padding: 12px 16px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    background: var(--white) !important;
    color: var(--ink) !important;
    transition: border-color 0.2s ease !important;
}

.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--rose) !important;
    box-shadow: 0 0 0 3px rgba(200, 56, 90, 0.08) !important;
    outline: none !important;
}

.stTextInput input::placeholder {
    color: var(--ink-light) !important;
    font-style: normal !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 2px solid var(--blush-deep) !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.7px !important;
    text-transform: uppercase !important;
    color: var(--ink-light) !important;
    padding: 12px 20px !important;
    border: none !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}

.stTabs [aria-selected="true"] {
    color: var(--rose) !important;
    border-bottom-color: var(--rose) !important;
}

/* ── Sidebar user card ── */
.user-card {
    background: linear-gradient(145deg, var(--blush), var(--blush-deep));
    border-bottom: 1.5px solid var(--border);
    padding: 28px 20px 20px;
    text-align: center;
}

/* ── Hero ── */
.hero-wrap {
    position: relative;
    background: linear-gradient(135deg, #1C0D12 0%, #3D1020 60%, #5E1530 100%);
    border-radius: 12px;
    padding: 64px 48px;
    margin-bottom: 36px;
    overflow: hidden;
}

.hero-wrap::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(200,56,90,0.35) 0%, transparent 70%);
    pointer-events: none;
}

.hero-wrap::after {
    content: '';
    position: absolute;
    bottom: -60px; left: -40px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(242,170,187,0.18) 0%, transparent 70%);
    pointer-events: none;
}

.hero-eyebrow {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--rose-soft);
    margin-bottom: 14px;
}

.hero-title {
    font-family: 'Playfair Display', serif !important;
    font-size: clamp(38px, 5vw, 62px) !important;
    font-weight: 800 !important;
    color: var(--white) !important;
    line-height: 1.05 !important;
    letter-spacing: -1px !important;
    margin: 0 0 16px !important;
}

.hero-title span {
    color: var(--rose-soft);
}

.hero-sub {
    font-size: 15px;
    font-weight: 500;
    color: rgba(255,255,255,0.55);
    margin: 0;
    line-height: 1.5;
}

/* ── Section labels ── */
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--rose);
    margin-bottom: 6px;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--ink);
    margin: 0 0 20px;
    padding-bottom: 12px;
    border-bottom: 1.5px solid var(--border);
}

/* ── Metric cards ── */
.metric-card {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 20px 16px;
    text-align: center;
    transition: border-color 0.2s;
}

.metric-card:hover {
    border-color: var(--rose-soft);
    box-shadow: var(--shadow-soft);
}

.metric-number {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 800;
    color: var(--rose);
    line-height: 1;
    margin-bottom: 6px;
}

.metric-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--ink-mid);
    margin-bottom: 4px;
}

.metric-sub {
    font-size: 11px;
    color: var(--ink-light);
    font-weight: 500;
}

/* ── Summary strip ── */
.summary-strip {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--rose);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 20px 0 28px;
    font-size: 14px;
    font-weight: 600;
    color: var(--ink-mid);
    line-height: 1.65;
}

/* ── Product card ── */
.product-card {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    margin-bottom: 8px;
}

.product-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-soft);
    border-color: var(--rose-soft);
}

.product-img-wrap {
    width: 100%;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--blush);
    padding: 12px;
}

.product-body {
    padding: 12px;
}

.brand-pill {
    display: inline-block;
    background: var(--rose);
    color: var(--white);
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.product-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.45;
    height: 38px;
    overflow: hidden;
    margin-bottom: 8px;
}

.product-price {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--rose);
    margin-bottom: 4px;
}

.product-link a {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--rose);
    text-decoration: none;
    border-bottom: 1px solid var(--rose-soft);
    padding-bottom: 1px;
    transition: border-color 0.15s;
}

.product-link a:hover {
    border-color: var(--rose);
}

/* ── No-match placeholder ── */
.no-match {
    border: 1.5px dashed var(--blush-deep);
    border-radius: 10px;
    padding: 28px 16px;
    text-align: center;
    color: var(--ink-light);
    font-size: 12px;
    font-weight: 500;
    background: var(--cream);
}

/* ── Suggestion chips ── */
.suggestion-row {
    display: flex;
    align-items: center;
    padding: 11px 0;
    border-bottom: 1px solid var(--blush);
    font-size: 13px;
    font-weight: 600;
    color: var(--ink-mid);
    gap: 10px;
}

.suggestion-row a {
    color: var(--rose);
    text-decoration: none;
    font-weight: 700;
}

.suggestion-row a:hover { text-decoration: underline; }

/* ── Results header ── */
.results-header {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 24px 28px;
    margin-bottom: 24px;
}

.results-title {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--ink);
    margin: 0 0 4px;
}

.results-sub {
    font-size: 13px;
    font-weight: 500;
    color: var(--ink-light);
    margin: 0;
}

/* ── Wishlist item ── */
.wishlist-item {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 6px 0;
}

.wishlist-item a {
    font-size: 12px;
    font-weight: 700;
    color: var(--rose);
    text-decoration: none;
    display: block;
    margin-bottom: 2px;
}

.wishlist-price {
    font-size: 11px;
    font-weight: 600;
    color: var(--ink-light);
}

/* ── AI compare box ── */
.compare-result {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--rose);
    border-radius: 8px;
    padding: 16px 18px;
    margin-top: 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--ink-mid);
    line-height: 1.65;
}

/* ── Footer ── */
.site-footer {
    text-align: center;
    margin-top: 60px;
    padding: 28px 0;
    border-top: 1.5px solid var(--border);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--ink-light);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--cream); }
::-webkit-scrollbar-thumb { background: var(--rose-soft); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 🌐 ENV + Auth State
FLASK_API_URL = os.getenv("FLASK_API_URL")
auth = {"logged_in": False, "username": None, "role": None}

try:
    resp = requests.get(
        f"{FLASK_API_URL}/auth/check_session",
        cookies=dict(st.session_state.get("cookies", {}))
    )
    if resp.ok:
        auth.update(resp.json())
except Exception as e:
    logger.warning(f"Auth check failed: {e}")

if auth["logged_in"] and auth["role"] == "admin":
    st.switch_page("pages/admin_app.py")
    st.stop()

# 🔐 Auth Functions
def login_user(username, password, role):
    try:
        res = requests.post(
            f"{FLASK_API_URL}/auth/login",
            json={"username": username, "password": password, "role": role}
        )
        if res.ok:
            st.session_state["cookies"] = res.cookies.get_dict()
            st.success("Login successful.")
            st.rerun()
        else:
            st.error(res.json().get("error", "Login failed."))
    except RequestException as e:
        st.error(f"Login error: {e}")

def register_user(username, password, role):
    try:
        res = requests.post(
            f"{FLASK_API_URL}/auth/register",
            json={"username": username, "password": password, "role": role}
        )
        if res.ok:
            st.success("Registration successful! Please log in.")
            st.session_state.show_login = True
        else:
            st.error(res.json().get("error", "Registration failed."))
    except RequestException as e:
        st.error(f"Registration error: {e}")

# 🎭 Sidebar Navigation
if auth["logged_in"]:
    st.sidebar.markdown(f"""
        <div class="user-card">
            <div style="font-size: 38px; margin-bottom: 10px;">🌸</div>
            <div style="font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700;
                        color: var(--ink); margin-bottom: 3px;">{auth['username']}</div>
            <div style="font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;
                        color: var(--rose);">MEMBER</div>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar.expander("Navigate", expanded=False):
        selection = st.radio("Go to", ["Home", "Admin Dashboard"], label_visibility="collapsed")
        if selection == "Admin Dashboard":
            if auth["role"] == "admin":
                st.switch_page("pages/admin_app.py")
            else:
                st.warning("Access denied.")

    with st.sidebar.expander("Wishlist", expanded=True):
        wishlist = load_wishlist(auth["username"])
        if wishlist:
            for item in wishlist:
                unique_key = "remove_" + hashlib.md5(item['link'].encode()).hexdigest()
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"""
                        <div class="wishlist-item">
                            <a href="{item['link']}" target="_blank">{item['name'][:35]}…</a>
                            <div class="wishlist-price">{item['price']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("✕", key=unique_key):
                        remove_from_wishlist(item['link'], auth["username"])
                        st.rerun()
        else:
            st.markdown("""
                <div style="text-align:center; padding: 20px 12px; color: var(--ink-light);
                            font-size: 12px; font-weight: 600; background: var(--blush);
                            border-radius: 8px; margin: 8px 0;">
                    No items saved yet.
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Signed out.")
            st.rerun()

        st.markdown("---")
        st.markdown("""
            <div style="font-size: 10px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;
                        color: var(--ink-light); margin-bottom: 12px;">Compare Products</div>
        """, unsafe_allow_html=True)

        if "stored_result" in st.session_state and st.session_state.stored_result:
            all_products = []
            for source in ["top_myntra", "top_flipkart", "top_nykaa", "top_amazon"]:
                all_products.extend(st.session_state.stored_result.get(source, []))

            product_names = sorted({p.get("name", "").strip() for p in all_products if p.get("name")})

            if len(product_names) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    selected_1 = st.selectbox("Product 1", product_names, key="compare_1")
                with col2:
                    selected_2 = st.selectbox("Product 2", product_names, key="compare_2")

                if st.button("Compare", key="trigger_compare", use_container_width=True):
                    if selected_1 != selected_2:
                        with st.spinner("Analysing…"):
                            try:
                                response = compare_products(selected_1, selected_2)
                                st.markdown(f'<div class="compare-result">{response}</div>', unsafe_allow_html=True)
                            except Exception as e:
                                logger.error("Compare error: " + str(e))
                                st.warning("Comparison failed.")
                    else:
                        st.warning("Choose two different products.")
            else:
                st.info("Need at least 2 products.")
        else:
            st.info("Run a search first.")

else:
    if "show_login" not in st.session_state:
        st.session_state.show_login = True
    if "show_admin_login" not in st.session_state:
        st.session_state.show_admin_login = False

    with st.sidebar:
        st.markdown("""
            <div style="padding: 28px 20px 18px; background: linear-gradient(145deg, #FAE8EE, #F5D0DC);
                        border-bottom: 1.5px solid rgba(200,56,90,0.18); text-align: center; margin-bottom: 20px;">
                <div style="font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700;
                            color: #1C0D12; margin-bottom: 2px;">Glam</div>
                <div style="font-size: 9px; font-weight: 800; letter-spacing: 2.5px; text-transform: uppercase;
                            color: #C8385A;">Beauty Comparator</div>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.show_admin_login:
            st.markdown("""<div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                            color:#7A4555;margin-bottom:12px;">Admin Login</div>""", unsafe_allow_html=True)
            username = st.text_input("Admin Username", key="admin_user")
            password = st.text_input("Admin Password", type="password", key="admin_pass")
            if st.button("Login as Admin", use_container_width=True):
                login_user(username, password, "admin")
            if st.button("← Back", use_container_width=True):
                st.session_state.show_admin_login = False
                st.session_state.show_login = True
                st.rerun()

        elif st.session_state.show_login:
            st.markdown("""<div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                            color:#7A4555;margin-bottom:12px;">Sign In</div>""", unsafe_allow_html=True)
            login_user_input = st.text_input("Username", key="login_user")
            login_pass_input = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In", use_container_width=True):
                login_user(login_user_input, login_pass_input, "user")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
            if st.button("Admin Login →", use_container_width=True):
                st.session_state.show_login = False
                st.session_state.show_admin_login = True
                st.rerun()

        else:
            st.markdown("""<div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                            color:#7A4555;margin-bottom:12px;">Create Account</div>""", unsafe_allow_html=True)
            register_user_input = st.text_input("Username", key="reg_user")
            register_pass_input = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Register", use_container_width=True):
                register_user(register_user_input, register_pass_input, "user")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Already have an account? →", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()
            if st.button("Admin Login →", use_container_width=True):
                st.session_state.show_admin_login = True
                st.session_state.show_login = False
                st.rerun()

# ✨ Hero Banner
FORTUNES = [
    "Your perfect shade is one search away.",
    "Discover your next beauty obsession.",
    "Smart shopping starts with better comparisons.",
    "Find your holy grail product today.",
    "Every great look starts with a great find.",
    "Compare smarter. Glow harder.",
    "The best deal is always one click away.",
    "Your next favourite product is waiting."
]
fortune = random.choice(FORTUNES)

st.markdown(f"""
    <div class="hero-wrap">
        <div class="hero-eyebrow">Beauty Price Intelligence</div>
        <h1 class="hero-title">Find The Best<br><span>Beauty Deals</span></h1>
        <p class="hero-sub">{fortune}</p>
    </div>
""", unsafe_allow_html=True)

# 🎛️ Initialize MCPClient and result cache
if "client" not in st.session_state:
    st.session_state.client = MCPClient()
if "stored_result" not in st.session_state:
    st.session_state.stored_result = {}

query_params = st.query_params
if "q" in query_params:
    st.session_state.input_query = query_params["q"]

# 🔍 Search Bar
st.markdown("""
    <div style="margin-bottom: 8px;">
        <div class="section-label">Search</div>
        <div style="font-family:'Playfair Display',serif; font-size:20px; font-weight:700;
                    color:var(--ink); margin-bottom:16px;">What are you looking for?</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_mid, col_right = st.columns([1, 3, 1])
with col_mid:
    query = st.text_input(
        "",
        key="input_query",
        placeholder="e.g. Maybelline Lipstick, Lakme Foundation…",
        label_visibility="collapsed"
    )
    if st.button("Compare Prices →", key="compare-button", use_container_width=True):
        search = True
    else:
        search = False

cleaned_query = query.strip()

# Helpers
def clean_price(p):
    return str(p).replace("Rs.", "₹").replace("INR", "₹") if p else "—"

def extract_numeric_price(p):
    if not p:
        return 0
    match = re.search(r"[\d,]+", str(p))
    return int(match.group(0).replace(",", "")) if match else 0

def get_safe_key(url, prefix="wishlist_"):
    return prefix + hashlib.md5(url.encode()).hexdigest()

def show_product_grid(products, title, price_range):
    if not products:
        st.info(f"No products found for {title}.")
        return

    wishlist_links = {item['link'] for item in load_wishlist(auth["username"])} if auth["logged_in"] else set()

    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    filtered_products = [
        p for p in products
        if price_range[0] <= extract_numeric_price(p.get("price")) <= price_range[1]
    ]

    if not filtered_products:
        st.info("No products in this price range.")
        return

    cols = st.columns(min(5, len(filtered_products)))

    for i, p in enumerate(filtered_products):
        link_key = get_safe_key(p['link'] + title + str(i))
        is_wishlisted = p["link"] in wishlist_links

        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="product-card">
                <div class="product-img-wrap">
                    <img src="{p.get('image','')}" style="max-width:95%;max-height:95%;object-fit:contain;"
                         alt="{p.get('name','Product')}"/>
                </div>
                <div class="product-body">
                    <div class="brand-pill">{p.get('brand','-')[:20]}</div>
                    <div class="product-name">{p.get('name','-')[:60]}</div>
                    <div class="product-price">{clean_price(p.get('price'))}</div>
                    <div class="product-link"><a href="{p.get('link','#')}" target="_blank">View Product →</a></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if auth["logged_in"]:
                btn_label = "Remove" if is_wishlisted else "+ Wishlist"
                if st.button(btn_label, key=link_key, use_container_width=True):
                    if is_wishlisted:
                        remove_from_wishlist(p['link'], auth["username"])
                    else:
                        add_to_wishlist(p, auth["username"])
                        st.success("Saved!")
                    st.rerun()
            else:
                st.markdown("""
                    <div style="font-size:10px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;
                                color:var(--ink-light);text-align:center;padding:6px;background:var(--blush);
                                border-radius:4px;margin-top:4px;">
                        Login to Save
                    </div>
                """, unsafe_allow_html=True)

# 🔍 Scrape
if search and cleaned_query:
    with st.spinner("Searching across Myntra, Flipkart, Nykaa & Amazon…"):
        try:
            res = st.session_state.client.compare_sites(cleaned_query)
            st.session_state.stored_result = res
        except Exception as e:
            logger.error("Error calling compare_sites(): " + str(e))
            st.error("Something went wrong while fetching results.")
            st.stop()

# 🧾 Display Results
if st.session_state.stored_result:
    res = st.session_state.stored_result

    st.markdown(f"""
        <div class="results-header">
            <div class="results-title">Results for "{cleaned_query}"</div>
            <div class="results-sub">Comparing prices across Myntra, Flipkart, Nykaa & Amazon</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    metrics_data = [
        (col1, "Myntra",   f"{res['myntra_match']}%",   f"{res['myntra_total']} products"),
        (col2, "Flipkart", f"{res['flipkart_match']}%", f"{res['flipkart_total']} products"),
        (col3, "Nykaa",    f"{res['nykaa_match']}%",    f"{res['nykaa_total']} products"),
        (col4, "Amazon",   f"{res['amazon_match']}%",   f"{res['amazon_total']} products"),
    ]

    for col, label, match, total in metrics_data:
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-number">{match}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-sub">{total}</div>
                </div>
            """, unsafe_allow_html=True)

    summary = res.get("summary", "—")
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    short_summary = " ".join(sentences[:2]) if len(sentences) >= 2 else summary
    st.markdown(f'<div class="summary-strip">{short_summary}</div>', unsafe_allow_html=True)

    with st.expander("Filter by Price Range", expanded=False):
        price_range = st.slider("Price (₹)", 0, 10000, (0, 10000), step=100)

    tabs = st.tabs(["Myntra", "Flipkart", "Nykaa", "Amazon"])
    with tabs[0]:
        show_product_grid(res.get("top_myntra", []), "Top Products — Myntra", price_range)
    with tabs[1]:
        show_product_grid(res.get("top_flipkart", []), "Top Products — Flipkart", price_range)
    with tabs[2]:
        show_product_grid(res.get("top_nykaa", []), "Top Products — Nykaa", price_range)
    with tabs[3]:
        show_product_grid(res.get("top_amazon", []), "Top Products — Amazon", price_range)

    # ── Matched section ──
    st.markdown("""
        <div style="margin-top:44px;">
            <div class="section-label">Cross-Site Comparison</div>
            <div class="section-title">Matched Products Across All Sites</div>
        </div>
    """, unsafe_allow_html=True)

    matched = res.get("matched_products", [])
    if matched:
        wishlist_links = {item['link'] for item in load_wishlist(auth["username"])} if auth["logged_in"] else set()
        for i, group in enumerate(matched):
            cols = st.columns(4)
            site_labels = {"myntra": "Myntra", "flipkart": "Flipkart", "nykaa": "Nykaa", "amazon": "Amazon"}
            for idx, site in enumerate(["myntra", "flipkart", "nykaa", "amazon"]):
                product = group.get(site)
                with cols[idx]:
                    st.markdown(f"""
                        <div style="font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;
                                    color:var(--rose);margin-bottom:10px;">{site_labels[site]}</div>
                    """, unsafe_allow_html=True)

                    if product:
                        link_key = get_safe_key(product['link'], prefix=f"{site}_match_{i}")
                        is_wishlisted = product["link"] in wishlist_links

                        st.markdown(f"""
                        <div class="product-card">
                            <div class="product-img-wrap" style="height:130px;">
                                <img src="{product.get('image','')}" style="max-width:95%;max-height:95%;object-fit:contain;"
                                     alt="{product.get('name','Product')}"/>
                            </div>
                            <div class="product-body">
                                <div class="brand-pill">{product.get('brand','-')[:18]}</div>
                                <div class="product-name" style="height:34px;">{product.get('name','-')[:55]}</div>
                                <div class="product-price" style="font-size:18px;">{clean_price(product.get('price'))}</div>
                                <div class="product-link"><a href="{product.get('link','#')}" target="_blank">View →</a></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if auth["logged_in"]:
                            btn_label = "Remove" if is_wishlisted else "+ Wishlist"
                            if st.button(btn_label, key=link_key, use_container_width=True):
                                if is_wishlisted:
                                    remove_from_wishlist(product['link'], auth["username"])
                                else:
                                    add_to_wishlist(product, auth["username"])
                                    st.success("Saved!")
                                st.rerun()
                        else:
                            st.markdown("""
                                <div style="font-size:10px;font-weight:700;text-transform:uppercase;
                                            color:var(--ink-light);text-align:center;padding:5px;
                                            background:var(--blush);border-radius:4px;margin-top:4px;">
                                    Login to Save
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="no-match">Not available on this platform.</div>', unsafe_allow_html=True)
    else:
        st.info("No matching products found across sites.")

    # ── Suggestions ──
    st.markdown("""
        <div style="margin-top:44px;">
            <div class="section-label">Discovery</div>
            <div class="section-title">You Might Also Like</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                        color:var(--rose);margin-bottom:14px;">AI Suggestions</div>
        """, unsafe_allow_html=True)
        try:
            suggestions = generate_suggestions(cleaned_query)
            if suggestions:
                for s in suggestions:
                    suggestion_query = s.replace(" ", "+")
                    st.markdown(f"""
                        <div class="suggestion-row">
                            <span style="color:var(--rose);font-weight:800;">→</span>
                            <a href="?q={suggestion_query}">{s}</a>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No AI suggestions available.")
        except Exception as e:
            logger.error("AI suggestion error: " + str(e))
            st.warning("AI suggestions could not be loaded.")

    with col2:
        st.markdown("""
            <div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                        color:var(--rose);margin-bottom:14px;">Trending Searches</div>
        """, unsafe_allow_html=True)
        try:
            api_key = os.getenv("SERPER_API_KEY")
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": cleaned_query})
            data = response.json()
            suggestions = [item.get("title") for item in data.get("organic", [])][:5]
            for s in suggestions:
                st.markdown(f"""
                    <div class="suggestion-row">
                        <span style="color:var(--rose);font-weight:800;">→</span>
                        <span>{s}</span>
                    </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            logger.error("Serper fetch error: " + str(e))
            st.warning("No trending searches available.")

    st.markdown("""
        <div class="site-footer">
            GLAM · Beauty Price Comparator &nbsp;·&nbsp; Made with care ♥
        </div>
    """, unsafe_allow_html=True)