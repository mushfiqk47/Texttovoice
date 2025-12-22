<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/CUDA-12.1-green?style=for-the-badge&logo=nvidia&logoColor=white" alt="CUDA">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

<h1 align="center">📚 Text To BOOK</h1>
<h3 align="center">AI-Powered Audiobook Generator</h3>

<p align="center">
  Transform your text into natural-sounding audiobooks using state-of-the-art AI voice synthesis.
  <br>
  Powered by <strong>Chatterbox-Turbo TTS</strong> technology.
</p>

---

## 🌟 What is Text To BOOK?

Text To BOOK is a powerful, easy-to-use application that converts text into realistic speech audio. Whether you want to:

- 🎙️ **Create audiobooks** from your favorite novels
- 📝 **Generate voiceovers** for presentations
- 🎧 **Listen to documents** while multitasking
- 🗣️ **Clone voices** using reference audio samples

This application makes it simple with a beautiful web interface and GPU-accelerated processing.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Quick TTS** | Instantly convert short text to speech |
| 📖 **Book Mode** | Process entire books with chapter detection |
| 🎭 **Emotion Tags** | Add expressions like `[laugh]`, `[sigh]`, `[gasp]` |
| 🔊 **Voice Cloning** | Use any audio sample as voice reference |
| 📚 **Voice Library** | Save and reuse your favorite voices |
| ⚡ **GPU Accelerated** | Ultra-fast generation with NVIDIA GPUs |
| 🖥️ **Modern UI** | Beautiful, responsive web interface |

---

## 📋 Requirements

Before you begin, make sure you have:

### Minimum Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: Version 3.10 or higher
- **RAM**: 8 GB minimum (16 GB recommended)
- **Storage**: 5 GB free space

### For Best Performance (GPU Mode)
- **NVIDIA GPU**: GTX 1060 or better
- **VRAM**: 4 GB minimum (8+ GB recommended)
- **CUDA**: Version 12.1 compatible drivers

> 💡 **Don't have a GPU?** No problem! The app works on CPU too, just slower.

---

## 🚀 Installation & Usage
 
This project is designed to be **Plug & Play**. You do not need to manually configure complex environments.
 
### 1. Clone the Repository
```bash
git clone https://github.com/your-username/text-to-book.git
cd text-to-book
```
 
### 2. Setup (Run Once)
Double-click **`setup.bat`**.
- It will create a virtual environment.
- It will ask if you want to install for **NVIDIA GPU** or **CPU**.
- It will install all necessary dependencies automatically.
 
### 3. Run the Application
Double-click **`run.bat`**.
 
The interface will open at: **http://localhost:8000**

---

### ⚠️ Important: Model Files
If the `models/` folder is empty after cloning (due to GitHub file size limits), you must download the `chatterbox-turbo` model manually and place it in:
`models/chatterbox-turbo/`

---

## 🌍 Universal / Mac / Linux Usage

### 🍎 Mac & 🐧 Linux Users
We have added a universal script that handles setup and running in one go.

1.  Open your Terminal.
2.  Navigate to the project folder.
3.  Run the script:
    ```bash
    chmod +x run.sh   # Make it executable (first time only)
    ./run.sh
    ```
    This will automatically check for Python, set up the environment, install dependencies, and launch the app.

### 🐳 Docker (Runs Everywhere)
If you have Docker installed, you can run this project without installing Python manually.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  Open `http://localhost:8000` in your browser.

---

## 🎮 How to Use

### Quick TTS Mode

Perfect for short text snippets and testing voices.

1. **Enter your text** in the input box
2. **Upload a voice reference** (optional) - 5-30 seconds of clear audio
3. **Adjust settings**:
   - **Expressiveness**: How dynamic the voice sounds (0.25-2.0)
   - **Guidance**: How closely to follow the reference voice (0.0-1.0)
4. **Click "Generate Speech"**
5. **Listen and download** your audio

#### 🎭 Using Emotion Tags

Make your speech more expressive by adding emotion tags:

| Tag | Description | Example |
|-----|-------------|---------|
| `[laugh]` | Adds laughter | "That's hilarious! [laugh]" |
| `[chuckle]` | Soft laugh | "Oh you [chuckle] that's funny" |
| `[sigh]` | Adds a sigh | "[sigh] It's been a long day" |
| `[gasp]` | Surprised sound | "[gasp] I can't believe it!" |
| `[cough]` | Adds coughing | "Sorry [cough] excuse me" |
| `[clear throat]` | Clearing throat | "[clear throat] Attention please" |
| `[shush]` | Asking for silence | "[shush] be quiet" |
| `[groan]` | Sound of pain/annoyance | "[groan] not again" |
| `[sniff]` | Sniffing sound | "[sniff] I think I'm sick" |
| `[whisper]` | Whispered speech | "[whisper] this is a secret" |

### Book Mode

Process entire books with automatic chapter detection.

1. **Upload your book** (supports .txt, .epub, .pdf)
2. **Click "Split Chapters"** to detect chapters automatically
3. **Review chapters** in the sidebar
4. **Upload a voice reference** for consistent narration
5. **Click "Generate All"** to process the entire book
6. **Download individual chapters** or export as a combined audiobook

