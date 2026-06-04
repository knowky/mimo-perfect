#!/usr/bin/env python3
"""
ClawX System Controller - Full PC Control Module
Provides: mouse/keyboard, window management, process control, screenshots
"""

import sys
import os
import json
import time
import subprocess
import ctypes
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1
except ImportError:
    pyautogui = None

try:
    import pywinauto
    from pywinauto import Desktop, Application
except ImportError:
    pywinauto = None

# ============================================================
# MOUSE & KEYBOARD CONTROL
# ============================================================

def mouse_move(x, y, duration=0.3):
    """Move mouse to absolute position"""
    if pyautogui:
        pyautogui.moveTo(x, y, duration=duration)
        return {"status": "ok", "action": "move", "x": x, "y": y}
    return {"status": "error", "msg": "pyautogui not available"}

def mouse_click(x, y, button="left", clicks=1):
    """Click at position"""
    if pyautogui:
        pyautogui.click(x, y, clicks=clicks, button=button)
        return {"status": "ok", "action": "click", "x": x, "y": y, "button": button}
    return {"status": "error", "msg": "pyautogui not available"}

def mouse_drag(x1, y1, x2, y2, duration=0.5, button="left"):
    """Drag from one position to another"""
    if pyautogui:
        pyautogui.moveTo(x1, y1)
        pyautogui.drag(x2 - x1, y2 - y1, duration=duration, button=button)
        return {"status": "ok", "action": "drag", "from": [x1, y1], "to": [x2, y2]}
    return {"status": "error", "msg": "pyautogui not available"}

def mouse_scroll(amount, x=None, y=None):
    """Scroll wheel"""
    if pyautogui:
        pyautogui.scroll(amount, x=x, y=y)
        return {"status": "ok", "action": "scroll", "amount": amount}
    return {"status": "error", "msg": "pyautogui not available"}

def keyboard_type(text, interval=0.05):
    """Type text"""
    if pyautogui:
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
        return {"status": "ok", "action": "type", "length": len(text)}
    return {"status": "error", "msg": "pyautogui not available"}

def keyboard_hotkey(*keys):
    """Press key combination (e.g., 'ctrl', 'c')"""
    if pyautogui:
        pyautogui.hotkey(*keys)
        return {"status": "ok", "action": "hotkey", "keys": list(keys)}
    return {"status": "error", "msg": "pyautogui not available"}

def keyboard_press(key):
    """Press single key"""
    if pyautogui:
        pyautogui.press(key)
        return {"status": "ok", "action": "press", "key": key}
    return {"status": "error", "msg": "pyautogui not available"}

# ============================================================
# SCREENSHOT & SCREEN
# ============================================================

def screenshot(region=None, save_path=None):
    """Take screenshot"""
    if pyautogui:
        img = pyautogui.screenshot(region=region)
        if save_path:
            img.save(save_path)
            return {"status": "ok", "path": save_path, "size": img.size}
        # Save to temp
        tmp = os.path.join(os.environ.get("TEMP", "."), f"screenshot_{int(time.time())}.png")
        img.save(tmp)
        return {"status": "ok", "path": tmp, "size": img.size}
    return {"status": "error", "msg": "pyautogui not available"}

def screen_size():
    """Get screen dimensions"""
    if pyautogui:
        return {"status": "ok", "width": pyautogui.size()[0], "height": pyautogui.size()[1]}
    return {"status": "error", "msg": "pyautogui not available"}

def locate_on_screen(image_path, confidence=0.8):
    """Find image on screen"""
    if pyautogui:
        loc = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if loc:
            return {"status": "ok", "found": True, "location": {"left": loc.left, "top": loc.top, "width": loc.width, "height": loc.height}}
        return {"status": "ok", "found": False}
    return {"status": "error", "msg": "pyautogui not available"}

# ============================================================
# WINDOW MANAGEMENT
# ============================================================

def list_windows():
    """List all visible windows"""
    if pywinauto:
        desktop = Desktop(backend="uia")
        windows = []
        for w in desktop.windows():
            try:
                title = w.window_text()
                if title and title.strip():
                    windows.append({
                        "title": title,
                        "class_name": w.class_name(),
                        "rect": str(w.rectangle()),
                        "visible": w.is_visible(),
                        "enabled": w.is_enabled()
                    })
            except:
                pass
        return {"status": "ok", "windows": windows}
    return {"status": "error", "msg": "pywinauto not available"}

