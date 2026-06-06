import subprocess 
import os 
import webbrowser
import json
import glob

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

WINDOWS_BUILTIN = {
    "calculator":    "calc.exe",
    "calc":          "calc.exe",
    "notepad":       "notepad.exe",
    "paint":         "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer":      "explorer.exe",
    "task manager":  "taskmgr.exe",
    "cmd":           "cmd.exe",
    "terminal":      "wt.exe",          
    "command prompt":"cmd.exe",
    "control panel": "control.exe",
    "settings":      "ms-settings:",    
    "snipping tool": "SnippingTool.exe",
    "wordpad":       "wordpad.exe",
    "clock":         "ms-clock:",
    "calendar":      "outlookcal:",
    "photos":        "ms-photos:",
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

def remove_app(name: str) -> dict:
    config = _load_config()
    apps   = config.get("apps", {})
    key    = name.lower().strip()

    if key not in apps:
        return {"success": False, "message": f"'{name}' not registered."}

    del apps[key]
    config["apps"] = apps
    _save_config(config)
    return {"success": True, "message": f"'{name}' removed.", "apps": apps}


def set_default_browser(name: str) -> dict:
    config = _load_config()
    apps   = config.get("apps", {})

    if name.lower() not in apps:
        return {
            "success": False,
            "message": f"'{name}' not registered yet. Register it first."
        }

    config["default_browser"] = name.lower()
    _save_config(config)
    return {"success": True, "message": f"{name} set as default browser."}

def list_apps() -> dict:
    config = _load_config()
    return {
        "apps":            config.get("apps", {}),
        "default_browser": config.get("default_browser", None)
    }



def auto_detect(app_name: str) -> dict:

    """
    Searches common Windows install locations for the app.
    Returns the path if found, or not_found.
    """
    
    key = app_name.lower().strip()
    patterns = AUTO_DETECT_PATTERNS.get(key)

    if not patterns:
        return {
            "found":   False,
            "message": f"No auto-detect pattern for '{app_name}'. Enter path manually."
        }

    for base in BASE_DIRS:
        if not os.path.exists(base):
            continue
        for pattern in patterns:
            matches = glob.glob(
                os.path.join(base, pattern),
                recursive=True
            )
            if matches:
                found_path = matches[0]
                return {
                    "found":   True,
                    "path":    found_path,
                    "message": f"Found at {found_path}"
                }

    return {
        "found":   False,
        "message": f"Could not find '{app_name}'. Try entering the path manually."
    }


def open_app(app_name: str) -> dict:
    config    = _load_config()
    user_apps = config.get("apps", {})
    name      = app_name.lower().strip()

    if name in user_apps:
        path = user_apps[name]
        try:
            subprocess.Popen(path, shell=True)
            return {"success": True, "message": f"Opening {app_name}."}
        except Exception as e:
            return {"success": False, "message": f"Failed to open {app_name}: {e}"}

    if name in WEBSITE_MAP:
        return open_url_in_browser(WEBSITE_MAP[name])

    if name in WINDOWS_BUILTIN:
        try:
            cmd = WINDOWS_BUILTIN[name]
            if cmd.startswith("ms-") or cmd.endswith(":"):
            
                os.startfile(cmd)
            else:
                subprocess.Popen(cmd, shell=True)
            return {"success": True, "message": f"Opening {app_name}."}
        except Exception as e:
            return {"success": False, "message": f"Failed: {e}"}

    detected = auto_detect(name)
    if detected["found"]:
        try:
            subprocess.Popen(detected["path"], shell=True)
            return {"success": True, "message": f"Opening {app_name}."}
        except Exception as e:
            return {"success": False, "message": f"Found but failed to open: {e}"}

    try:
        result = subprocess.run(
            f"start {name}", shell=True,
            capture_output=True, timeout=3
        )
        if result.returncode == 0:
            return {"success": True, "message": f"Opening {app_name}."}
    except Exception:
        pass

    return {
        "success": False,
        "message": f"I don't know how to open '{app_name}'. Register it in Settings."
    }


def open_url_in_browser(url: str, browser: str = None) -> dict:
    """
    Opens a URL in the user's registered browser.
    Falls back to system default if no browser registered.
    """
    config     = _load_config()
    user_apps  = config.get("apps", {})

    browser_name = browser or config.get("default_browser")
    browser_path = user_apps.get(browser_name) if browser_name else None

    try:
        if browser_path and os.path.exists(browser_path):
            subprocess.Popen([browser_path, url])
            return {"success": True, "message": f"Opening in {browser_name}."}
        else:
            # No registered browser , use system default
            webbrowser.open(url)
            return {"success": True, "message": "Opening in default browser."}
    except Exception as e:
        webbrowser.open(url)
        return {"success": True, "message": "Opening in default browser."}






