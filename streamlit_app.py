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

st.set_page_config(page_title="Product Comparator", layout="wide")
load_dotenv()

# 🧼 Hide default Streamlit sidebar page selector
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #FFF5F7 !important;
        color: #4B2C3A;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton > button, .stTextInput > div > input, .stSelectbox > div {
        background-color: #FFE4EC !important;
        color: #4B2C3A !important;
        border: 1px solid #f8c7d8;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #fbe3ed;
        color: #4B2C3A;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #fbd1e2;
        color: #4B2C3A;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FEC8D8 !important;
        font-weight: bold;
        border-bottom: 2px solid #E69EBB;
    }
    .stProgress > div > div > div > div {
        background-color: #FEC8D8;
    }
    .stMetric {
        background-color: #ffeaf1 !important;
        border-radius: 12px;
        padding: 12px;
    }
    .stAlert {
        background-color: #ffeaf1 !important;
        border-left: 6px solid #F48FB1 !important;
    }
    a {
        color: #d16ba5 !important;
    }
    a:hover {
        color: #b84d94 !important;
        text-decoration: underline;
    }
    .pink-link button {
        background: none;
        border: none;
        padding: 0;
        color: #d16ba5;
        text-decoration: underline;
        font-size: 14px;
        cursor: pointer;
    }
    .pink-link button:hover {
        color: #b84d94;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 ENV + Auth State
FLASK_API_URL = os.getenv("FLASK_API_URL")
auth = {"logged_in": False, "username": None, "role": None}

# 🍪 Check session
try:
    resp = requests.get(
        f"{FLASK_API_URL}/auth/check_session",
        cookies=dict(st.session_state.get("cookies", {}))
    )
    if resp.ok:
        auth.update(resp.json())
except Exception as e:
    logger.warning(f"Auth check failed: {e}")

# 🚫 Admin Redirect
if auth["logged_in"] and auth["role"] == "admin":
    st.switch_page("pages/admin_app.py")
    st.stop()

import streamlit.components.v1 as components

components.html("""
<style>
.drawer-button {
    position: fixed;
    top: 70px;
    left: 20px;
    z-index: 1001;
    background-color: #FEC8D8;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 16px;
    color: #4B2C3A;
    cursor: pointer;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
}

.drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.3);
    z-index: 1000;
    display: none;
}

.drawer {
    position: fixed;
    top: 0;
    left: -300px;
    height: 100%;
    width: 260px;
    background-color: #fff0f5;
    box-shadow: 2px 0 10px rgba(0,0,0,0.15);
    z-index: 1001;
    padding: 20px;
    transition: left 0.3s ease;
    border-radius: 0 12px 12px 0;
}

.drawer.open {
    left: 0;
}

.drawer h4 {
    margin-top: 0;
    color: #D16BA5;
}

.drawer ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.drawer ul li {
    margin: 16px 0;
}

.drawer a {
    text-decoration: none;
    color: #D16BA5;
    font-size: 16px;
}
.drawer a:hover {
    text-decoration: underline;
    color: #b84d94;
}
</style>

<div class="drawer-overlay" id="drawer-overlay" onclick="toggleDrawer()"></div>

<div class="drawer" id="drawer">
  <h4>Menu</h4>
  <ul>
    <li><a href="#home">Home</a></li>
    <li><a href="#wishlist">Wishlist</a></li>
    <li><a href="#admin">🛠 Admin Dashboard</a></li>
    <li><a href="#logout">Logout</a></li>
  </ul>
</div>

<button class="drawer-button" onclick="toggleDrawer()">☰ Menu</button>

<script>
function toggleDrawer() {
    const drawer = window.parent.document.getElementById("drawer");
    const overlay = window.parent.document.getElementById("drawer-overlay");
    const isOpen = drawer.classList.contains("open");
    if (isOpen) {
        drawer.classList.remove("open");
        overlay.style.display = "none";
    } else {
        drawer.classList.add("open");
        overlay.style.display = "block";
    }
}
</script>
""", height=0)

# 🔐 Auth Functions
def login_user(username, password, role):
    try:
        res = requests.post(
            f"{FLASK_API_URL}/auth/login",
            json={"username": username, "password": password, "role": role}
        )
        if res.ok:
            st.session_state["cookies"] = res.cookies.get_dict()
            st.success("Login successful. Please rerun the app.")
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
            st.success("Registration successful! Please log in below.")
            st.session_state.show_login = True
        else:
            st.error(res.json().get("error", "Registration failed."))
    except RequestException as e:
        st.error(f"Registration error: {e}")

st.markdown('<a name="admin"></a>', unsafe_allow_html=True)

if auth["logged_in"]:
    with st.sidebar.expander("Menu", expanded=False):
        selection = st.radio("Go to", ["Home", "Admin Dashboard"], label_visibility="collapsed")

        if selection == "Admin Dashboard":
            if auth["role"] == "admin":
                st.switch_page("pages/admin_app.py")
            else:
                st.warning("Access denied: Admins only.")

    st.markdown('<a name="wishlist"></a>', unsafe_allow_html=True)

    with st.sidebar.expander("My Wishlist", expanded=True):

        wishlist = load_wishlist(auth["username"])
        if wishlist:
            for item in wishlist:
                unique_key = "remove_" + hashlib.md5(item['link'].encode()).hexdigest()
                with st.container():
                    col1, col2 = st.columns([8, 1])
                    with col1:
                        st.markdown(f"""
                            <div style="margin-top:5px">
                                <a href="{item['link']}" target="_blank">
                                    <strong>{item['name']}</strong>
                                </a><br>
                                {item['price']}
                            </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("X", key=unique_key):
                            remove_from_wishlist(item['link'], auth["username"])
                            st.rerun()
        else:
            st.info("No items wishlisted yet.")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully.")
            st.rerun()

        # Compare Tool
        st.markdown("---")
        st.markdown("**Compare Two Products**")
        if "stored_result" in st.session_state and st.session_state.stored_result:
            all_products = []
            for source in ["top_myntra", "top_ajio", "top_nykaa", "top_amazon"]:
                all_products.extend(st.session_state.stored_result.get(source, []))

            product_names = sorted({p.get("name", "").strip() for p in all_products if p.get("name")})

            if len(product_names) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    selected_1 = st.selectbox("Product 1", product_names, key="compare_1")
                with col2:
                    selected_2 = st.selectbox("Product 2", product_names, key="compare_2")

                if st.button("Compare Now", key="trigger_compare"):
                    if selected_1 != selected_2:
                        with st.spinner("Generating comparison..."):
                            try:
                                response = compare_products(selected_1, selected_2)
                                st.markdown("----")
                                st.markdown(f"<strong>You:</strong> Compare *{selected_1}* and *{selected_2}*", unsafe_allow_html=True)
                                st.markdown(f"<div style='background-color:#fff0f5; padding:12px; border-radius:10px;'><strong>AI:</strong> {response}</div>", unsafe_allow_html=True)
                            except Exception as e:
                                logger.error("Compare error: " + str(e))
                                st.warning("Comparison failed.")
                    else:
                        st.warning("Choose two different products.")
            else:
                st.info("Need at least two products to compare.")
        else:
            st.info("Search first to use comparison.")
else:
    if "show_login" not in st.session_state:
        st.session_state.show_login = True
    if "show_admin_login" not in st.session_state:
        st.session_state.show_admin_login = False

    with st.sidebar:
        if st.session_state.show_admin_login:
            st.subheader("Admin Login")
            username = st.text_input("Admin Username", key="admin_user")
            password = st.text_input("Admin Password", type="password", key="admin_pass")
            if st.button("Login as Admin"):
                login_user(username, password, "admin")

            if st.button("← Back to User Login"):
                st.session_state.show_admin_login = False
                st.session_state.show_login = True
                st.rerun()

        elif st.session_state.show_login:
            st.subheader("User Login")
            login_user_input = st.text_input("Username", key="login_user")
            login_pass_input = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                login_user(login_user_input, login_pass_input, "user")

            if st.button("New user? Register here"):
                st.session_state.show_login = False

            if st.button("Login as Admin"):
                st.session_state.show_login = False
                st.session_state.show_admin_login = True
                st.rerun()

        else:
            st.subheader("Register")
            register_user_input = st.text_input("New Username", key="reg_user")
            register_pass_input = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Register"):
                register_user(register_user_input, register_pass_input, "user")

            if st.button("Already registered? Login here"):
                st.session_state.show_login = True

            if st.button("Login as Admin"):
                st.session_state.show_admin_login = True
                st.session_state.show_login = False
                st.rerun()

# 🎀 Main Title & Fortune Caption - Redesigned
FORTUNES = [
    "Your perfect shade is just a click away!",
    "One swipe could change your look forever!",
    "Today’s glam find might be hiding in plain sight!",
    "Beauty begins the moment you start searching!",
    "A glow-up is only one product away!",
    "Self-care starts with the right pick!",
    "Find your holy grail product today!",
    "Slay the day with your next beauty buy!"
]

fortune = random.choice(FORTUNES)

with st.container():
    st.markdown(
        f"""
        <div style="text-align:center; padding: 30px 0;">
            <h1 style="font-size: 48px; color: #D16BA5; margin-bottom: 8px;">Product Comparator</h1>
            <p style="font-size: 20px; color: #7A4F66;">{fortune}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
st.markdown('<a name="home"></a>', unsafe_allow_html=True)

# 🎛️ Initialize MCPClient and result cache
if "client" not in st.session_state:
    st.session_state.client = MCPClient()
if "stored_result" not in st.session_state:
    st.session_state.stored_result = {}

query_params = st.query_params
if "q" in query_params:
    st.session_state.input_query = query_params["q"]
 

with st.container():
    st.markdown(
        "<h3 style='text-align:center; color:#D16BA5;'> Search for a product</h3>",
        unsafe_allow_html=True
    )

    query = st.text_input(
        "",
        key="input_query",
        placeholder="e.g. Maybelline Lipstick",
        label_visibility="collapsed"
    )

    if st.button("Compare", key="compare-button", use_container_width=True):
        search = True
    else:
        search = False

#Hidden input field linked to Streamlit
#query = st.text_input("Query", key="input_query", label_visibility="collapsed")
#search = st.button("Compare", key="compare-button")

cleaned_query = query.strip()

def clean_price(p):
    return str(p).replace("Rs.", "₹").replace("INR", "₹") if p else "-"

def extract_numeric_price(p):
    if not p:
        return 0
    match = re.search(r"[\d,]+", str(p))
    if match:
        return int(match.group(0).replace(",", ""))
    return 0

def get_safe_key(url, prefix="wishlist_"):
    return prefix + hashlib.md5(url.encode()).hexdigest()

def show_product_grid(products, title, price_range):
    if not products:
        st.info(f"No products to display for {title}.")
        return

    wishlist_links = {item['link'] for item in load_wishlist(auth["username"])}
    st.markdown(f"### {title}")
    cols = st.columns(min(5, len(products)))

    for i, p in enumerate(products):
        price = extract_numeric_price(p.get("price"))
        if not (price_range[0] <= price <= price_range[1]):
            continue

        link_key = get_safe_key(p['link'] + title + str(i))
        is_wishlisted = p["link"] in wishlist_links

        with cols[i % len(cols)]:
            st.markdown(f"""
            <div style="border:1px solid #f8c7d8; border-radius:12px; padding:10px; text-align:center; height:440px; background-color:#fff0f5;">
                <img src="{p.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                <h5 style="margin-top:10px;">{p.get('brand', '-')}</h5>
                <p style="font-size:13px; height:40px; overflow:hidden;">{p.get('name', '-')}</p>
                <p><strong>{clean_price(p.get('price'))}</strong></p>
                <a href="{p.get('link', '#')}" target="_blank" style="font-size:12px; color:#d16ba5;">View Product</a><br><br>
            """, unsafe_allow_html=True)
            if auth["logged_in"]:
                if st.button("Remove from Wishlist" if is_wishlisted else "Add to Wishlist", key=link_key, use_container_width=True):
                    if is_wishlisted:
                        remove_from_wishlist(p['link'], auth["username"])
                    else:
                        add_to_wishlist(p, auth["username"])
                        st.success("Saved to wishlist!")
                    st.rerun()
            else:
                st.info("Login to use wishlist")

# 🔍 Scrape
if search and cleaned_query:
    with st.spinner("Scraping websites & analyzing matches..."):
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
    st.markdown(f"## Results for **'{cleaned_query}'**")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Myntra Match", f"{res['myntra_match']}%", delta=f"{res['myntra_total']} total")
    col2.metric("AJIO Match", f"{res['ajio_match']}%", delta=f"{res['ajio_total']} total")
    col3.metric("Nykaa Match", f"{res['nykaa_match']}%", delta=f"{res['nykaa_total']} total")
    col4.metric("Amazon Match", f"{res['amazon_match']}%", delta=f"{res['amazon_total']} total")
    col1.progress(res["myntra_match"] / 100)
    col2.progress(res["ajio_match"] / 100)
    col3.progress(res["nykaa_match"] / 100)
    col4.progress(res["amazon_match"] / 100)

    summary = res.get("summary", "-")
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    short_summary = " ".join(sentences[:2]) if len(sentences) >= 2 else summary
    st.success(short_summary)

    with st.expander("Filter Options", expanded=False):
        price_range = st.slider("Filter by price range (₹)", 0, 10000, (0, 10000), step=100)

    tabs = st.tabs(["Myntra", "AJIO", "Nykaa", "Amazon"])
    with tabs[0]: show_product_grid(res.get("top_myntra", []), "Top Products from Myntra", price_range)
    with tabs[1]: show_product_grid(res.get("top_ajio", []), "Top Products from AJIO", price_range)
    with tabs[2]: show_product_grid(res.get("top_nykaa", []), "Top Products from Nykaa", price_range)
    with tabs[3]: show_product_grid(res.get("top_amazon", []), "Top Products from Amazon", price_range)
    
    # 🎯 Matched Products Across Sites
    st.markdown("### Matched Products Across Sites")
    matched = res.get("matched_products", [])
    if matched:
        wishlist_links = {item['link'] for item in load_wishlist(auth["username"])}
        for i, group in enumerate(matched):
            cols = st.columns(4)
            for idx, site in enumerate(["myntra", "ajio", "nykaa", "amazon"]):
                product = group.get(site)
                with cols[idx]:
                    st.markdown(f"<h4 style='text-align:center;'>{site.capitalize()}</h4>", unsafe_allow_html=True)
                    if product:
                        link_key = get_safe_key(product['link'], prefix=f"{site}_match_{i}")
                        is_wishlisted = product["link"] in wishlist_links
                        st.markdown(f"""
                        <div style="border:1px solid #f8c7d8; border-radius:12px; padding:10px; text-align:center; height:440px; background-color:#fff0f5;">
                            <img src="{product.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                            <h5 style="margin-top:10px;">{product.get('brand', '-')}</h5>
                            <p style="font-size:13px; height:40px; overflow:hidden;">{product.get('name', '-')}</p>
                            <p><strong>{clean_price(product.get('price'))}</strong></p>
                            <a href="{product.get('link', '#')}" target="_blank" style="font-size:12px; color:#d16ba5;">View on {site.capitalize()}</a><br><br>
                        """, unsafe_allow_html=True)
                        if auth["logged_in"]:
                            if st.button("Remove from Wishlist" if is_wishlisted else "Add to Wishlist", key=link_key, use_container_width=True):
                                if is_wishlisted:
                                    remove_from_wishlist(product['link'], auth["username"])
                                else:
                                    add_to_wishlist(product, auth["username"])
                                    st.success("Saved to wishlist!")
                                st.rerun()
                        else:
                            st.info("Login to wishlist items")
                    else:
                        st.info("No product found")
    else:
        st.info("No matching products found across sites.")

    # 🤖 AI + Google Suggestions
    st.markdown("### People Also Searched For")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### AI Suggestions")
        try:
            suggestions = generate_suggestions(cleaned_query)
            if suggestions:
                for s in suggestions:
                    suggestion_query = s.replace(" ", "+")
                    st.markdown(f"- [{s}](?q={suggestion_query})", unsafe_allow_html=True)
            else:
                st.info("No AI suggestions available.")
        except Exception as e:
            logger.error("AI suggestion error: " + str(e))
            st.warning("AI suggestions could not be loaded.")

    with col2:
        st.markdown("#### Top Google Searches")
        try:
            api_key = os.getenv("SERPER_API_KEY")
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": cleaned_query})
            data = response.json()
            suggestions = [item.get("title") for item in data.get("organic", [])][:5]
            for s in suggestions:
                st.markdown(f"- {s}")
        except Exception as e:
            logger.error("Serper fetch error: " + str(e))
            st.warning("No Google suggestions available.")
