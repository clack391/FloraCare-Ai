import streamlit as st
import sys
import os

# Add project root to python path to allow importing 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import httpx
from typing import Optional
from src.frontend.components.voice import VoiceComponent
from src.services.annotator import Annotator
from src.models.schemas import PlantImageAnalysis

# --- Configuration ---
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FloraCare AI",
    page_icon="🌿",
    layout="wide"
)

# --- CSS Styling ---
st.markdown("""
<style>
.weather-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
}
.report-header {
    margin-top: 0px;
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_ip_location() -> str:
    """Detects location via IP."""
    try:
        resp = httpx.get("http://ip-api.com/json/", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city", "London")
            country_code = data.get("countryCode", "UK")
            return f"{city},{country_code}"
    except Exception:
        pass
    return "London,UK" # Fallback

def check_backend_status():
    """Checks if API is reachable."""
    try:
        r = httpx.get(f"{API_URL}/health", timeout=1.0)
        return r.status_code == 200
    except:
        return False

# --- Sidebar ---
st.sidebar.title("Settings ⚙️")

# Backend Status
is_online = check_backend_status()
if is_online:
    st.sidebar.success("✅ Backend Online")
else:
    st.sidebar.error("❌ Backend Offline")

# Initialize Session State for Location if not set
if 'user_location' not in st.session_state:
    st.session_state['user_location'] = get_ip_location()

location = st.sidebar.text_input("📍 Your Location", value=st.session_state['user_location'])

st.sidebar.markdown("---")
st.sidebar.info("FloraCare AI is running in stateless mode. No data is stored.")

# --- Main Page ---
st.title("FloraCare AI 🌿")
st.markdown("### Intelligent Plant Diagnosis System")

# Voice Input Section
st.divider()
col_v1, col_v2 = st.columns([1, 4])
with col_v1:
    st.write("🎙️ **Voice Query**")
with col_v2:
    voice_text = VoiceComponent.render()

# Text Input for Targeted Query
text_query = st.text_input("💬 Ask a specific question (e.g. 'Is this contagious?')", value="")

# Combine Inputs (Text overrides Voice if both present, or concatenate? Let's prefer Text if typed, else Voice)
final_query = text_query if text_query else voice_text

# Image Input
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display Original Image if no analysis yet, otherwise we might show annotated
    if 'diagnosis_result' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    
    # Analyze Button
    if st.button("Analyze Plant 🔍", type="primary"):
        with st.spinner("Analyzing visual symptoms, fetching weather, and checking knowledge base..."):
            try:
                # Prepare Request
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                data = {
                    "location": location,
                    "user_query": final_query
                }
                
                # Call Backend
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(f"{API_URL}/diagnose", files=files, data=data)
                    
                if response.status_code == 200:
                    report = response.json()
                    st.session_state['diagnosis_result'] = report
                    st.session_state['last_file'] = uploaded_file.name
                    
                    # --- Process Annotation ---
                    try:
                        analysis_obj = PlantImageAnalysis(**report['analysis'])
                        annotated_bytes = Annotator.draw_boxes(uploaded_file.getvalue(), analysis_obj)
                        st.session_state['annotated_image'] = annotated_bytes
                    except Exception as e:
                        print(f"Annotation error: {e}")
                        st.session_state['annotated_image'] = uploaded_file.getvalue()
                    

                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except httpx.ConnectError:
                st.error("Cannot connect to Backend API. Is it running? (http://localhost:8000)")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Render Results (Persistent) ---
if 'diagnosis_result' in st.session_state and st.session_state.get('last_file') == (uploaded_file.name if uploaded_file else ""):
    report = st.session_state['diagnosis_result']
    
    st.divider()
    st.success("Analysis Complete!")
    
    # Layout: Image Left, Details Right
    r_col1, r_col2 = st.columns([1, 1])
    
    with r_col1:
        st.subheader("Visual Findings")
        if 'annotated_image' in st.session_state:
            st.image(st.session_state['annotated_image'], caption="Detected Symptoms (Annotated)", use_container_width=True)
        
        with st.expander("Detailed Description"):
            st.write(report['analysis']['description'])

    with r_col2:
        st.subheader(f"Diagnosis: {report['diagnosis']}")
        
        # Direct Answer Section
        if report.get('user_query_answer'):
            st.info(f"**Answer to your question:** {report['user_query_answer']}")
        
        # Severity Metrics
        sev = report['analysis'].get('severity_score')
        area = report['analysis'].get('affected_area')
        if sev:
            st.metric("Severity Score", f"{sev}/10", delta_color="inverse")
        if area:
            st.metric("Affected Area", area)
        
        # Weather
        weather = report.get('weather_context')
        if weather:
            st.markdown(f"""
            <div class="weather-card">
                <b>🌥️ Weather Context</b><br>
                {weather['condition']}<br>
                {weather['temperature']}°C | {weather['humidity']}% Humidity
            </div>
            """, unsafe_allow_html=True)
            
        # Symptoms
        st.write("**Identified Symptoms:**")
        for s in report['analysis']['visual_symptoms']:
            st.markdown(f"- {s}")
            
        # Treatment
        st.subheader("💊 Treatment Plan")
        for step in report['treatment_plan']:
            st.markdown(f"- {step}")

    # Sources
    with st.expander("📚 Knowledge Sources"):
        for ref in report['relevant_knowledge']:
            st.info(ref)

    # --- Chat Session (New) ---
    st.divider()
    st.subheader("💬 Chat with FloraCare AI")
    
    # Initialize Chat History for THIS diagnosis
    # We reset if the diagnosis changes
    if 'last_chat_diagnosis_id' not in st.session_state or st.session_state['last_chat_diagnosis_id'] != uploaded_file.name:
         st.session_state['chat_history'] = []
         st.session_state['last_chat_diagnosis_id'] = uploaded_file.name

    # Display History
    for msg in st.session_state['chat_history']:
        with st.chat_message(msg['role']):
            st.write(msg['content'])

    # Input
    if user_input := st.chat_input("Ask a follow-up question (e.g. 'How much water specifically?')"):
        # Add User Message to UI
        st.session_state['chat_history'].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
            
        # Call Backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "message": user_input,
                        "context": report,
                        "history": st.session_state['chat_history'][:-1] # Exclude current message? Or include? API expects history BEFORE current msg usually, or we handle it. Simple protocol: pass history including recent? Schema says 'history' is previous.
                    }
                    # Schema adjustment: API expects 'history' list of objects.
                    
                    res = httpx.post(f"{API_URL}/chat", json=payload, timeout=30.0)
                    if res.status_code == 200:
                        bot_response = res.json()['response']
                        st.write(bot_response)
                        st.session_state['chat_history'].append({"role": "assistant", "content": bot_response})
                    else:
                         st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Chat Error: {e}")
