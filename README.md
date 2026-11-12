# 🌌 SKY AI — Dual-Agent Autonomous Desktop Assistant

**Sky** is an autonomous AI assistant that runs directly on your laptop. Built using **LangChain**, **LangGraph**, and **Groq**, Sky coordinates two specialized agents to execute your daily laptop tasks and dynamically expand its own capabilities when tools are missing.

---

## 🧠 Dual-Agent Architecture

```
                    ┌─────────────────────────┐
                    │    User (Voice / Text)  │
                    │   "Hey Sky, do <task>"  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │    Executor Agent     │
                     │  (Plans & Coordinates)│
                     └───────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
        Has Required Tool?               Missing Required Tool?
                 │                               │
                 ▼                               ▼
       ┌───────────────────┐          ┌─────────────────────┐
       │   Execute Tool    │          │  Toolbuilder Agent  │
       │ (e.g. apps, files)│          │ (Writes Python Tool)│
       └─────────┬─────────┘          └──────────┬──────────┘
                 │                               │
                 │                    [Validates AST & Saves]
                 │                               │
                 │                    ┌──────────▼──────────┐
                 │                    │ Register into Tools │
                 │                    │  Dynamic Registry   │
                 │                    └──────────┬──────────┘
                 │                               │
                 └───────────────►───────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │     Sky Speaks &      │
                     │  Delivers Completion  │
                     └───────────────────────┘
```

1. **Executor Agent**:
   - Understands your command (from voice or text).
   - Uses pre-built core tools: launch apps (`code`, `chrome`, `terminal`), inspect active file context, create & edit code files, run terminal commands, inspect laptop battery/RAM.
   - If a tool needed to finish the task is not present, it calls `request_toolbuilder_build_tool` to delegate to the Toolbuilder Agent.

2. **Toolbuilder Agent**:
   - Synthesizes clean, production-grade Python code decorated with `@tool`.
   - Validates code syntax using Abstract Syntax Trees (`ast.parse`).
   - Saves the new tool into `sky/tools/dynamic/<tool_name>.py`.
   - Dynamically imports and registers the tool into the active tool registry.
   - Hands control back to the Executor Agent, which immediately uses the new tool to finish your task!

3. **Persistent Memory System**:
   - Stores user preferences, project details, and past interactions in `sky/memory/memory.json`.
   - Persists facts across laptop reboots and restarts.
   - Sky knows his creator is **Omkar Waghmare** and remembers things Omkar teaches him (e.g., favorite languages, tools).

---

## 🎙️ Voice & Wake-Word Pipeline

- **Wake Words**: `"Hey Sky"`, `"Wake up Sky"`, or any spoken sentence containing `"Sky"`.
- **Speech-to-Text (STT)**: Powered by Groq's cloud Whisper (`whisper-large-v3` / `whisper-large-v3-turbo`) for sub-second, highly accurate transcription.
- **Wake Engine**:
  - **Continuous Voice Spotter (Active by Default)**: Listens to your microphone with Voice Activity Detection (VAD). When you speak and say "Hey Sky ...", it detects the wake word, strips the wake phrase, and immediately executes the task!
  - **Porcupine**: Optional hardware-accelerated wake-word engine if you provide a `PICOVOICE_ACCESS_KEY` in `.env`.
- **Voice Feedback (Speaker)**: Sky speaks back to you through your laptop speakers using a built-in Text-to-Speech (TTS) engine.

---

## 📁 Project Structure

```
sky-ai/
├── .env                  # Your Groq API key and configuration (kept strictly local)
├── .env.example          # Template configuration
├── requirements.txt      # Project dependencies
├── run.py                # Main executable entry point
├── sky/
│   ├── __init__.py       # Library initializer with C++ runtime conflict guard
│   ├── config.py         # Settings & environment validation
│   ├── cli.py            # Rich terminal UI & interactive runtime
│   ├── agents/
│   │   ├── state.py      # LangGraph state schema
│   │   ├── executor.py   # Executor agent logic & tool calling
│   │   ├── toolbuilder.py# Toolbuilder agent & code generation
│   │   └── graph.py      # Compiled LangGraph workflow
│   ├── tools/
│   │   ├── registry.py   # Dynamic tool registry (core + dynamic)
│   │   ├── core/         # Pre-built tools
│   │   │   ├── app_launcher.py  # Open VS Code, Chrome, Terminal, etc.
│   │   │   ├── file_ops.py      # Read, write, list files
│   │   │   ├── system_ops.py    # Run bash commands, get battery/RAM, speak aloud
│   │   │   └── code_editor.py   # Context-aware coding in VS Code
│   │   └── dynamic/      # Self-expanding tool repository (auto-written by Toolbuilder)
│   └── voice/
│       ├── listener.py   # Microphone audio capture & Whisper transcription
│       ├── wake_word.py  # Wake-word detection engine
│       └── speaker.py    # TTS voice speech synthesis
└── workspace/            # Default workspace directory where Sky creates & edits code
```

