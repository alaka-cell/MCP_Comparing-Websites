import streamlit as st
import requests
import random
from utils.logger import logger
from mcp_client import MCPClient

st.set_page_config(page_title="🛍️ Product Comparator", layout="wide")

# UI Styling
st.markdown("""
    <style>
        .main { padding: 1rem 2rem; }
        footer {visibility: hidden;}
        h1, h2, h3 { color: #3B3B98; }
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

SUGGESTIONS = ["shoes", "tshirt", "jeans", "kurta", "jacket", "bag", "blush", "moisturizer"]
FORTUNES = [
    "🧧 A great deal is just a click away!",
    "💡 Your next search might surprise you!",
    "✨ Today’s click might bring the trendiest find!",
    "🛍️ Keep calm and keep shopping!"
]

if "client" not in st.session_state:
    st.session_state.client = MCPClient()

if "input_query" not in st.session_state:
    st.session_state.input_query = random.choice(SUGGESTIONS)

st.title("🛒 Myntra vs AJIO: Product Comparator")
st.caption(random.choice(FORTUNES))

query = st.text_input("Search for a product", key="input_query", help="Type a keyword like 'Shoes', 'Blush', etc")
search = st.button("🔍 Compare")

cleaned_query = query.strip()

if search and cleaned_query:
    with st.spinner("Scraping websites & analyzing matches..."):
        res = st.session_state.client.compare_sites(cleaned_query)

    st.markdown(f"## 📊 Results for **'{cleaned_query}'**")

    # Match % Gauge Bars (only one section retained)
    st.subheader("📊 Match Percentage")
    colg1, colg2 = st.columns(2)
    with colg1:
        st.markdown("**Myntra Match %**")
        st.progress(res["myntra_match"] / 100)
        st.caption(f"🔢 Total products: {res['myntra_total']}")
    with colg2:
        st.markdown("**AJIO Match %**")
        st.progress(res["ajio_match"] / 100)
        st.caption(f"🔢 Total products: {res['ajio_total']}")

    # Metric Display
    col1, col2 = st.columns(2)
    col1.metric("🧮 Myntra Matches", f"{res['myntra_match']}%", delta=f"Total: {res['myntra_total']}")
    col2.metric("🧮 AJIO Matches", f"{res['ajio_match']}%", delta=f"Total: {res['ajio_total']}")

    st.markdown("### 📝 Summary")
    st.success(res.get("summary", "-"))

    def clean_price(p):
        return str(p).replace("Rs.", "₹").replace("INR", "₹") if p else "-"

    def show_product_grid(products, title):
        st.markdown(f"### 🛍️ {title}")
        cols = st.columns(5)
        for i, p in enumerate(products):
            with cols[i % 5]:
                st.markdown(f"""
                <div style="border:1px solid #ccc; border-radius:12px; padding:10px; text-align:center; height:360px;">
                    <img src="{p.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                    <h5 style="margin-top:10px;">{p.get('brand', '-')}</h5>
                    <p style="font-size:13px; height:40px; overflow:hidden;">{p.get('name', '-')}</p>
                    <p><strong>💸 {clean_price(p.get('price'))}</strong></p>
                    <a href="{p.get('link', '#')}" target="_blank" style="font-size:12px; color:#007BFF;">🔗 View Product</a>
                </div>
                """, unsafe_allow_html=True)

    show_product_grid(res.get("top_myntra", []), "Top Products from Myntra")
    show_product_grid(res.get("top_ajio", []), "Top Products from AJIO")

    matched = res.get("matched_products", [])
    if matched:
        st.markdown("### 🔁 Matching Products on Both Sites")
        for pair in matched:
            m = pair.get("myntra", {})
            a = pair.get("ajio", {})
            cols = st.columns(2)
            for idx, p in enumerate([m, a]):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:12px; padding:10px; text-align:center; height:360px;">
                        <img src="{p.get("image", "")}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                        <h5 style="margin-top:10px;">{p.get("brand", "-")}</h5>
                        <p style="font-size:13px; height:40px; overflow:hidden;">{p.get("name", "-")}</p>
                        <p><strong>💸 {clean_price(p.get("price"))}</strong></p>
                        <a href="{p.get("link", "#")}" target="_blank" style="font-size:12px; color:#007BFF;">
                        🔗 View on {'Myntra' if idx == 0 else 'AJIO'}</a>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("No matching products found between Myntra and AJIO.")

    st.markdown("### 🔎 Related Google Search Results")
    for item in res.get("serper_links", []):
        st.markdown(f"[🔗 {item['title']}]({item['link']})")

    with st.expander("💡 Suggestions", expanded=False):
        st.markdown("Try searching for one of these popular items:")
        st.write(", ".join(SUGGESTIONS))
