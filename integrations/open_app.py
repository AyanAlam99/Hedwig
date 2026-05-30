import subprocess 
import os 
import webbrowser
import json

CONFIG_FILE = "hedwig_config.json"

WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "gemini" : "https://gemini.google.com/app" ,
    "chatgpt": "https://chat.openai.com",
    "claude" : "https://claude.ai/new" , 
    "netflix": "https://www.netflix.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
}

AUTO_DETECT_PATTERNS = {
    "brave":     ["BraveSoftware/**/brave.exe"],
    "chrome":    ["Google/Chrome/**/chrome.exe"],
    "firefox":   ["Mozilla Firefox/firefox.exe"],
    "edge":      ["Microsoft/Edge/**/msedge.exe"],
    "vscode":    ["Microsoft VS Code/Code.exe"],
    "code":      ["Microsoft VS Code/Code.exe"],
    "discord":   ["Discord/**/Discord.exe"],
    "telegram":  ["Telegram Desktop/Telegram.exe"],
    "whatsapp":  ["WhatsApp/WhatsApp.exe"],
    "spotify":   ["Spotify/Spotify.exe"],
    "notion":    ["Notion/Notion.exe"]
}


BASE_DIRS = [
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    os.path.expandvars(r"%LOCALAPPDATA%"),
    os.path.expandvars(r"%APPDATA%"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
]

def _load_config()->dict : 
    if os.path.exists(CONFIG_FILE):
        with open (CONFIG_FILE, "r")  as f : 
            return json.load(f)
    return {}

def _save_config(config : dict) : 
    with open(CONFIG_FILE, "w") as f : 
        json.dump(config, f,indent=2)


def open_browser_url (url : str , browser : str = 'brave') ->dict : 
    config = _load_config()

def register_app(name : str, path : str) ->dict : 
    if not name:
        return {"success": False, "message": "App name is required."}
    if not path:
        return {"success": False, "message": "App path is required."}
    if not os.path.exists(path):
        return {"success": False, "message": f"Path does not exist: {path}"}
    
    config = _load_config()

    if 'apps' not in config : 
        config['apps'] ={}

    config["apps"][name.lower().strip()] = path
    _save_config(config)

    return {
        "success" : True , 
        "message": f"'{name}' registered.",
        "apps":    config["apps"]
    }