---

## 🚀 How to Run Sky

### 1. Hybrid Mode (Default — Talk & Type Simultaneously)
```bash
python run.py
```
Sky runs in **Hybrid Mode**: the background voice listener detects wake words (*"Hey Sky..."*, *"Wake up Sky..."*), while the interactive terminal prompt lets you type commands or slash commands at the same time!

### 2. Available Slash Commands (Type anytime in terminal)
| Command | Action | Example / Shortcut |
| :--- | :--- | :--- |
| **`/help`** | Displays full guide of commands & voice triggers | `help`, `/?` |
| **`/mute`** | Mutes speech output (silent terminal mode) | `mute`, `/silent`, `/quiet` |
| **`/unmute`** | Enables voice output (speaks aloud + terminal) | `unmute`, `/voice`, `/speak` |
| **`/sleep`** | Puts PC / laptop hardware to sleep (system suspend) | `sleep`, `suspend`, `go to sleep` |
| **`/status`** | Displays laptop battery, CPU, RAM, and disk status | `status`, `/sys` |
| **`/tools`** | Lists all loaded core and dynamic agent tools | `tools`, `/list` |
| **`/clear`** | Clears terminal screen and redisplays clean banner | `clear`, `cls` |
| **`/stop`** | Bids farewell and shuts down Sky completely | `/exit`, `/quit`, `stop` |

### 3. Other Run Modes
- **Single Task Execution:**
  ```bash
  python run.py --task "open vs code"
  python run.py --task "check laptop battery and ram"
  ```
- **Voice-Only Mode:**
  ```bash
  python run.py --voice
  ```
- **List Tools:**
  ```bash
  python run.py --list-tools
  ```

---

## ⚡ Auto-Start on Laptop Boot & Login

Sky is configured to launch automatically whenever you turn on your laptop and log into your desktop:

