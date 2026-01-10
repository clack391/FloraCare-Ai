import io
import asyncio
import edge_tts
import threading

class VoiceService:
    @staticmethod
    def _clean_text_for_audio(text: str) -> str:
        """
        Prepares text for TTS by removing formatting symbols.
        """
        import re
        
        # 1. Remove Markdown Formatting (Bold, Italic, Header, Links)
        # Remove bold/italic markers (*, **, _, __) but keep text
        text = re.sub(r'[*_]{1,3}', '', text)
        
        # Remove Headers (#)
        text = re.sub(r'#+\s?', '', text)
        
        # Remove Links [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 2. Handle Lists
        # Replace list bullets (-, *, + at start of line) with pauses
        text = re.sub(r'^\s*[-*+]\s+', ', ', text, flags=re.MULTILINE)
        text = text.replace("•", "")
        
        # 3. Replace newlines with full stop pauses
        text = text.replace("\n", ". ")
        
        # 4. Clean up punctuation
        text = re.sub(r'\.+', '.', text)       # '..' -> '.'
        text = re.sub(r'\s+', ' ', text)       # '  ' -> ' '
        
        return text.strip()

    @staticmethod
    def text_to_audio(text: str) -> io.BytesIO:
        """
        Converts text to audio bytes (MP3) using Microsoft Edge TTS (Neural).
        Returns a BytesIO object ready for streaming.
        Uses 'en-US-AriaNeural' for a high-quality, universal sound.
        Runs in a separate thread to isolate from the main Streamlit/Uvicorn event loop (uvloop).
        """
        if not text or not text.strip():
            return None

        # Clean formatting for better speech flow
        clean_text = VoiceService._clean_text_for_audio(text)

        # Voice: en-US-AriaNeural is a very standard, pleasant female AI voice.
        voice = "en-US-AriaNeural"
        
        async def _generate():
            communicate = edge_tts.Communicate(clean_text, voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

        result_holder = {}

        def run_in_thread():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result_holder['data'] = loop.run_until_complete(_generate())
                loop.close()
            except Exception as e:
                result_holder['error'] = e

        # Run the async generation in a dedicated thread
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()

        if 'error' in result_holder:
            print(f"Voice generation error: {result_holder['error']}")
            return None
            
        if 'data' in result_holder:
            buffer = io.BytesIO(result_holder['data'])
            buffer.seek(0)
            return buffer
            
        return None
