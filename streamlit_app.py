import streamlit as st
import random
import hashlib
from utils.logger import logger
from mcp_client import MCPClient
from utils.wishlist_manager import load_wishlist, add_to_wishlist, remove_from_wishlist
from utils.ai_suggestor import generate_suggestions, generate_comparison_summary

st.set_page_config(page_title="🍭 Product Comparator", layout="wide")

# 📌 Wishlist Sidebar
with st.sidebar.expander("Wishlist", expanded=True):
    wishlist = load_wishlist()
    if wishlist:
        for item in wishlist:
            unique_key = "remove_" + hashlib.md5(item['link'].encode()).hexdigest()
            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"""
                    <div style="margin-top:5px">
                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#3B3B98;">
                            <strong>{item['name']}</strong>
                        </a><br>
                        💸 {item['price']}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("❌", key=unique_key):
                        remove_from_wishlist(item['link'])
                        st.rerun()
    else:
        st.info("No items wishlisted yet.")

# 🖼️ UI Styling
st.markdown("""
    <style>
        .main { padding: 1rem 2rem; }
        footer {visibility: hidden;}
        .block-container { padding-top: 1.5rem; }
        .tag {
            display: inline-block;
            background-color: #f0f0f5;
            color: #333;
            border-radius: 20px;
            padding: 6px 14px;
            margin: 5px 8px 5px 0;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid #bbb;
        }
        .suggestion-link {
            display: inline-block;
            color: #3B3B98;
            margin: 6px 10px 6px 0;
            cursor: pointer;
            text-decoration: underline;
            font-weight: 500;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

# Fortune Caption
FORTUNES = [
    "💋 Your perfect shade is just a click away!",
    "💄 One swipe could change your look forever!",
    "✨ Today’s glam find might be hiding in plain sight!",
    "🌸 Beauty begins the moment you start searching!",
    "🔮 A glow-up is only one product away!",
    "🧴 Self-care starts with the right pick!",
    "🎯 Find your holy grail product today!",
    "🌟 Slay the day with your next beauty buy!"
]

st.title("💼 All things beauty comparator")
st.caption(random.choice(FORTUNES))

# Init state
if "client" not in st.session_state:
    st.session_state.client = MCPClient()
if "stored_result" not in st.session_state:
    st.session_state.stored_result = {}

# Handle query from AI suggestion clicks
query_params = st.query_params
if "q" in query_params:
    st.session_state.input_query = query_params["q"]

# Input box without default value
query = st.text_input("Search for a product", key="input_query")
search = st.button("🔍 Compare")
cleaned_query = query.strip()

def clean_price(p):
    return str(p).replace("Rs.", "₹").replace("INR", "₹") if p else "-"

def get_safe_key(url, prefix="wishlist_"):
    return prefix + hashlib.md5(url.encode()).hexdigest()

def show_product_grid(products, title, price_range):
    if not products:
        st.info(f"No products to display for {title}.")
        return

    wishlist_links = {item['link'] for item in load_wishlist()}
    st.markdown(f"### 💼 {title}")
    cols = st.columns(min(5, len(products)))

    for i, p in enumerate(products):
        try:
            price = int(str(p.get("price", "0")).replace("₹", "").replace(",", "").strip())
        except:
            price = 0

        if not (price_range[0] <= price <= price_range[1]):
            continue

        link_key = get_safe_key(p['link'] + title + str(i))  # Ensure unique key with index
        is_wishlisted = p["link"] in wishlist_links

        with cols[i % len(cols)]:
            st.markdown(f"""
            <div style="border:1px solid #ccc; border-radius:12px; padding:10px; text-align:center; height:440px; position:relative;">
                <img src="{p.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                <h5 style="margin-top:10px;">{p.get('brand', '-')}</h5>
                <p style="font-size:13px; height:40px; overflow:hidden;">{p.get('name', '-')}</p>
                <p><strong>💸 {clean_price(p.get('price'))}</strong></p>
                <a href="{p.get('link', '#')}" target="_blank" style="font-size:12px; color:#007BFF;">🔗 View Product</a><br>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Add to Wishlist" if not is_wishlisted else "Remove from Wishlist", key=link_key):
                if is_wishlisted:
                    remove_from_wishlist(p['link'])
                else:
                    add_to_wishlist(p)
                    st.success("Saved to wishlist!")
                st.rerun()

# Scrape if button clicked
if search and cleaned_query:
    with st.spinner("Scraping websites & analyzing matches..."):
        try:
            res = st.session_state.client.compare_sites(cleaned_query)
            st.session_state.stored_result = res
        except Exception as e:
            logger.error("Error calling compare_sites(): " + str(e))
            st.error("Something went wrong while fetching results.")
            st.stop()

# Results
if st.session_state.stored_result:
    res = st.session_state.stored_result
    st.markdown(f"## 📊 Results for **'{cleaned_query}'**")

    st.subheader("📊 Match Percentage")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧾 Myntra Match", f"{res['myntra_match']}%", delta=f"{res['myntra_total']} total")
    col2.metric("🧾 AJIO Match", f"{res['ajio_match']}%", delta=f"{res['ajio_total']} total")
    col3.metric("🧾 Nykaa Match", f"{res['nykaa_match']}%", delta=f"{res['nykaa_total']} total")
    col4.metric("🧾 Amazon Match", f"{res['amazon_match']}%", delta=f"{res['amazon_total']} total")

    col1.progress(res["myntra_match"] / 100)
    col2.progress(res["ajio_match"] / 100)
    col3.progress(res["nykaa_match"] / 100)
    col4.progress(res["amazon_match"] / 100)

    st.markdown("### 📝 Summary")
    st.success(res.get("summary", "-"))

    with st.expander("🧰 Filter Options", expanded=False):
        price_range = st.slider("Filter by price range (₹)", 0, 10000, (0, 10000), step=100)

    tabs = st.tabs(["💼 Myntra", "💼 AJIO", "💼 Nykaa", "💼 Amazon"])
    with tabs[0]:
        show_product_grid(res.get("top_myntra", []), "Top Products from Myntra", price_range)
    with tabs[1]:
        show_product_grid(res.get("top_ajio", []), "Top Products from AJIO", price_range)
    with tabs[2]:
        show_product_grid(res.get("top_nykaa", []), "Top Products from Nykaa", price_range)
    with tabs[3]:
        show_product_grid(res.get("top_amazon", []), "Top Products from Amazon", price_range)

    st.markdown("### ♻️ Matched Products Across Sites")
    matched = res.get("matched_products", [])
    if matched:
        wishlist_links = {item['link'] for item in load_wishlist()}
        for i, group in enumerate(matched):
            cols = st.columns(4)
            for idx, site in enumerate(["myntra", "ajio", "nykaa", "amazon"]):
                product = group.get(site)
                with cols[idx]:
                    st.markdown(f"<h4 style='text-align:center;'>{site.capitalize()}</h4>", unsafe_allow_html=True)
                    if not product:
                        st.markdown("""<div style='border: 1px dashed #555; border-radius: 12px; padding: 20px; text-align: center; color: #999; font-size: 16px; height: 390px; display: flex; flex-direction: column; justify-content: center; align-items: center;'><span style='font-size: 36px;'>🔍</span><em style='margin-top: 10px;'>No product found</em></div>""", unsafe_allow_html=True)
                    else:
                        link_key = get_safe_key(product['link'], prefix=f"{site}_match_{i}")
                        is_wishlisted = product["link"] in wishlist_links
                        st.markdown(f"""
                        <div style="border:1px solid #ccc; border-radius:12px; padding:10px; text-align:center; height:440px; position:relative;">
                            <img src="{product.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                            <h5 style="margin-top:10px;">{product.get('brand', '-')}</h5>
                            <p style="font-size:13px; height:40px; overflow:hidden;">{product.get('name', '-')}</p>
                            <p><strong>💸 {clean_price(product.get('price'))}</strong></p>
                            <a href="{product.get('link', '#')}" target="_blank" style="font-size:12px; color:#007BFF;">🔗 View on {site.capitalize()}</a><br>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Add to Wishlist" if not is_wishlisted else "Remove from Wishlist", key=link_key):
                            if is_wishlisted:
                                remove_from_wishlist(product['link'])
                            else:
                                add_to_wishlist(product)
                                st.success("Saved to wishlist!")
                            st.rerun()
    else:
        st.info("No matching products found across sites.")

    # 🧠 AI Suggestions via Ollama
    st.markdown("### 🧠 People Also Searched For...")
    try:
        suggestions = generate_suggestions(cleaned_query)
        if suggestions:
            for s in suggestions:
                suggestion_query = s.replace(" ", "+")
                st.markdown(f"[🔎 {s}](?q={suggestion_query})", unsafe_allow_html=True)
        else:
            st.info("No AI suggestions available.")
    except Exception as e:
        logger.error("Failed to get AI suggestions: " + str(e))
        st.warning("AI suggestions could not be loaded.")
