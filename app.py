import streamlit as st
import numpy as np
import soundfile as sf
import io
import torch # KPipeline might return torch tensors
from pydub import AudioSegment
from datetime import datetime # To timestamp history entries
import uuid # To give unique keys to history items
from kokoro import KPipeline # <--- ADD THIS LINE HERE

# --- Installation Notes ---
# (Keep installation notes as before)
# 1. Make sure 'kokoro', 'soundfile', 'pydub' are installed: pip install kokoro soundfile pydub
# 2. CRITICAL: 'espeak-ng' must be installed on the system.
#    - Debian/Ubuntu: sudo apt-get update && sudo apt-get install espeak-ng ffmpeg
#    - macOS (brew): brew install espeak-ng ffmpeg
#    - Windows: Requires manual installation or WSL.
# 3. FFmpeg is needed by pydub for MP3 export.

ALL_VOICE_IDS = sorted([
    # (Voice IDs remain the same)
    'af_heart', 'af_alloy', 'af_aoede', 'af_bella', 'af_jessica', 'af_kore',
    'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky', 'am_adam',
    'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa', 'bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily',
    'bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis', 'jf_alpha',
    'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro', 'jm_kumo', 'zf_xiaobei',
    'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi', 'zm_yunjian', 'zm_yunxi',
    'zm_yunxia', 'zm_yunyang', 'ef_dora', 'em_alex', 'em_santa', 'ff_siwis',
    'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi', 'if_sara', 'im_nicola',
    'pf_dora', 'pm_alex', 'pm_santa',
])

# --- Model Loading (Cached) ---
@st.cache_resource
def load_kokoro_pipeline():
    """Loads the Kokoro pipeline. Cached by Streamlit."""
    st.info("Loading Kokoro TTS model... (This happens only once per session)")
    try:
        pipeline = KPipeline(lang_code='a')
        st.success("Kokoro TTS model loaded.")
        return pipeline
    except Exception as e:
        st.error(f"Failed to load Kokoro pipeline: {e}")
        st.warning("Ensure 'espeak-ng' is correctly installed and accessible.")
        st.exception(e)
        return None

# --- Speech Generation Function ---
# (generate_speech_kokoro function remains largely the same)
def generate_speech_kokoro(text, pipeline, voice):
    if not text:
        st.warning("Input text is empty.")
        return None, None
    if pipeline is None:
        st.error("Kokoro pipeline is not loaded.")
        return None, None
    try:
        # st.info(f"Generating audio with voice: {voice}...") # Can be noisy in chat
        generator = pipeline(text, voice=voice)
        audio_chunks = []
        for i, (gs, ps, audio_chunk) in enumerate(generator):
            if torch.is_tensor(audio_chunk):
                audio_chunk = audio_chunk.cpu().numpy()
            if isinstance(audio_chunk, np.ndarray):
                audio_chunks.append(audio_chunk)
        if not audio_chunks:
            st.warning("Model did not generate any audio output.")
            return None, None
        full_audio_waveform = np.concatenate(audio_chunks)
        sampling_rate = 24000 # Kokoro uses 24kHz
        return full_audio_waveform, sampling_rate
    except ValueError as ve:
        if "Voice" in str(ve) and "not found" in str(ve):
            st.error(f"Error: Voice ID '{voice}' not found.")
        else:
            st.error(f"An error occurred during generation: {ve}")
        return None, None
    except Exception as e:
        st.error(f"An unexpected error occurred during audio generation: {e}")
        st.exception(e)
        return None, None

# --- Helper Function for MP3 Conversion (needed for download button) ---
def convert_wav_to_mp3(wav_bytes):
    """Converts WAV bytes to MP3 bytes using pydub."""
    if not wav_bytes:
        return None
    try:
        wav_bytes_io = io.BytesIO(wav_bytes)
        audio_segment = AudioSegment.from_wav(wav_bytes_io)
        mp3_bytes_io = io.BytesIO()
        audio_segment.export(mp3_bytes_io, format="mp3", bitrate="192k")
        mp3_bytes_io.seek(0)
        return mp3_bytes_io.getvalue()
    except Exception as e:
        st.error(f"MP3 conversion failed. Is FFmpeg installed and in PATH?\nError: {e}")
        return None

