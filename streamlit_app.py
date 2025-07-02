import streamlit as st
import requests

st.set_page_config(page_title="Product Match Comparator")
st.title("Compare E-commerce Websites")

kw = st.text_input("Enter product keyword (e.g., shoes, jeans):")

if st.button("Compare"):
    if not kw.strip():
        st.warning("Please enter a keyword")
    else:
        res = {}
        with st.spinner("Fetching comparison..."):
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
                st.write(f"Total Myntra items: {res.get('myntra_total', 0)}")
                st.write(f"Total AJIO items: {res.get('ajio_total', 0)}")

                st.markdown(f"**Summary:** {res.get('summary', '-')}\n")

                st.markdown("### Top 5 MYNTRA")
                try:
                    for p in res.get("top_myntra", []):
                        st.markdown(f"- [{p.get('name','N/A')}]({p.get('link','#')}) — **{p.get('price','-')}**")
                except Exception as e:

                    st.warning(f"Error showing Myntra products: {e}")

                st.markdown("### Top 5 AJIO")
                try:
                    for p in res.get("top_ajio", []):
                        st.markdown(f"- [{p.get('name','N/A')}]({p.get('link','#')}) — **{p.get('price','-')}**")
                except Exception as e:
                    st.warning(f"Error showing AJIO products: {e}")

                st.markdown("### Google Search Results")
                try:
                    for link in res.get("serper_links", []):
                        st.markdown(f"- [{link.get('title','Untitled')}]({link.get('link','#')})")
                except Exception as e:
                    st.warning(f"Error showing search links: {e}")

            except requests.exceptions.Timeout:
                st.error("The server took too long to respond (timeout). Try again later.")

            except Exception as e:
                st.error("API error: " + str(e))
                if isinstance(res, dict) and "response" in res:
                    st.warning(res["response"])