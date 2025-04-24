import streamlit as st
import time
import json

st.set_page_config(
    page_title="Online Health Science Knowledge Biomarker Configuration",
    page_icon="👋",
    layout="wide",
)

if not st.session_state.get("is_logged_in"):
    st.switch_page("./Homepage.py")

st.sidebar.success("Welcome, " + st.session_state["username"] + "!")
st.sidebar.page_link(page="./Homepage.py", label="Homepage")
st.sidebar.page_link(page="pages/chatbot.py", label="Chatbot")
st.sidebar.page_link(page="pages/news.py", label="News")
st.sidebar.page_link(page="pages/biomarker.py", label="Biomarker")
if st.session_state.username == "admin":
    st.sidebar.page_link(page="pages/admin.py", label="Admin")

st.markdown("""
<style>
.biomarker-section {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 2rem;
    margin: 1rem 0;
    background: #f8f9fa;
}
.success-box {
    background: #e8f5e9;
    color: #2e7d32;
    padding: 1rem;
    border-radius: 5px;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

if 'enable_biomarker' not in st.session_state:
    st.session_state.enable_biomarker = False
if 'biomarker_data' not in st.session_state:
    st.session_state.biomarker_data = {}


st.title("Biomarker Configuration")


def __change_status():
    status = st.session_state.enable_biomarker
    if status:
        st.session_state.enable_biomarker = False
        st.session_state.biomarker_data = {}
    else:
        st.session_state.enable_biomarker = True


with st.container():
    st.checkbox(
        "Enable Biomarker-Enhanced Chat",
        value=st.session_state.get("enable_biomarker", False),
        on_change=__change_status
    )

if st.session_state.enable_biomarker:
    with st.form("biomarker_form"):
        st.subheader("Basic Physiological Metrics")
        col1, col2 = st.columns(2)
        with col1:
            blood_pressure = st.text_input("Blood Pressure (mmHg)", "120/80")
            heart_rate = st.number_input(
                "Heart Rate (bpm)", min_value=30, max_value=200, value=72)
        with col2:
            body_temp = st.number_input(
                "Body Temperature (°C)", min_value=35.0, max_value=42.0, value=36.6)
            bmi = st.number_input("BMI", min_value=10.0,
                                  max_value=50.0, value=22.0)

        st.subheader("Blood Biochemistry")
        blood_cols = st.columns(3)
        with blood_cols[0]:
            glucose = st.number_input(
                "Glucose (mmol/L)", min_value=2.0, max_value=20.0, value=5.4)
        with blood_cols[1]:
            cholesterol = st.number_input(
                "Total Cholesterol (mmol/L)", min_value=2.0, max_value=10.0, value=4.5)
        with blood_cols[2]:
            hdl = st.number_input(
                "HDL (mmol/L)", min_value=0.5, max_value=3.0, value=1.2)

        st.markdown('</div>', unsafe_allow_html=True)

        if st.form_submit_button("💾 Save Configuration", use_container_width=True):
            biomarker_data = {
                "blood_pressure": blood_pressure,
                "heart_rate": heart_rate,
                "body_temp": body_temp,
                "bmi": bmi,
                "glucose": glucose,
                "cholesterol": cholesterol,
                "hdl": hdl
            }
            with open("user_data/biomarker.json", 'w', encoding='utf-8') as f:
                json.dump(biomarker_data, f, ensure_ascii=False, indent=4)

            success = st.success("Configuration saved successfully!")
            time.sleep(2)
            st.switch_page("pages/chatbot.py")