def focus_window(title_substring):
    """Focus a window by title substring"""
    if pywinauto:
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            try:
                if title_substring.lower() in w.window_text().lower():
                    w.set_focus()
                    return {"status": "ok", "focused": w.window_text()}
            except:
                pass
        return {"status": "error", "msg": f"Window matching '{title_substring}' not found"}
    return {"status": "error", "msg": "pywinauto not available"}

def minimize_window(title_substring):
    """Minimize a window"""
    if pywinauto:
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            try:
                if title_substring.lower() in w.window_text().lower():
                    w.minimize()
                    return {"status": "ok", "minimized": w.window_text()}
            except:
                pass
        return {"status": "error", "msg": f"Window matching '{title_substring}' not found"}
    return {"status": "error", "msg": "pywinauto not available"}

def maximize_window(title_substring):
    """Maximize a window"""
    if pywinauto:
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            try:
                if title_substring.lower() in w.window_text().lower():
                    w.maximize()
                    return {"status": "ok", "maximized": w.window_text()}
            except:
                pass
        return {"status": "error", "msg": f"Window matching '{title_substring}' not found"}
    return {"status": "error", "msg": "pywinauto not available"}

def close_window(title_substring):
    """Close a window"""
    if pywinauto:
        desktop = Desktop(backend="uia")
        for w in desktop.windows():
            try:
                if title_substring.lower() in w.window_text().lower():
                    w.close()
                    return {"status": "ok", "closed": w.window_text()}
            except:
                pass
        return {"status": "error", "msg": f"Window matching '{title_substring}' not found"}
    return {"status": "error", "msg": "pywinauto not available"}

# ============================================================
# PROCESS MANAGEMENT
# ============================================================