1. **Auto-Launch**: Handled via `~/.config/autostart/sky-ai.desktop` which executes [`start_sky.sh`](file:///home/omkar/Desktop/sky-ai/start_sky.sh).
2. **Audio Delay**: Waits 3 seconds after login to ensure PipeWire / PulseAudio is ready.
3. **Random Spoken Greeting**: Shuffles and speaks one of 6 friendly welcomes aloud:
   - *"Hello Omkar, nice to have you back again! I'm ready whenever you need me."*
   - *"Hi Omkar, I'm at your service. What are we building today?"*
   - *"Hey Omkar, good to see you! Sky is online and listening."*
   - *"Welcome back Omkar! Everything's up and running, just say the word."*
   - *"Hi Omkar, hope you're having a great day. I'm right here if you need anything."*
   - *"Hey Omkar, nice to see you again! All systems are ready to go."*
4. **Clean Startup**: No instruction walls on terminal. Sky greets you and is immediately ready to talk or type.
5. **Instant Synchronized Voice**: Spoken voice output starts playing at the exact same instant text appears on screen.

---

## 🎙️ Speech & Voice Controls

### 1. Mute / Unmute Speaking
- **To stop speaking (terminal text output only):**
  - Say: *"Sky, stop speaking"*, *"Mute"*, or *"Be quiet"* (or type `/mute`)
  - Sky mutes his voice. Responses will only display as text on your terminal.
  - **Visual Mute Indicator**: While muted, your terminal prompt clearly updates to:
    `Sky 🔇 [MUTED] > `
    and response panels are marked with `[🔇 Muted]`.
- **To start speaking again:**
  - Say: *"Sky, start speaking"* or *"Unmute"* (or type `/unmute`)
  - Sky will unmute, prompt returns to `Sky > `, and answers are spoken aloud.

### 2. RAM Usage (< 1% of 8GB)
Sky runs with an ultra-lightweight footprint consuming only **~74 MB of RAM** (< 0.9% of an 8GB laptop). Because heavy LLM reasoning and Whisper transcription run on Groq cloud LPUs, your laptop memory stays completely free for all your other applications and tasks.

### 2. Natural Male Neural Voice
Sky speaks with a single lifelike human male voice (`en-US-GuyNeural`), streaming output immediately without awkward pauses.

### 3. Command Understanding
If Sky does not understand a spoken or typed command, he will explicitly speak up and ask for clarification:
- e.g., *"I didn't quite catch that, Omkar! Could you let me know what you'd like me to do?"*

### 4. Offline / No Internet Warning
If internet connectivity is not present:
- Sky shows a hardcoded **Offline Mode** warning panel on the terminal.
- Sky speaks an upset, disappointed message through laptop speakers using local offline audio assets:
  > *"Ugh... Omkar, I don't have an internet connection right now! I really can't think or do anything without Wi-Fi... Please connect me to the internet so I can help you!"*
- Works 100% offline without needing any cloud connection.

### 5. Automatic Reconnection Announcement
Sky actively monitors internet connectivity in the background. When your laptop connects or reconnects to Wi-Fi / hotspot:
- Sky automatically detects the connection.
- Displays a green **Back Online** panel on the terminal.
- Enthusiastically speaks aloud:
  > *"Yahoo! Internet is back! Now I'm feeling the power in my veins! Ready for your commands, Omkar!"*

---

## 🛑 Terminating Sky vs. Putting PC to Sleep

Sky clearly distinguishes between putting your laptop to sleep and shutting down the Sky process:

### 1. 💤 Putting PC / Laptop to Sleep (Hardware Suspend)
When you tell Sky to sleep, it suspends your laptop hardware via `systemctl suspend` (keeping Sky alive so it is ready when you wake your laptop):
- **Voice**: Say *"Sky, go to sleep"*, *"Put PC to sleep"*, *"Sleep"*, or *"Suspend"*
- **Terminal**: Type `/sleep` or `sleep`
- Sky confirms: *"Putting your laptop to sleep now. Catch you later, Omkar!"* and suspends the PC.

### 2. 🛑 Terminating Sky Assistant (Process Shutdown)
When you want to stop the Sky assistant process completely and close the terminal:
- **Voice**: Say *"Call it a day"*, *"Sky stop"*, *"Stop Sky"*, *"Rest"*, or *"Take a rest"*
- **Terminal**: Type `/stop`, `stop`, `exit`, or `quit`
- Sky responds with a warm spoken farewell (e.g. *"Alright Omkar, calling it a day! Have a great rest."*) and cleanly exits.

### 2. From Terminal (Manual Stop Script):
If Sky is running in the background and you want to stop it immediately:
```bash
cd /home/omkar/Desktop/sky-ai
./stop_sky.sh
```

### 3. Turning Autostart On / Off:
- **To disable boot autostart:**
  ```bash
  rm ~/.config/autostart/sky-ai.desktop
  ```
- **To re-enable boot autostart:**
  ```bash
  cp /home/omkar/Desktop/sky-ai/sky-ai.desktop ~/.config/autostart/
  ```

---

## 🛠️ Context-Aware Coding Features

When you ask:
> *"write hello world code in python in this file"*

Sky:
1. Calls `inspect_open_file_context()` to see if an active file or VS Code workspace is open.
2. If nothing is currently open, it automatically creates a new `.py` file (e.g. `workspace/hello_world.py`).
3. Writes the code into the file.
4. Automatically opens the new file inside **VS Code** on your screen.
5. Speaks confirmation aloud!

---

## ⚙️ Configuration (`.env`)

```ini
# Primary Groq API Key
GROQ_API_KEY=gsk_...

# Backup Groq API Key (Auto-fallback when primary burns out or hits limits)
GROQ_API_KEY1=gsk_...

# Groq Model
GROQ_MODEL=qwen/qwen3.8-27b

# Whisper Model for voice transcription
WHISPER_MODEL=whisper-large-v3

# Wake phrases (comma-separated)
WAKE_WORDS=hey sky,wake up sky,sky

# Human-like Neural Voice (Male: en-US-GuyNeural, en-US-ChristopherNeural, en-IN-PrabhatNeural)
TTS_VOICE=en-US-GuyNeural

# Text-to-Speech enabled
ENABLE_TTS=true

# Workspace directory
WORKSPACE_DIR=/home/omkar/Desktop/sky-ai/workspace
```
