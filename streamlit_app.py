import streamlit as st
import requests
import random

SUGGESTIONS = ["shoes", "tshirt", "jeans", "kurta", "jacket", "bag", "dress", "watch"]

FORTUNES = [
    "🧧 A great deal is just a click away!",
    "💡 Your next search might surprise you!",
    "✨ Today’s click might bring the perfect pick!",
    "📦 You will discover something stylish and unexpected.",
    "🎁 Don’t wait—your dream product awaits!",
    "🛒 Shopping karma is on your side today!",
]

st.set_page_config(page_title="Product Match Comparator", layout="wide")
st.title("🛍️ Product Match Comparator")

kw = st.text_input("Enter product keyword:", placeholder="e.g., shoes, kurta, dress")

if not kw:
    st.markdown("💡 Try: " + ", ".join(random.sample(SUGGESTIONS, 3)))

if kw.strip().lower() == "meowmode":
    st.balloons()
    st.markdown("## 🐾 Secret Mode Activated: Meow Mode!")
    st.markdown("### You found the hidden cat cave 🎉")
    st.markdown(
        f'<div style="text-align:center;"><img src="https://custom-doodle.com/wp-content/uploads/doodle/auto-draft/kawaii-white-cat-shaking-head-doodle.gif" width="180"/></div>',
        unsafe_allow_html=True
    )
    st.markdown("> _Here’s your lucky dancing cat blessing for the day!_ 😸")

elif kw.strip().lower() == "fortunemode":
    st.markdown("## 🥠 Fortune Cookie Mode")
    st.markdown("✨ Here's your digital fortune:")
    st.success(random.choice(FORTUNES))

elif st.button("Compare"):
    if not kw.strip():
        st.warning("Please enter a keyword.")
    else:
        res = {}
        with st.spinner("🔍 Fetching comparison..."):
            try:
                response = requests.post(
                    "http://localhost:8000/compare",
                    json={"keyword": kw},
                    timeout=90
                )
                res = response.json()

                if not isinstance(res, dict):
                    st.error("Unexpected response format from server.")
                    st.stop()

                st.success("Comparison Results")

                st.metric("Myntra Match %", f"{res.get('myntra_match', 0)}%")
                st.metric("AJIO Match %", f"{res.get('ajio_match', 0)}%")
                st.write(f"**Total Myntra items:** {res.get('myntra_total', 0)}")
                st.write(f"**Total AJIO items:** {res.get('ajio_total', 0)}")

                st.markdown("### 📝 Summary")
                st.write(res.get("summary", "-"))

                st.markdown("### 🛍️ Top 5 MYNTRA")
                for p in res.get("top_myntra", []):
                    st.markdown(f"- [{p.get('name', 'N/A')}]({p.get('link', '#')}) — **{p.get('price', '-')}**")

                st.markdown("### 👗 Top 5 AJIO")
                for p in res.get("top_ajio", []):
                    st.markdown(f"- [{p.get('name', 'N/A')}]({p.get('link', '#')}) — **{p.get('price', '-')}**")

                st.markdown("### 🔗 Google Search Results")
                for link in res.get("serper_links", []):
                    st.markdown(f"- [{link.get('title', 'Untitled')}]({link.get('link', '#')})")

            except requests.exceptions.Timeout:
                st.error("The server took too long to respond (timeout). Try again later.")
            except Exception as e:
                st.error("API error: " + str(e))
                if isinstance(res, dict) and "response" in res:
                    st.warning(res["response"])
