import streamlit as st
import sys
import os

# Add project root to python path to allow importing 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import httpx
from typing import Optional
from src.frontend.components.voice import VoiceComponent
from src.services.annotator import Annotator
from src.services.voice import VoiceService
from src.services.pdf_generator import generate_pdf_report
from src.models.schemas import PlantImageAnalysis
import tempfile
from concurrent.futures import ThreadPoolExecutor
import time

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

def call_backend_api(files, data):
    """Blocking call to be run in a thread."""
    with httpx.Client(timeout=300.0) as client:
        response = client.post(f"{API_URL}/diagnose", files=files, data=data)
        return response

STATUS_STEPS = [
    "Scanning leaf texture and discoloration...",
    "Identifying plant species...",
    "Analyzing visual symptoms (necrosis, chlorosis)...",
    "Cross-referencing with Knowledge Base...",
    "Fetching localized weather data...",
    "Calculating confidence scores...",
    "Generating treatment plan..."
]

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
                
                # Call Backend with Dynamic Status
                with st.status("🚀 Starting FloraCare Agent...", expanded=True) as status:
                    with ThreadPoolExecutor() as executor:
                        future = executor.submit(call_backend_api, files, data)
                        
                        step_index = 0
                        while not future.done():
                            # Cycle through updates
                            msg = STATUS_STEPS[step_index % len(STATUS_STEPS)]
                            status.update(label=msg, state="running")
                            time.sleep(1.5)
                            step_index += 1
                        
                        # Get Result
                        response = future.result()
                        
                        if response.status_code == 200:
                            status.update(label="✅ Diagnosis Complete!", state="complete", expanded=False)
                        else:
                            status.update(label="❌ Connection Failed", state="error")
                    
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

    import re
    # Sources
    with st.expander("📚 Knowledge Sources"):
        for ref in report['relevant_knowledge']:
            # Try to extract " (Source: ...)"
            match = re.search(r"(.*) \(Source: (.*)\)$", ref)
            if match:
                content, source_name = match.groups()
                st.markdown(f"**Source: {source_name}**")
                st.info(content)
            else:
                st.info(ref)
            
    # Read Diagnosis Button
    if st.button("🔊 Read Full Diagnosis", key="read_diagnosis"):
        with st.spinner("Generating audio..."):
            # Construct narrative
            narrative = f"Diagnosis: {report['diagnosis']}. Description: {report['analysis']['description']}. Treatment Plan: {'. '.join(report['treatment_plan'])}"
            audio_bytes = VoiceService.text_to_audio(narrative)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
                
    st.divider()
    
    # Download Report Button
    # Prepare data
    conf = report['analysis'].get('confidence', 0.0)
    # Simple logic for trust label to match report style
    if conf > 0.85:
        t_label = "HIGH"
    elif conf > 0.60:
        t_label = "MEDIUM"
    else:
        t_label = "LOW"
        

    # Optimized Download Flow:
    # Since generating PDF might be fast, let's pre-generate or generate on click if we can.
    # Actually, st.download_button needs the data.
    # Let's simple create a "Prepare Download" button or just do it.
    # Given it uses fpdf, it's fast. Let's try to generate it ONLY when users asks, 
    # BUT st.download_button requires the file object.
    
    # Alternative: Put the generation inside the button logic? No, download_button IS the trigger.
    # Let's do this:
    # We will generate the PDF *automatically* when the report is shown, so the button is ready.
    # It's local and fast.
    
    file_ext = uploaded_file.type.split('/')[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_img:
        tmp_img.write(uploaded_file.getvalue())
        tmp_img_path = tmp_img.name
    
    
    try:
        # Prepare data for new PDF function
        diagnosis_data = {
            "disease_name": report['diagnosis'],
            "confidence_score": f"{conf * 100:.1f}%",
            "trust_label": t_label,
            "weather_context": f"{report.get('weather_context', {}).get('condition', 'N/A')}, {report.get('weather_context', {}).get('temperature', 'N/A')}°C, {report.get('weather_context', {}).get('humidity', 'N/A')}% Humidity" if report.get('weather_context') else None,
            "visual_symptoms": report['analysis']['visual_symptoms'],
            "analysis": report['analysis']['description'],
            "treatment_plan": report['treatment_plan']
        }
        
        pdf_path = generate_pdf_report(tmp_img_path, diagnosis_data)
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            
        st.download_button(
            label="📄 Download Official Report",
            data=pdf_bytes,
            file_name="FloraCare_Report.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")

    # --- Chat Session (New) ---
    st.divider()
    st.subheader("💬 Chat with FloraCare AI")
    
    # Initialize Chat History for THIS diagnosis
    # We reset if the diagnosis changes
    if 'last_chat_diagnosis_id' not in st.session_state or st.session_state['last_chat_diagnosis_id'] != uploaded_file.name:
         st.session_state['chat_history'] = []
         st.session_state['last_chat_diagnosis_id'] = uploaded_file.name

    # Display History
    for idx, msg in enumerate(st.session_state['chat_history']):
        with st.chat_message(msg['role']):
            st.write(msg['content'])
            # Add Read Button for Assistant messages
            if msg['role'] == 'assistant':
                if st.button("🔊", key=f"read_chat_{idx}"):
                     audio = VoiceService.text_to_audio(msg['content'])
                     if audio:
                         st.audio(audio, format='audio/mp3')

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
