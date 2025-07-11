import streamlit as st
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth.models import User, Wishlist
from dotenv import load_dotenv
import os

# ---------------- ENV + CONFIG ----------------
load_dotenv()
st.set_page_config(page_title="Admin Dashboard", layout="wide")
FLASK_API_URL = os.getenv("FLASK_API_URL", "http://localhost:5000")

# ---------------- CHECK LOGIN SESSION ----------------
auth = {"logged_in": False, "username": None, "role": None}

# Check if cookies are present
if "cookies" not in st.session_state or not st.session_state.get("cookies"):
    st.error("Unauthorized. Please log in as admin through the main app.")
    st.stop()

# Validate session through Flask API
try:
    resp = requests.get(
        f"{FLASK_API_URL}/auth/check_session",
        cookies=st.session_state["cookies"]
    )
    if resp.ok:
        auth.update(resp.json())
    else:
        st.error("Session invalid. Please log in again.")
        st.stop()
except Exception as e:
    st.error("Unable to verify session with Flask API.")
    st.stop()

# Reject non-admins
if not auth["logged_in"] or auth["role"] != "admin":
    st.error("Unauthorized access: Admins only.")
    st.stop()

# ---------------- DATABASE INIT ----------------
DATABASE_URL = "sqlite:///auth/users.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# ---------------- PAGE HEADER ----------------
st.title("Admin Dashboard")
tab1, tab2, tab3, tab4 = st.tabs(["Users", "Wishlists", "Statistics", "Monitoring"])

# ---------------- USERS TAB ----------------
with tab1:
    st.subheader("Registered Users")
    users = session.query(User).all()

    if users:
        df = pd.DataFrame([{"Username": u.username, "Role": u.role} for u in users])
        st.dataframe(df, use_container_width=True)

        for user in users:
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.text(user.username)
            col2.text(user.role)
            if col3.button("Delete", key=f"delete_{user.username}"):
                session.delete(user)
                session.commit()
                st.success(f"Deleted user: {user.username}")
                st.rerun()
    else:
        st.info("No registered users.")

# ---------------- WISHLISTS TAB ----------------
with tab2:
    st.subheader("All User Wishlists")
    wishlists = session.query(Wishlist).all()

    if wishlists:
        df = pd.DataFrame([{
            "User": w.username,
            "Name": w.name,
            "Price": w.price,
            "Link": w.link
        } for w in wishlists])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No wishlists found.")

# ---------------- STATS TAB ----------------
with tab3:
    st.subheader("Platform Statistics")

    total_users = session.query(User).count()
    total_admins = session.query(User).filter_by(role="admin").count()
    total_wishlists = session.query(Wishlist).count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", total_users)
    col2.metric("Admins", total_admins)
    col3.metric("Wishlists", total_wishlists)

    # Role Distribution Chart
    role_df = pd.DataFrame(session.query(User.role).all(), columns=["Role"])
    role_counts = role_df["Role"].value_counts().reset_index()
    role_counts.columns = ["Role", "Count"]
    st.bar_chart(role_counts.set_index("Role"))

# ---------------- MONITORING TAB ----------------
with tab4:
    st.subheader("Integration Monitoring")
    try:
        health = requests.get("http://localhost:8000/health")
        if health.status_code == 200:
            st.success("FastAPI server is up and healthy.")
        else:
            st.warning("FastAPI responded but is unhealthy.")
    except Exception:
        st.error("FastAPI server is not reachable on port 8000.")

# ---------------- LOGOUT ----------------
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Logged out.")
    st.rerun()
