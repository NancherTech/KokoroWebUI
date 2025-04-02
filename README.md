# Kokoro TTS Streamlit Web UI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) A simple web interface built with Streamlit to perform Text-to-Speech (TTS) using the **[hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)** model. This application allows you to easily select different voices, generate speech from text, listen to the audio output, and download the results as WAV or MP3 files.

## Features

* Synthesize speech from input text using the Kokoro TTS model.
* Select from a wide range of voices available in the Kokoro model (covering various languages and accents).
* Playback the generated audio directly in the browser via an interactive player.
* Download the generated audio as high-quality WAV files.
* Optionally download the generated audio as compressed MP3 files (requires FFmpeg).

## System Requirements (Crucial!)

This application **requires external software** to be installed on your system *before* running the Python code. These are system-level dependencies, not Python packages.

1.  **`espeak-ng`**: Required by the `kokoro` Python library for text processing and phonemization.
    * **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install espeak-ng`
    * **macOS (Homebrew):** `brew install espeak-ng`
    * **Windows:** Download pre-compiled binaries from the [espeak-ng GitHub releases](https://github.com/espeak-ng/espeak-ng/releases). Extract the files and **add the installation directory to your system's PATH environment variable.** Alternatively, use package managers like Chocolatey (`choco install espeak-ng`) or Scoop if available.

2.  **`ffmpeg`**: Required by the `pydub` Python library for converting audio to MP3 format. This is **only needed if you want the MP3 download option** to work.
    * **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`
    * **macOS (Homebrew):** `brew install ffmpeg`
    * **Windows:** Download pre-compiled builds from the [FFmpeg website](https://ffmpeg.org/download.html) (builds from "gyan.dev" are recommended). Extract the archive (e.g., to a folder like `C:\ffmpeg`) and **add the `bin` subfolder** within that folder (e.g., `C:\ffmpeg\bin`) **to your system's PATH environment variable.**

**Important:** After installing or modifying the PATH for these dependencies (especially on Windows), **you MUST restart your terminal, command prompt, or IDE** for the changes to take effect before running the Streamlit app.

## Installation

Follow these steps to set up the project locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NancherTech/KokoroWebUI.git
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create and activate a Python virtual environment (Recommended):**
    ```bash
    # Create a virtual environment named 'venv'
    python -m venv venv

    # Activate it:
    # Windows (Command Prompt)
    .\venv\Scripts\activate
    # Windows (PowerShell)
    .\venv\Scripts\Activate.ps1
    # macOS / Linux (Bash/Zsh)
    source venv/bin/activate
    ```

3.  **Install Python packages:**
    Make sure you have the `requirements.txt` file (generated previously) in your project directory. Then run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure your virtual environment is activated.
2.  Make sure you are in the project's root directory (where `app.py` is located).
3.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
4.  The application interface should automatically open in your default web browser.
5.  Enter text into the text area.
6.  Select a voice from the dropdown menu in the sidebar.
7.  Click the "Generate Speech" button and wait for the synthesis.
8.  Use the audio player to listen and the download buttons to save the file.

## Troubleshooting

* **Errors related to `kokoro` or `espeak-ng`:** Double-check that `espeak-ng` is correctly installed *and* accessible system-wide (check your PATH if needed). Ensure the `kokoro` Python package is installed in your active virtual environment (`pip show kokoro`).
* **`MP3 conversion failed... [WinError 2]` (Windows) or "ffmpeg not found":** This means the `ffmpeg` executable could not be located. Confirm it's installed and its `bin` directory is correctly added to your system PATH. **Remember to restart your terminal/IDE after modifying the PATH.** You can verify the PATH setup by opening a *new* terminal and running `ffmpeg -version`.
* **Other Python Errors:** Check the console output in the terminal where you launched `streamlit run app.py` for detailed Python tracebacks.

## License

The Python code for this Streamlit application (`app.py` and associated files in this repository) is licensed under the **[MIT License](LICENSE)**. See the `LICENSE` file for the full text.

*(**Action Required:** You need to create a file named `LICENSE` in the root of your repository and paste the text of the MIT License into it. You can easily find the standard text online.)*

Please be aware that the underlying Text-to-Speech model, **[hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)**, is distributed by its creators under the **Apache 2.0 License**. Your use of the model itself is subject to the terms of that license.

## Contributing

Contributions are welcome! If you'd like to improve this Kokoro TTS Web UI, please feel free to contribute.

**Ways to Contribute:**

* **Report Bugs:** If you find a bug, please open an issue in the repository's [Issue Tracker](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME/issues), providing as much detail as possible.
* **Suggest Enhancements:** Have an idea for a new feature or improvement? Open an issue to discuss it.
* **Submit Pull Requests:** Fork the repo, create a branch, make your changes, and open a Pull Request against the `main` branch. Please provide a clear description of your changes.

*(Replace `YOUR_USERNAME/YOUR_REPOSITORY_NAME` in the Issue Tracker link)*

## Acknowledgements

* This application is built around the excellent open-source [Kokoro TTS model](https://huggingface.co/hexgrad/Kokoro-82M) developed by hexgrad and contributors.
* User interface created using [Streamlit](https://streamlit.io/).
* MP3 conversion enabled by [pydub](https://github.com/jiaaro/pydub) (which uses FFmpeg).
* WAV file handling via [SoundFile](https://github.com/bastibe/SoundFile).
