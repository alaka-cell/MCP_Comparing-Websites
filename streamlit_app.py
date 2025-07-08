import streamlit as st
import random
from utils.logger import logger
from mcp_client import MCPClient

st.set_page_config(page_title="🛍️ Product Comparator", layout="wide")

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
    "💋 Your perfect shade is just a click away!",
    "💄 One swipe could change your look forever!",
    "✨ Today’s glam find might be hiding in plain sight!",
    "🌸 Beauty begins the moment you start searching!",
    "🔮 A glow-up is only one product away!",
    "🧴 Self-care starts with the right pick!",
    "🎯 Find your holy grail product today!",
    "🌟 Slay the day with your next beauty buy!"
]

if "client" not in st.session_state:
    st.session_state.client = MCPClient()

if "input_query" not in st.session_state:
    st.session_state.input_query = random.choice(SUGGESTIONS)

if "stored_result" not in st.session_state:
    st.session_state.stored_result = {}

st.title("🛒 All things beauty comparator")
st.caption(random.choice(FORTUNES))

query = st.text_input("Search for a product", key="input_query", help="Type a keyword like 'Shoes', 'Blush', etc")
search = st.button("🔍 Compare")

cleaned_query = query.strip()

def clean_price(p):
    return str(p).replace("Rs.", "₹").replace("INR", "₹") if p else "-"

def show_product_grid(products, title):
    if not products:
        st.info(f"No products to display for {title}.")
        return
    st.markdown(f"### 🛍️ {title}")
    cols = st.columns(5)
    for i, p in enumerate(products):
        rating = p.get("rating")
        rating_display = f"⭐ {rating}" if rating else ""
        with cols[i % 5]:
            st.markdown(f"""
            <div style="border:1px solid #ccc; border-radius:12px; padding:10px; text-align:center; height:390px;">
                <img src="{p.get('image', '')}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                <h5 style="margin-top:10px;">{p.get('brand', '-')}</h5>
                <p style="font-size:13px; height:40px; overflow:hidden;">{p.get('name', '-')}</p>
                <p><strong>💸 {clean_price(p.get('price'))}</strong></p>
                <p style="font-size:13px;">{rating_display}</p>
                <a href="{p.get('link', '#')}" target="_blank" style="font-size:12px; color:#007BFF;">🔗 View Product</a>
            </div>
            """, unsafe_allow_html=True)

# 🔍 Fetch results (summary always generated)
if search and cleaned_query:
    with st.spinner("Scraping websites & analyzing matches..."):
        try:
            res = st.session_state.client.compare_sites(cleaned_query)
            st.session_state.stored_result = res
        except Exception as e:
            logger.error("Error calling MCPClient.compare_sites(): " + str(e))
            st.error("Something went wrong while fetching results.")
            st.stop()

# 💡 Display results if available
if st.session_state.stored_result:
    res = st.session_state.stored_result
    st.markdown(f"## 📊 Results for **'{cleaned_query}'**")

    st.subheader("📊 Match Percentage")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧮 Myntra Match", f"{res['myntra_match']}%", delta=f"{res['myntra_total']} total")
    col2.metric("🧮 AJIO Match", f"{res['ajio_match']}%", delta=f"{res['ajio_total']} total")
    col3.metric("🧮 Nykaa Match", f"{res['nykaa_match']}%", delta=f"{res['nykaa_total']} total")
    col4.metric("🧮 Amazon Match", f"{res['amazon_match']}%", delta=f"{res['amazon_total']} total")

    col1.progress(res["myntra_match"] / 100)
    col2.progress(res["ajio_match"] / 100)
    col3.progress(res["nykaa_match"] / 100)
    col4.progress(res["amazon_match"] / 100)

    # 📝 Always show summary
    st.markdown("### 📝 Summary")
    st.success(res.get("summary", "-"))

    show_product_grid(res.get("top_myntra", []), "Top Products from Myntra")
    show_product_grid(res.get("top_ajio", []), "Top Products from AJIO")
    show_product_grid(res.get("top_nykaa", []), "Top Products from Nykaa")
    show_product_grid(res.get("top_amazon", []), "Top Products from Amazon")

    matched = res.get("matched_products", [])
    if matched:
        st.markdown("### 🔁 Matched Products Across Sites")
        for group in matched:
            cols = st.columns(4)
            for idx, site in enumerate(["myntra", "ajio", "nykaa", "amazon"]):
                product = group.get(site)
                with cols[idx]:
                    st.markdown(f"<h4 style='text-align:center;'>{site.capitalize()}</h4>", unsafe_allow_html=True)
                    if not product:
                        st.markdown(
                            """
                            <div style='
                                border: 1px dashed #555;
                                border-radius: 12px;
                                padding: 20px;
                                text-align: center;
                                color: #999;
                                font-size: 16px;
                                height: 390px;
                                display: flex;
                                flex-direction: column;
                                justify-content: center;
                                align-items: center;
                            '>
                                <span style='font-size: 36px;'>🔍</span>
                                <em style='margin-top: 10px;'>No product found</em>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        rating = product.get("rating")
                        rating_display = f"⭐ {rating}" if rating else ""
                        st.markdown(f"""
                        <div style="border:1px solid #ccc; border-radius:12px; padding:10px; text-align:center; height:390px;">
                            <img src="{product.get("image", "")}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;" />
                            <h5 style="margin-top:10px;">{product.get("brand", "-")}</h5>
                            <p style="font-size:13px; height:40px; overflow:hidden;">{product.get("name", "-")}</p>
                            <p><strong>💸 {clean_price(product.get("price"))}</strong></p>
                            <p style="font-size:13px;">{rating_display}</p>
                            <a href="{product.get("link", "#")}" target="_blank" style="font-size:12px; color:#007BFF;">🔗 View on {site.capitalize()}</a>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No matching products found across sites.")

    st.markdown("### 🔎 Related Google Search Results")
    for item in res.get("serper_links", []):
        st.markdown(f"[🔗 {item['title']}]({item['link']})")

    with st.expander("💡 Suggestions", expanded=False):
        st.markdown("Try searching for one of these popular items:")
        st.write(", ".join(SUGGESTIONS))