# --- Main Application ---
def main():
    st.set_page_config(layout="wide", page_title="Kokoro TTS Chat")
    st.title("🗣️ Kokoro TTS Chat")

    # --- Initialize Session State ---
    # `chats`: Dictionary to store all chat sessions. Key is chat_id, Value is list of messages.
    # `active_chat_id`: The ID of the chat currently displayed in the main area.
    # `chat_counter`: Simple way to generate unique chat IDs.
    if 'chats' not in st.session_state:
        st.session_state.chats = {}
    if 'active_chat_id' not in st.session_state:
        st.session_state.active_chat_id = None
    if 'chat_counter' not in st.session_state:
        st.session_state.chat_counter = 0

    # --- Load Model ---
    pipeline = load_kokoro_pipeline()
    if pipeline is None:
        st.error("Application cannot start because the Kokoro pipeline failed to load.")
        st.stop()

    # --- Sidebar ---
    with st.sidebar:
        st.header("Chats")

        # --- New Chat Button ---
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.chat_counter += 1
            new_chat_id = f"chat_{st.session_state.chat_counter}"
            st.session_state.chats[new_chat_id] = {
                "title": f"Chat {st.session_state.chat_counter}", # Store a title
                "messages": [] # Initialize with empty message list
            }
            st.session_state.active_chat_id = new_chat_id
            st.rerun() # Rerun to reflect the new active chat

        st.markdown("---")

        # --- List Existing Chats ---
        # Sort chats by creation order (assuming IDs are sequential)
        # Convert keys to integers for sorting if using the counter method
        try:
             sorted_chat_ids = sorted(
                 st.session_state.chats.keys(),
                 key=lambda x: int(x.split('_')[1]), # Sort by counter number
                 reverse=True # Show newest first
             )
        except: # Fallback if keys aren't in expected format
             sorted_chat_ids = sorted(st.session_state.chats.keys(), reverse=True)


        if not st.session_state.chats:
            st.caption("Start a new chat!")
        else:
            for chat_id in sorted_chat_ids:
                 chat_title = st.session_state.chats[chat_id].get("title", chat_id) # Get title or use ID
                 # Highlight the active chat button
                 button_type = "primary" if chat_id == st.session_state.active_chat_id else "secondary"
                 if st.button(chat_title, key=f"select_{chat_id}", use_container_width=True, type=button_type):
                     st.session_state.active_chat_id = chat_id
                     st.rerun() # Switch to the selected chat

        st.markdown("---")
        st.header("Configuration")
        # --- Voice Selection ---
        default_voice = "af_bella"
        try:
            default_index = ALL_VOICE_IDS.index(default_voice)
        except ValueError:
            default_index = 0

        # Use a consistent key for the voice selector
        selected_voice = st.selectbox(
            "Select Voice:",
            options=ALL_VOICE_IDS,
            index=default_index,
            key="voice_selector_main", # Unique key
            help="Choose a voice. This applies to the next generation in the active chat."
        )

        # --- Dependency Info ---
        with st.expander("Dependency Info"):
            st.markdown("""
            Uses [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).
            **Requires system dependencies:**
            * `espeak-ng`
            * `ffmpeg` (for MP3)
            Install via package manager (e.g., `apt`, `brew`).
            """)

    # --- Main Chat Area ---
    if st.session_state.active_chat_id is None:
        st.info("Start a new chat or select an existing one from the sidebar.")
    else:
        # Get the messages for the active chat
        active_chat_id = st.session_state.active_chat_id
        if active_chat_id not in st.session_state.chats:
             st.error("Selected chat not found. Please start a new chat.")
             st.session_state.active_chat_id = None # Reset active chat
             st.stop()

        messages = st.session_state.chats[active_chat_id]["messages"]

        # --- Display Past Messages ---
        for i, msg in enumerate(messages):
            # Display User Input Text
            with st.chat_message("user"):
                 st.markdown(f"**Text:**\n```\n{msg['text']}\n```")
                 st.caption(f"Voice: {msg['voice']} | Time: {msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

            # Display Assistant Response (Audio)
            with st.chat_message("assistant"):
                 st.audio(msg['wav_bytes'], format='audio/wav')

                 # --- Download Buttons ---
                 col1, col2 = st.columns(2)
                 with col1:
                     st.download_button(
                         label="Download WAV",
                         data=msg['wav_bytes'],
                         file_name=f"{active_chat_id}_msg{i+1}_{msg['voice']}.wav",
                         mime="audio/wav",
                         key=f"wav_dl_{active_chat_id}_{msg['id']}" # Unique key per message
                     )
                 with col2:
                     # Generate MP3 on demand for download
                     mp3_bytes = convert_wav_to_mp3(msg['wav_bytes'])
                     if mp3_bytes:
                          st.download_button(
                              label="Download MP3",
                              data=mp3_bytes,
                              file_name=f"{active_chat_id}_msg{i+1}_{msg['voice']}.mp3",
                              mime="audio/mpeg",
                              key=f"mp3_dl_{active_chat_id}_{msg['id']}" # Unique key per message
                          )
                     else:
                          # Show placeholder if conversion failed
                          st.button("MP3 Error", disabled=True, help="MP3 conversion failed. Check console/logs and ensure FFmpeg is installed.", key=f"mp3_err_{active_chat_id}_{msg['id']}")


        # --- Handle New Input ---
        if prompt := st.chat_input("Enter text for TTS..."):
            # 1. Add user text to messages immediately for display
            # (Although we'll regenerate, this feels more responsive)
            # We might skip this intermediate display if preferred

            # 2. Generate Audio
            with st.spinner("Generating audio..."):
                 audio_waveform, sampling_rate = generate_speech_kokoro(prompt, pipeline, selected_voice)

            # 3. Process and Add to State if Successful
            if audio_waveform is not None and sampling_rate is not None:
                 try:
                     # Convert to WAV bytes
                     wav_bytes_io = io.BytesIO()
                     sf.write(wav_bytes_io, audio_waveform, sampling_rate, format='WAV', subtype='PCM_16')
                     wav_bytes = wav_bytes_io.getvalue()

                     # Create the message entry
                     new_message = {
                         "id": str(uuid.uuid4()), # Unique ID for the message
                         "text": prompt,
                         "voice": selected_voice,
                         "wav_bytes": wav_bytes, # Store WAV bytes
                         "timestamp": datetime.now()
                     }

                     # Append the new message pair to the active chat
                     st.session_state.chats[active_chat_id]["messages"].append(new_message)

                     # Update chat title with first message if it's the default title
                     if st.session_state.chats[active_chat_id]["title"].startswith("Chat ") and len(st.session_state.chats[active_chat_id]["messages"]) == 1:
                          st.session_state.chats[active_chat_id]["title"] = prompt[:30] + "..." # Use first few words as title


                     st.rerun() # Rerun to display the new message

                 except Exception as e:
                      st.error(f"Error processing generated audio: {e}")
            else:
                 st.error("Audio generation failed.")

if __name__ == "__main__":
    main()
