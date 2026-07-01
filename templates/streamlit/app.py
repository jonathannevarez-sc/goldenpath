import os

import streamlit as st

st.set_page_config(page_title="{{SERVICE_NAME}}", page_icon="🛤️")
st.title("{{SERVICE_NAME}}")
st.write("Hello from the Shop Golden Path — Streamlit template.")
st.caption(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")