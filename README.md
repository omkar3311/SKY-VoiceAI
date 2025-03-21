# SKY - Voice Assistant  
**Version:** 1.0  
**Developed by:** Omkar Waghmare  

## Introduction  
SKY is a voice-controlled assistant designed to perform various tasks, including:  

- Opening applications and websites  
- Searching on Google and YouTube  
- Telling jokes  
- Providing pre-written code  
- Entering text in typing mode  

## How to Use  

### 1. Activating SKY  
Say **"Hey Sky"** to activate the assistant.  
SKY will respond with **"Hello master"**.  

### 2. Commands List  

#### General Commands:  
- **"Introduce yourself"** → SKY will introduce itself.  
- **"Tell me a joke"** → SKY will tell a random joke.
- **"Turn on typing mode"** → SKY enter in typing mode 
- **"Stop"** → Exits the program.  

#### Opening Applications & Websites:  
- **"Open [application name]"** → Opens installed applications (as defined in `data.py`).  
- **"Open [website name]"** → Opens the corresponding website.  

#### Searching the Internet:  
- **"Search [query] on Google"** → Performs a Google search.  
- **"Search [query] on YouTube"** → Searches for videos on YouTube.  

#### Code Retrieval:  
- **"Give me code for [topic]"** → Displays predefined code stored in `data.py`.  
- **"List all codes"** → Lists all available coding topics.  

#### Typing Mode:  
- **"Typing mode on"** → Enables voice-based typing.  
- **"Copy"**  → Copy sentence
Commands within typing mode:  
- **"Press Enter"** → Presses the Enter key.  
- **"Backspace"** → Deletes the last word. 
- **"Copy"**  → Copy sentence 
- **"Copy all"** → Copy all text
- **"paste"** → Paste
- **"Stop typing mode"** → Exits typing mode. 

## Installation & Requirements  

### 1. Install Dependencies  
Run the following command to install required Python modules:  

```bash
pip install speechrecognition pyttsx3 requests pyautogui
