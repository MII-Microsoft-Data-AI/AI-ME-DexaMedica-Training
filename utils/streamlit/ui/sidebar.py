import streamlit as st

# Import config
from ..config import COMPANY_LOGO_URL, COMPANY_NAME

# Sidebar navigation - simplified
# st.sidebar.image(COMPANY_LOGO_URL)
# st.sidebar.title(f"{COMPANY_NAME}")
# st.sidebar.markdown("---")


# Navigation
st.sidebar.image(COMPANY_LOGO_URL)
st.sidebar.title(f"{COMPANY_NAME}")
st.sidebar.markdown("---")
page = st.sidebar.selectbox("📍 Navigation", ["🤖 Agent", "📁 Upload"])

# Convert display names back to simple names for routing
page_mapping = {
    "🤖 Agent": "Agent",
    "📁 Upload": "Upload"
}
page = page_mapping[page]