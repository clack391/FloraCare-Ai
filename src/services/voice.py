import io
import asyncio
import edge_tts
import threading

class VoiceService:
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

        # Voice: en-US-AriaNeural is a very standard, pleasant female AI voice.
        voice = "en-US-AriaNeural"
        
        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
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
