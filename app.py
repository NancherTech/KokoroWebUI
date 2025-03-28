import streamlit as st
import numpy as np
import soundfile as sf
import io
import torch # KPipeline might return torch tensors
from pydub import AudioSegment
# --- Installation Notes ---
# 1. Make sure 'kokoro' and 'soundfile' are installed: pip install kokoro soundfile
# 2. CRITICAL: 'espeak-ng' must be installed on the system.
#    - Debian/Ubuntu: sudo apt-get update && sudo apt-get install espeak-ng
#    - macOS (brew): brew install espeak-ng
#    - Windows: Requires manual installation or WSL.
#    This dependency might prevent deployment on standard Streamlit Community Cloud.

ALL_VOICE_IDS = sorted([
    # American English
    'af_heart', 'af_alloy', 'af_aoede', 'af_bella', 'af_jessica', 'af_kore',
    'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky', 'am_adam',
    'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx',
    'am_puck', 'am_santa',
    # British English
    'bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily', 'bm_daniel', 'bm_fable',
    'bm_george', 'bm_lewis',
    # Japanese
    'jf_alpha', 'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro', 'jm_kumo',
    # Mandarin Chinese
    'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi', 'zm_yunjian',
    'zm_yunxi', 'zm_yunxia', 'zm_yunyang',
    # Spanish
    'ef_dora', 'em_alex', 'em_santa',
    # French
    'ff_siwis',
    # Hindi
    'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi',
    # Italian
    'if_sara', 'im_nicola',
    # Brazilian Portuguese
    'pf_dora', 'pm_alex', 'pm_santa',
])


try:
    from kokoro import KPipeline
except ImportError:
    st.error(
        "ERROR: Could not import `KPipeline` from `kokoro`.\n"
        "1. Ensure 'kokoro' is installed (`pip install kokoro`).\n"
        "2. Ensure 'espeak-ng' is installed on your system (see code comments for instructions)."
    )
    # Optionally add platform-specific instructions or links here
    st.stop() # Stop the app if prerequisites aren't met
except Exception as e:
    st.error(f"An unexpected error occurred during import: {e}")
    st.exception(e)
    st.stop()


# Cache the pipeline loading to avoid reloading on every interaction
@st.cache_resource
def load_kokoro_pipeline():
    """Loads the Kokoro pipeline. Cached by Streamlit."""
    try:
        # Using lang_code='a' as per the official example
        # You could change this e.g., to 'en' if needed
        pipeline = KPipeline(lang_code='a')
        return pipeline
    except Exception as e:
        # Catch potential errors during pipeline initialization
        st.error(f"Failed to load Kokoro pipeline: {e}")
        st.warning("Ensure 'espeak-ng' is correctly installed and accessible.")
        st.exception(e)
        return None

def generate_speech_kokoro(text, pipeline, voice):
    """
    Generates speech using the loaded Kokoro KPipeline.

    Args:
        text (str): Text to synthesize.
        pipeline (KPipeline): The loaded Kokoro pipeline instance.
        voice (str): The voice ID to use (e.g., 'en-us_ljspeech').

    Returns:
        tuple(np.ndarray, int): Tuple of (audio_waveform, sampling_rate) or (None, None) on error.
    """
    if not text:
        st.warning("Please enter some text.")
        return None, None
    if pipeline is None:
         st.error("Kokoro pipeline is not loaded. Cannot generate speech.")
         return None, None

    try:
        st.info(f"Generating audio with voice: {voice}...")
        # Call the pipeline - it returns a generator
        generator = pipeline(text, voice=voice)

        audio_chunks = []
        # Iterate through the generator to collect all audio chunks
        for i, (gs, ps, audio_chunk) in enumerate(generator):
            # Ensure chunk is numpy array
            if torch.is_tensor(audio_chunk):
                audio_chunk = audio_chunk.cpu().numpy()
            if isinstance(audio_chunk, np.ndarray):
                audio_chunks.append(audio_chunk)
            # You might add logging here: print(f"Received chunk {i}, length {len(audio_chunk)}")

        if not audio_chunks:
             st.warning("Model did not generate any audio output.")
             return None, None

        # Concatenate chunks into a single waveform
        full_audio_waveform = np.concatenate(audio_chunks)
        sampling_rate = 24000 # Kokoro uses 24kHz according to documentation

        return full_audio_waveform, sampling_rate

    except ValueError as ve:
         # Catch specific error for invalid voice ID
         if "Voice" in str(ve) and "not found" in str(ve):
             st.error(f"Error: Voice ID '{voice}' not found in Kokoro. "
                      "Please check the available voices list.")
         else:
             # Catch other potential ValueErrors during generation
             st.error(f"An error occurred during generation: {ve}")
             st.exception(ve)
         return None, None
    except Exception as e:
        # Catch any other unexpected errors
        st.error(f"An unexpected error occurred during audio generation: {e}")
        st.exception(e)
        return None, None


