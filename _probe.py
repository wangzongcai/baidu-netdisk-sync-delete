import sys
print("python", sys.version)
mods = ["cv2", "numpy", "playwright", "pyautogui"]
for m in mods:
    try:
        mod = __import__(m)
        print(f"{m}: OK ver={getattr(mod, '__version__', '?')}")
    except Exception as e:
        print(f"{m}: FAIL {type(e).__name__}: {e}")