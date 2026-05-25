from datetime import datetime

app_logs = []

def ui_log(msg: str, sender: str = "system"):
    print(msg)
    app_logs.append({"ts": datetime.now().strftime("%H:%M"), "msg": msg, "sender": sender})
    if len(app_logs) > 50:
        app_logs.pop(0)