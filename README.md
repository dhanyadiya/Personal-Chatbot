# Diya — Personal AI Companion

A local-first personal chatbot using Flask, Ollama, HTML/CSS/JavaScript, and SQLite.

## Features
- Friendly English-language companion personality
- Local language model through Ollama
- Persistent chat history in `diya_memory.db`
- Explicit saved memories using messages that start with `remember:`
- Delete individual saved memories
- Clear chat history without deleting saved memories
- Sage green responsive interface
- No external AI API key required

## 1. Requirements
- Windows 11
- Python 3.11 or newer
- Ollama for Windows
- A few GB of free disk space for the model

## 2. Install Ollama and download a model
1. Install Ollama from https://ollama.com/download/windows
2. Open **Command Prompt** or **PowerShell**.
3. Download a small starter model:

   ```powershell
   ollama pull llama3.2:1b
   ```

4. Test the model:

   ```powershell
   ollama run llama3.2:1b
   ```

   Type a message. To exit the model chat, type `/bye`.

Ollama normally runs in the background and provides its local API at `http://127.0.0.1:11434`.

## 3. Create a Python environment
Open Command Prompt in the folder containing `app.py` and run:

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `py` is not recognized, install Python from https://www.python.org/downloads/windows/ and enable the option to add Python to PATH.

## 4. Start Diya
Make sure Ollama is running and the model is downloaded. In the project folder, run:

```powershell
.venv\Scripts\activate
python app.py
```

Open this address in your browser:

http://127.0.0.1:5000

To stop the Flask app, return to the terminal and press `Ctrl+C`.

## 5. Teach Diya a memory
Send a message in this format:

`remember: I prefer short explanations with examples.`

Diya saves that memory in the local SQLite database and uses saved memories as context in future chats. Only use this for information you are comfortable storing on this computer. You can delete memories in the left sidebar.

## 6. Change the model
The starter model is `llama3.2:1b`, selected as a smaller starting point. If your computer has enough RAM, you can try another model such as `qwen2.5:3b`:

```powershell
ollama pull qwen2.5:3b
```

Then set the model before starting Flask:

```powershell
$env:OLLAMA_MODEL = "qwen2.5:3b"
python app.py
```

This environment variable applies only to that PowerShell session.

## Privacy and safety notes
- Chat history and memories are saved in `diya_memory.db` in the project folder.
- Do not commit the database file to a public Git repository.
- The app binds to `127.0.0.1`, so it is intended for use on your own computer.
- Keep the Ollama API local; do not expose port `11434` to the internet.
- This is a learning/development project. Do not use Flask's debug server or expose this app publicly without adding authentication, CSRF protections, production hosting, and a security review.
- The web fonts are loaded from Google Fonts when internet access is available. The chatbot itself can work offline after the model is downloaded, but the font may fall back to a local font.
