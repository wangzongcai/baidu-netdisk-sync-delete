# -*- coding: utf-8 -*-
"""查 hwnd=2493982 的所属进程PID及该进程详情(路径/命令行)。"""
import ctypes
from ctypes import wintypes
import subprocess, json

user32=ctypes.windll.user32
hwnd=2493982
pid=wintypes.DWORD()
user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
print("柚子双删 所属 PID =", pid.value)

p=subprocess.run(["powershell","-NoProfile","-Command",
    f"Get-CimInstance Win32_Process -Filter 'ProcessId={pid.value}' | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine | ConvertTo-Json"],
    capture_output=True)
print(p.stdout.decode('utf-8',errors='replace'))
print(p.stderr.decode('utf-8',errors='replace'))