---

## 📁 Project Structure

```
Text To BOOK/
├── 📄 setup.bat          # Unified setup script (CPU/GPU)
├── 📄 run.bat            # Unified run script
├── 📄 app.py             # Main application entry point
├── 📄 requirements.txt   # Python dependencies
│
├── 📁 backend/           # Server-side code
│   ├── main.py          # FastAPI server & API routes
│   ├── services.py      # TTS generation logic
│   ├── config.py        # Application settings
│   └── utils.py         # Helper functions
│
├── 📁 frontend/          # User interface
│   ├── index.html       # Main HTML page
│   ├── styles.css       # CSS styling
│   └── app.js           # JavaScript functionality
│
├── 📁 models/            # AI model files
│   └── chatterbox-turbo/# TTS model (downloaded automatically)
│
├── 📁 voices/            # Saved voice presets
│
└── 📁 output/            # Generated audio files
```

---

## ⚙️ Configuration

### Voice Settings Explained

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| **Expressiveness** | 0.25 - 2.0 | 1.0 | Controls voice dynamics. Lower = monotone, Higher = dramatic |
| **Guidance** | 0.0 - 1.0 | 0.5 | How closely to match reference voice. Lower = creative, Higher = precise |

### Tips for Best Results

1. **Voice Reference Quality**
   - Use 5-30 seconds of clean audio
   - Avoid background noise or music
   - Single speaker only
   - Clear pronunciation

2. **Text Formatting**
   - Use proper punctuation for natural pauses
   - Break long paragraphs into smaller chunks
   - Add emotion tags where expressions are needed

3. **Performance**
   - Close other GPU-intensive applications
   - Use GPU mode for 10x faster generation
   - Process long books in chapters

---

## 🔧 Troubleshooting

### Common Issues and Solutions

<details>
<summary><strong>❌ "Python not found" error</strong></summary>

**Solution:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, check ✅ **"Add Python to PATH"**
3. Restart your computer
4. Run `setup.cmd` again

</details>

<details>
<summary><strong>❌ "CUDA not available" warning</strong></summary>

**Solution:**
1. Update your NVIDIA drivers from [nvidia.com/drivers](https://www.nvidia.com/drivers)
2. Check GPU compatibility (GTX 1060 or newer recommended)
3. Run `setup_gpu.cmd` again to force reinstall with CUDA support

**Note:** If GPU fails, you can switch to CPU mode by running `setup_cpu.cmd` and `run.cmd`.

</details>

<details>
<summary><strong>❌ "Port 8000 already in use" error</strong></summary>

**Solution:**
1. Close any other applications using port 8000
2. Or change the port in `app.py`:
   ```python
   uvicorn.run(..., port=8001)
   ```
3. Access the app at `http://localhost:8001`

</details>

<details>
<summary><strong>❌ "Out of memory" error during generation</strong></summary>

**Solution:**
1. Go to Settings → Click "Clear GPU Cache"
2. Reduce text length (try smaller chunks)
3. Close other GPU-intensive applications
4. If using 4GB VRAM, try shorter text segments

</details>

<details>
<summary><strong>❌ Audio sounds robotic or unnatural</strong></summary>

**Solution:**
1. Use a better voice reference (clear, 10-20 seconds)
2. Increase Expressiveness to 1.2-1.5
3. Add punctuation for natural pauses
4. Use emotion tags like `[sigh]` or `[laugh]`

</details>

### Getting Help

If you're still having issues:

1. Check the terminal/command prompt for error messages
2. Make sure all files are in their correct locations
3. Try running `setup.cmd` again
4. Create an issue on GitHub with your error details

---

## 🔒 Privacy & Security

- ✅ **100% Local Processing** - All audio generation happens on your computer
- ✅ **No Data Upload** - Your text and audio never leave your machine
- ✅ **No Internet Required** - Works completely offline after setup
- ✅ **No Account Needed** - No registration or login required

---

## 📊 System Resource Usage

| Mode | RAM Usage | GPU VRAM | Generation Speed |
|------|-----------|----------|------------------|
| CPU Only | ~4 GB | N/A | ~0.3x realtime |
| GPU (4GB) | ~2 GB | ~3 GB | ~3x realtime |
| GPU (8GB+) | ~2 GB | ~4 GB | ~10x realtime |

---

## 🛠️ For Developers

### Running in Development Mode

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run with auto-reload
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate` | POST | Generate speech from text |
| `/api/voices` | GET | List saved voices |
| `/api/gpu-info` | GET | Get GPU status |
| `/api/clear-cache` | POST | Clear GPU memory |

### API Documentation

FastAPI automatically generates interactive docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Chatterbox-Turbo](https://github.com/resemble-ai/chatterbox)** - The amazing TTS model
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[PyTorch](https://pytorch.org/)** - Deep learning framework

---

<p align="center">
  Made with ❤️ for audiobook enthusiasts
  <br><br>
  <strong>⭐ Star this project if you find it useful! ⭐</strong>
</p>


Note: This is an educational project. Please use responsibly and respect content creators' rights.