def main():
    st.title("🗣️ Kokoro TTS - Text to Speech")
    # --- Updated Dependency Notice ---
    st.markdown("""
    Uses [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).
    **Requires system dependencies:**
    * `espeak-ng` (for Kokoro text processing)
    * `ffmpeg` (for MP3 conversion - required for MP3 download)

    Install via your system's package manager (e.g., `apt`, `brew`) or download from official websites. Ensure they are in your system's PATH.
    """)
    # --- End Updated Dependency Notice ---

    pipeline = load_kokoro_pipeline()
    if pipeline is None:
         st.error("Application cannot start because the Kokoro pipeline failed to load...")
         st.stop()

    # --- Sidebar (Keep Selectbox as before) ---
    st.sidebar.header("Configuration")
    default_voice = "af_bella"
    try:
        default_index = ALL_VOICE_IDS.index(default_voice)
    except ValueError:
        default_index = 0
    selected_voice = st.sidebar.selectbox(
        "Select Voice:",
        options=ALL_VOICE_IDS,
        index=default_index,
        help="Choose a voice from the available options."
    )
    # --- End Sidebar ---

    # --- Main Area ---
    text_input = st.text_area(
        "Enter text to convert to speech:",
        height=150,
        placeholder="e.g., Hello world!"
    )
    generate_button = st.button("Generate Speech", type="primary")
    progress_container = st.container()
    audio_container = st.container()
    # --- End Main Area ---

    if generate_button and text_input:
        with progress_container:
            with st.spinner('Synthesizing audio...'):
                audio_waveform, sampling_rate = generate_speech_kokoro(
                    text_input,
                    pipeline,
                    selected_voice
                )

                # --- Process and Display Audio ---
                if audio_waveform is not None and sampling_rate is not None:
                    with audio_container:
                        st.success("Speech generated successfully!")
                        try:
                            # --- Create WAV in memory ---
                            wav_bytes_io = io.BytesIO()
                            # Using subtype='PCM_16' is generally good practice for WAV
                            sf.write(wav_bytes_io, audio_waveform, sampling_rate, format='WAV', subtype='PCM_16')
                            wav_bytes_io.seek(0) # Important: Rewind BytesIO to the beginning

                            # --- Display Audio (Fixes Warning) ---
                            # Pass BytesIO directly, DO NOT pass sample_rate here
                            st.audio(wav_bytes_io, format='audio/wav')

                            # --- Download Buttons ---
                            col1, col2 = st.columns(2) # Use columns for side-by-side buttons

                            # WAV Download Button
                            with col1:
                                st.download_button(
                                    label="Download WAV",
                                    data=wav_bytes_io, # Pass the BytesIO object directly
                                    file_name=f"kokoro_{selected_voice}.wav",
                                    mime="audio/wav"
                                )

                            # MP3 Download Button (Requires pydub and FFmpeg)
                            with col2:
                                # Check if pydub was imported successfully
                                if AudioSegment:
                                    try:
                                        # Ensure WAV BytesIO is at the start
                                        wav_bytes_io.seek(0)
                                        # Load WAV data from BytesIO using pydub
                                        audio_segment = AudioSegment.from_wav(wav_bytes_io)

                                        # Export as MP3 to a new BytesIO object
                                        mp3_bytes_io = io.BytesIO()
                                        # You can add parameters like bitrate="192k" for quality
                                        audio_segment.export(mp3_bytes_io, format="mp3")
                                        mp3_bytes_io.seek(0) # Rewind MP3 BytesIO

                                        st.download_button(
                                            label="Download MP3",
                                            data=mp3_bytes_io, # Pass the MP3 BytesIO object
                                            file_name=f"kokoro_{selected_voice}.mp3",
                                            mime="audio/mpeg" # Correct MIME type for MP3
                                        )
                                    except Exception as e:
                                        # Display error if MP3 conversion fails (likely missing FFmpeg)
                                        st.error(f"MP3 conversion failed. Is FFmpeg installed and in PATH?\nError: {e}")
                                else:
                                    # Show message if pydub is not installed
                                    st.warning("Install 'pydub' for MP3 download option.")

                        except Exception as e:
                             st.error(f"Error processing or displaying audio: {e}")
                             st.exception(e)
                else:
                    # If generation failed, message is shown in generate_speech_kokoro
                    pass
                # --- End Process and Display Audio ---

if __name__ == "__main__":
    # Make sure ALL_VOICE_IDS is defined globally or passed appropriately if needed here
    main()