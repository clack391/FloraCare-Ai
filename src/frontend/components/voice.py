import streamlit as st
import io
import os
import torch

# Try importing whisper, handle if missing
try:
    import whisper
    import numpy as np
    import soundfile as sf
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("WARNING: openai-whisper or dependencies not found.")

class VoiceComponent:
    _model = None

    @classmethod
    def load_model(cls):
        if cls._model is None and HAS_WHISPER:
            with st.spinner("Loading Voice Model (this may take a moment)..."):
                # Use "base" or "tiny" for speed on CPU
                cls._model = whisper.load_model("base", device="cpu") 
        return cls._model

    @staticmethod
    def render() -> str:
        """Renders the audio input and returns transcribed text (or empty string)."""
        if not HAS_WHISPER:
            st.warning("Voice features unavailable (missing dependencies).")
            return ""

        audio_value = st.audio_input("🎤 Record Voice Query")
        
        if audio_value:
            # Transcribe
            model = VoiceComponent.load_model()
            if model:
                # Convert UploadedFile (BytesIO) to numpy array for Whisper
                # Whisper expects path or numpy array
                # We can save to temp file to be safe/easy with Whisper's load_audio logic
                # or use soundfile to read into numpy
                try:
                    data, samplerate = sf.read(io.BytesIO(audio_value.getvalue()))
                    # Whisper expects float32
                    data = data.astype(np.float32)
                    
                    result = model.transcribe(data)
                    text = result["text"]
                    st.info(f"Transcribed: '{text}'")
                    return text.strip()
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
                    
        return ""