def list_processes(filter_name=None):
    """List running processes"""
    result = subprocess.run(
        ["powershell", "-Command", "Get-Process | Select-Object Name, Id, CPU, WorkingSet64, MainWindowTitle | ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    try:
        procs = json.loads(result.stdout)
        if isinstance(procs, dict):
            procs = [procs]
        if filter_name:
            procs = [p for p in procs if filter_name.lower() in (p.get("Name", "") or "").lower()]
        return {"status": "ok", "processes": procs[:50]}
    except:
        return {"status": "error", "msg": result.stderr}

def kill_process(name_or_pid):
    """Kill process by name or PID"""
    try:
        if isinstance(name_or_pid, int):
            subprocess.run(["taskkill", "/PID", str(name_or_pid), "/F"], capture_output=True, timeout=10)
        else:
            subprocess.run(["taskkill", "/IM", f"{name_or_pid}.exe", "/F"], capture_output=True, timeout=10)
        return {"status": "ok", "killed": name_or_pid}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def start_process(path, args=None):
    """Launch a process"""
    try:
        cmd = [path] + (args or [])
        subprocess.Popen(cmd, shell=True)
        return {"status": "ok", "started": path}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ============================================================
# APPLICATION LAUNCHERS
# ============================================================

def open_app(name):
    """Open common applications by name"""
    apps = {
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "taskmgr": "taskmgr.exe",
        "settings": "ms-settings:",
        "browser": None,  # handled separately
        "wechat": None,
        "steam": None,
    }
    
    # Special handling
    if name.lower() == "browser":
        return start_process("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe") or \
               start_process("C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
    
    if name.lower() == "wechat":
        # Find WeChat path
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process Weixin -ErrorAction SilentlyContinue | Select-Object Path"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return {"status": "ok", "msg": "WeChat already running"}
        # Try common paths
        for p in [os.path.expandvars(r"%ProgramFiles%\Tencent\WeChat\WeChat.exe"),
                  os.path.expandvars(r"%ProgramFiles(x86)%\Tencent\WeChat\WeChat.exe")]:
            if os.path.exists(p):
                return start_process(p)
        return {"status": "error", "msg": "WeChat not found"}
    
    exe = apps.get(name.lower())
    if exe:
        return start_process(exe)
    
    # Try direct
    return start_process(name)

# ============================================================
# SYSTEM INFO
# ============================================================

def system_info():
    """Get comprehensive system info"""
    info = {}
    
    # Basic info
    result = subprocess.run(["powershell", "-Command", """
        $os = Get-CimInstance Win32_OperatingSystem
        $cpu = Get-CimInstance Win32_Processor
        $gpu = Get-CimInstance Win32_VideoController
        @{
            OS = $os.Caption
            OSVersion = $os.Version
            CPU = $cpu.Name
            CPUCores = $cpu.NumberOfCores
            GPU = $gpu.Name
            RAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2).ToString() + ' GB'
            FreeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 2).ToString() + ' GB'
            ComputerName = $env:COMPUTERNAME
            UserName = $env:USERNAME
        } | ConvertTo-Json
    """], capture_output=True, text=True)
    try:
        info = json.loads(result.stdout)
    except:
        info = {"error": result.stderr}
    
    return {"status": "ok", "system": info}

def disk_info():
    """Get disk usage"""
    result = subprocess.run(["powershell", "-Command", """
        Get-Volume | Where-Object {$_.DriveLetter} | Select-Object DriveLetter, @{N='SizeGB';E={[math]::Round($_.Size/1GB,2)}}, @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB,2)}}, FileSystemLabel | ConvertTo-Json
    """], capture_output=True, text=True)
    try:
        return {"status": "ok", "disks": json.loads(result.stdout)}
    except:
        return {"status": "error", "msg": result.stderr}

def network_info():
    """Get network info"""
    result = subprocess.run(["powershell", "-Command", """
        Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'} | Select-Object InterfaceAlias, IPAddress | ConvertTo-Json
    """], capture_output=True, text=True)
    try:
        return {"status": "ok", "network": json.loads(result.stdout)}
    except:
        return {"status": "error", "msg": result.stderr}

# ============================================================
# FILE SYSTEM
# ============================================================

def list_files(path=".", filter_ext=None):
    """List files in directory"""
    try:
        p = Path(path)
        files = []
        for f in p.iterdir():
            if filter_ext and f.suffix.lower() != filter_ext.lower():
                continue
            files.append({
                "name": f.name,
                "type": "dir" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else None,
                "modified": f.stat().st_mtime
            })
        return {"status": "ok", "path": str(p), "files": files[:100]}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def open_file(path):
    """Open file with default application"""
    try:
        os.startfile(path)
        return {"status": "ok", "opened": path}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ============================================================
# CLI DISPATCHER
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: system_control.py <command> [args...]"}))
        return
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        # Mouse
        "mouse_move": lambda: mouse_move(int(args[0]), int(args[1])),
        "mouse_click": lambda: mouse_click(int(args[0]), int(args[1]), args[2] if len(args) > 2 else "left"),
        "mouse_drag": lambda: mouse_drag(int(args[0]), int(args[1]), int(args[2]), int(args[3])),
        "mouse_scroll": lambda: mouse_scroll(int(args[0])),
        # Keyboard
        "type": lambda: keyboard_type(args[0]),
        "hotkey": lambda: keyboard_hotkey(*args),
        "press": lambda: keyboard_press(args[0]),
        # Screen
        "screenshot": lambda: screenshot(save_path=args[0] if args else None),
        "screen_size": lambda: screen_size(),
        # Windows
        "list_windows": lambda: list_windows(),
        "focus_window": lambda: focus_window(args[0]),
        "minimize_window": lambda: minimize_window(args[0]),
        "maximize_window": lambda: maximize_window(args[0]),
        "close_window": lambda: close_window(args[0]),
        # Processes
        "list_processes": lambda: list_processes(args[0] if args else None),
        "kill_process": lambda: kill_process(int(args[0]) if args[0].isdigit() else args[0]),
        "start_process": lambda: start_process(args[0], args[1:] if len(args) > 1 else None),
        # Apps
        "open_app": lambda: open_app(args[0]),
        # System
        "system_info": lambda: system_info(),
        "disk_info": lambda: disk_info(),
        "network_info": lambda: network_info(),
        # Files
        "list_files": lambda: list_files(args[0] if args else "."),
        "open_file": lambda: open_file(args[0]),
    }
    
    if cmd in commands:
        result = commands[cmd]()
        print(json.dumps(result, default=str))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}", "available": list(commands.keys())}))

if __name__ == "__main__":
    main()
