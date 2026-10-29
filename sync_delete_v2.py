# -*- coding: utf-8 -*-
"""双端同步删除 v2 —— 同步点击 + 真实链路测量

网页端:
  - CDP Input.dispatchMouseEvent 精确点击视口坐标(不动物理光标)
  - page.on('request'/'response') 捕获删除请求「发出时刻」「响应时刻」及请求体
客户端:
  - 确认框是独立窗口『系统提示』(DuiHostWnd)，不再是主窗口内部子面板
  - 自动定位弹窗内的「确定」按钮(深色文字像素聚类)
  - SendInput 物理点击
  - 完成信号: 确认框窗口消失 (轮询 IsWindowVisible)

⚠ 运行即真实删除，务必先经小康确认。
用法: python sync_delete_v2.py [--dry]
"""
import ctypes
import json
import os
import sys
import threading
import time
from ctypes import wintypes

from PIL import Image
from playwright.sync_api import sync_playwright

HOST, PORT = "127.0.0.1", 9222
CLEAR_URL = "https://pan.baidu.com/disk/clear"   # 启动 Edge 时直接打开这一页
# 截图/临时文件目录：自动取程序所在目录，换电脑不用改
# 打包成 exe 后 __file__ 在临时目录里，要用 exe 自身所在位置
if getattr(sys, "frozen", False):
    IMG_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    IMG_DIR = os.path.dirname(os.path.abspath(__file__))
LEAD_MS = 20.0        # 网页端提前量基准：单文件时网页本地段比客户端慢约 20ms
CLIENT_LOCAL_MS = 7.0 # 客户端「点击→发出请求」的经验值（实测 6~8ms，无法直接测量）


# ---------------- 提前量自动校准（跨轮记忆） ----------------
def cal_path():
    """校准文件放在用户目录，跟程序放哪无关，换位置也不丢。"""
    base = os.environ.get("LOCALAPPDATA") or IMG_DIR
    d = os.path.join(base, "BaiduDupeSync")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "lead_cal.json")


def load_cal():
    try:
        with open(cal_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cal(cal):
    try:
        with open(cal_path(), "w", encoding="utf-8") as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"（校准值保存失败: {e}）")
        return False


def must_spread(ns):
    """样本的勾选数量是否拉开足够档位，才值得做直线拟合。

    实测：285 个 → 928.3ms、298 个 → 923.1ms，只差 13 个却看不出规律。
    这种挤在同一档的样本强行拟合，斜率只反映噪声，外推会给出离谱的提前量。
    """
    lo, hi = min(ns), max(ns)
    return (hi - lo) >= 50 and hi >= 2 * max(lo, 1)


def predict_web_local(cal, n):
    """用历史实测样本预测「网页端本地段」(点击→请求发出，单位 ms)。

    网页端本地段跟勾选数量强相关（实测 5 个≈230ms、285 个≈928ms），
    而且单次波动很大，所以：
      1) 历史上删过差不多数量的 → 直接取那几次的均值，最准
      2) 数量差得远 → 用已知样本做直线拟合外推
      3) 样本不够 → 返回 None，退回按数量公式粗估
    """
    hist = [h for h in (cal.get("history") or []) if isinstance(h, dict)]
    if not hist:
        return None
    # 1) 数量接近：容差取 5 个或 15%
    near = [h["ms"] for h in hist if abs(h["n"] - n) <= max(5, int(n * 0.15))]
    if near:
        return sum(near) / len(near)
    # 2) 外推：最小二乘拟合「数量 → 本地段」
    #    前提是样本数量本身要拉开档位。实测 285 个和 298 个的本地段只差 5ms，
    #    两个点挤在同一档去拟合直线，斜率纯属噪声，外推到小数量会离谱（曾算出 840ms）。
    if len(hist) >= 2 and len({h["n"] for h in hist}) >= 2:
        xs = [h["n"] for h in hist]
        ys = [h["ms"] for h in hist]
        if must_spread(xs):
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            sxx = sum((x - mx) ** 2 for x in xs)
            if sxx > 0:
                b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                b = max(0.3, min(8.0, b))      # 单文件增量限制在合理范围
                return my + b * (n - mx)
    return None

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()

MOUSEDOWN, MOUSEUP = 0x0002, 0x0004
WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
MK_LBUTTON = 0x0001
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def lparam(x, y):
    return (y << 16) | (x & 0xFFFF)


# ---------------- 窗口抓取 ----------------
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def window_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def capture(hwnd):
    """PrintWindow 抓窗口内容(不受遮挡/副屏/DPI 影响)。返回 RGB Image 或 None。"""
    L, T, R, B = window_rect(hwnd)
    w, h = R - L, B - T
    if w <= 0 or h <= 0:
        return None
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    ok = user32.PrintWindow(hwnd, mem, 0x2) or user32.PrintWindow(hwnd, mem, 0)
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return img if ok else None


def list_duihost_windows():
    hits = []

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value != "DuiHostWnd":
            return True
        t = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, t, 256)
        L, T, R, B = window_rect(hwnd)
        if R - L >= 100 and B - T >= 50 and T > -10000:
            hits.append((hwnd, t.value, L, T, R, B))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return hits


# ---------------- 按钮定位 ----------------
def _is_text(p):
    r, g, b = p
    return 35 <= max(r, g, b) <= 145


def locate_confirm_button(im):
    """在弹窗图像中找成对按钮，返回左侧那个(确定)的图像坐标 (x,y)；找不到返回 None。"""
    W, H = im.size
    px = im.load()

    # 白底内容区(排除透明padding形成的纯黑)
    wx = [x for x in range(W) if sum(1 for y in range(H) if min(px[x, y]) > 200) > H * 0.3]
    wy = [y for y in range(H) if sum(1 for x in range(W) if min(px[x, y]) > 200) > W * 0.3]
    if not wx or not wy:
        return None
    wx1, wx2, wy1, wy2 = min(wx), max(wx), min(wy), max(wy)

    # 只在下方区域(按钮行)扫描
    y0 = int(wy1 + (wy2 - wy1) * 0.60)
    counts = []
    for x in range(wx1, wx2 + 1):
        counts.append(sum(1 for y in range(y0, wy2 + 1) if _is_text(px[x, y])))

    # 按列聚类
    clusters, cur, gap = [], None, 0
    for i, c in enumerate(counts):
        x = wx1 + i
        if c >= 2:
            cur = [x, x] if cur is None else [cur[0], x]
            gap = 0
        elif cur is not None:
            gap += 1
            if gap > 10:
                clusters.append(tuple(cur))
                cur = None
    if cur:
        clusters.append(tuple(cur))

    # 只保留像按钮文字的簇(宽 8~60)，同一行高度
    cand = []
    for x1, x2 in clusters:
        w = x2 - x1 + 1
        if not (8 <= w <= 60):
            continue
        ys = [y for y in range(y0, wy2 + 1) for x in range(x1, x2 + 1) if _is_text(px[x, y])]
        if not ys:
            continue
        cand.append((x1, x2, min(ys), max(ys)))
    if len(cand) < 2:
        return None

    # 取纵向最靠下的一行(按钮行)，按 x 排序
    cand.sort(key=lambda c: -c[3])
    row = [cand[0]]
    for c in cand[1:]:
        if abs(c[3] - cand[0][3]) <= 4:
            row.append(c)
    row.sort(key=lambda c: c[0])
    if len(row) < 2:
        return None
    x1, x2, y1, y2 = row[0]
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def content_scale(hwnd, im):
    """应用内容坐标 → 客户区物理坐标 的缩放系数。
    该弹窗是 DPI 虚拟化窗口: PrintWindow 抓到的内容只占位图左上约 1/1.25,
    真实客户区尺寸要用 GetClientRect 读。"""
    c = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(c))
    cw = c.right - c.left
    W, H = im.size
    px = im.load()
    wx = [x for x in range(W) if sum(1 for y in range(H) if min(px[x, y]) > 200) > H * 0.3]
    content_w = (max(wx) - min(wx) + 1) if wx else W
    s = cw / content_w if content_w else 1.0
    return s, cw, content_w


def find_confirm_dialog():
    """找到带两个按钮的『系统提示』弹窗，返回 (hwnd, rect, 客户区按钮坐标, im, scale)。"""
    best = None
    for hwnd, title, L, T, R, B in list_duihost_windows():
        if "系统提示" not in title:
            continue
        im = capture(hwnd)
        if im is None:
            continue
        xy = locate_confirm_button(im)
        if xy:
            s, cw, content_w = content_scale(hwnd, im)
            cxy = (int(round(xy[0] * s)), int(round(xy[1] * s)))
            return hwnd, (L, T, R, B), cxy, im, s
        if best is None:
            best = (hwnd, (L, T, R, B), None, im, 1.0)
    return best


def find_main_window():
    for hwnd, title, L, T, R, B in list_duihost_windows():
        if "垃圾文件清理" in title and (R - L) > 600:
            return hwnd, (L, T, R, B)
    return None


def find_edge_exe():
    """在各常见安装位置找 msedge.exe。"""
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    lad = os.environ.get("LOCALAPPDATA", "")
    for c in (os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
              os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
              os.path.join(lad, "Microsoft", "Edge", "Application", "msedge.exe"),
              os.path.join(pf86, "Microsoft", "EdgeCore", "msedge.exe"),
              os.path.join(pf, "Microsoft", "EdgeCore", "msedge.exe")):
        if os.path.isfile(c):
            return c
    return None


def launch_edge(wait_seconds=20):
    """启动带调试端口的 Edge（独立 profile，保留登录态）。
    返回 True 表示端口已就绪。"""
    import subprocess
    import urllib.request

    exe = find_edge_exe()
    if not exe:
        print("ERROR: 没找到 msedge.exe，请确认已安装 Edge")
        return False

    ud = os.path.join(IMG_DIR, "_edge_profile")
    os.makedirs(ud, exist_ok=True)

    print(f"启动 Edge: {exe}")
    # 直接打开清理页：未登录会自动弹登录框，登录完成后仍回到这一页
    subprocess.Popen([exe, f"--remote-debugging-port={PORT}", f"--user-data-dir={ud}",
                      "--no-first-run", CLEAR_URL],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(wait_seconds * 2):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/json/version", timeout=2) as r:
                r.read()
            print("OK: 调试端口已就绪")
            return True
        except Exception:
            pass
    print(f"ERROR: 端口 {PORT} 未就绪")
    return False


def port_ready():
    """只检查调试端口通不通，不启动任何东西。"""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/json/version", timeout=2) as r:
            r.read()
        return True
    except Exception:
        return False


class _Tee:
    """把 print 同时写到屏幕和日志文件——事后能翻原始记录，不用靠截图。"""

    def __init__(self, *targets):
        self.targets = targets

    def write(self, s):
        for t in self.targets:
            try:
                t.write(s)
                t.flush()
            except Exception:
                pass

    def flush(self):
        for t in self.targets:
            try:
                t.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def main():
    dry = "--dry" in sys.argv

    # 上一轮若没还原 stdout，先收拾干净，避免文件句柄越攒越多
    while isinstance(sys.stdout, _Tee) and len(sys.stdout.targets) > 1:
        try:
            sys.stdout.targets[-1].close()
        except Exception:
            pass
        sys.stdout = sys.stdout.targets[0]

    # 全流程日志落盘（追加），方便事后核对每一轮的原始数字
    log_fp = None
    old_stdout = sys.stdout
    try:
        log_path = os.path.join(IMG_DIR, "sync_delete_log.txt")
        log_fp = open(log_path, "a", encoding="utf-8")
        log_fp.write("\n" + "=" * 70 + "\n"
                     + time.strftime("===== %Y-%m-%d %H:%M:%S =====\n"))
        sys.stdout = _Tee(old_stdout, log_fp)
    except Exception:
        log_fp = None

    found = find_confirm_dialog()
    if not found or not found[2]:
        print("ERROR: 未找到客户端确认弹窗(带确定/取消)，中止")
        return
    dlg_hwnd, (L, T, R, B), cxy, dim, scale = found
    print(f"客户端确认弹窗 hwnd={dlg_hwnd} rect=({L},{T})-({R},{B}) {R-L}x{B-T}")
    print(f"  内容缩放系数={scale:.3f}  『确定』客户区坐标={cxy}")
    dim.save(f"{IMG_DIR}\\_v2_dialog.png")

    main_win = find_main_window()
    if main_win:
        print(f"客户端主窗口 hwnd={main_win[0]} rect={main_win[1]}")

    if not port_ready():
        print(f"ERROR: Edge 调试端口 {PORT} 没开。请先点『启动 Edge』再试。")
        return

    p = sync_playwright().start()
    try:
        b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    except Exception as e:
        print(f"ERROR: 连不上 Edge 调试端口 {PORT}: {e}")
        p.stop()
        return
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("ERROR: 未找到网页清理页")
        p.stop()
        return

    info = page.evaluate(r"""() => {
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      const vis = dlg ? dlg.getBoundingClientRect().width>0 : false;
      let btn=null;
      if(vis) dlg.querySelectorAll('button,span,div,a').forEach(n=>{
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) return;
        if((n.innerText||'').trim()==='确定'){
          if(!btn||r.width*r.height<btn.area) btn={x:r.x+r.width/2,y:r.y+r.height/2,area:r.width*r.height};
        }
      });
      const txt=(document.body.innerText||'').replace(/\s+/g,' ');
      const m=txt.match(/(\d+)个重复文件/), s=txt.match(/已选(\d+)个文件/);
      return {dialogVisible:vis, confirm:btn, count:m?m[1]:'?', selected:s?s[1]:'?'};
    }""")
    print(f"网页端: 确认框={info['dialogVisible']} 确定按钮={info['confirm']} "
          f"重复={info['count']} 已选={info['selected']}")

    if not info["dialogVisible"] or not info["confirm"]:
        print("ERROR: 网页端确认框未就绪，中止(不点击)")
        p.stop()
        return

    # 数量提示（不再拦截）：小康要求只要两个确认框都在就直接执行，勾几个都行
    if info["selected"] not in ("1", "?"):
        print(f"提示: 网页端已选 {info['selected']} 个文件，按多选处理。")

    if dry:
        page.screenshot(path=f"{IMG_DIR}\\_v2_dry_web.png")
        print("--dry 核对通过，未点击。")
        p.stop()
        return

    # ---------------- 网页端网络埋点 ----------------
    ts = {}
    ev = {"req": None, "req_url": "", "req_body": "", "resp": None, "req_m": ""}
    all_req = []
    # 网页端删除请求真正发出的那一刻会置位，客户端据此立刻点击
    sent_event = threading.Event()

    def on_request(r):
        now = time.perf_counter_ns()
        all_req.append((now, r.method, r.url))
        # 必须限定成「删除接口」本身。点确定后浏览器可能先发别的 POST（埋点、上报之类），
        # 如果拿它当触发信号，客户端会在网页端真正删除之前就被点下去。
        is_delete_api = (r.method in ("POST", "DELETE", "PUT")
                         and "delete" in r.url.lower())
        if ev["req"] is None and is_delete_api:
            ev["req"] = now
            ev["req_m"] = r.method
            ev["req_url"] = r.url
            try:
                ev["req_body"] = (r.post_data or "")[:400]
            except Exception:
                ev["req_body"] = ""
            sent_event.set()

    def on_response(r):
        if ev["resp"] is None and ev["req_url"] and r.url == ev["req_url"]:
            ev["resp"] = time.perf_counter_ns()

    page.on("request", on_request)
    page.on("response", on_response)

    # 预热一次(只发鼠标移动，不点击)，让客户端先准备好处理输入
    user32.PostMessageW(dlg_hwnd, WM_MOUSEMOVE, 0, lparam(*cxy))
    page.wait_for_timeout(200)

    # 客户端完成信号 = 主窗口整块切换成「清理完成」页（绿勾 + "清理了 N 个重复文件"）。
    # 这一步的数据（释放多少空间、清理多少个）只有服务器知道，所以是可信信号。
    # 之前一直去找独立的"系统提示"小窗，结果它根本不是独立窗口，永远抓不到。
    def green_count(im):
        """粗略统计绿色像素数：页面中间那个绿勾圆 ≈ RGB(76,175,80)。"""
        try:
            small = im.convert("RGB").resize((80, 60))
            n = 0
            for r, g, b in small.getdata():
                if g > 130 and r < 140 and b < 140 and g - max(r, b) > 20:
                    n += 1
            return n
        except Exception:
            return 0

    def client_snapshot():
        """一次截图，同时给出「列表区哈希」和「绿勾像素数」。"""
        m = find_main_window()
        if not m:
            return None, 0
        im = capture(m[0])
        if not im:
            return None, 0
        # 哈希只截「N 个重复文件」这一行，避开下面的「已选择 M 个」——
        # 点确定后"已选择"会立刻变成 0，会把时刻误判成完成（会早 500ms+）
        return hash(im.crop((50, 55, 650, 100)).tobytes()), green_count(im)

    base_sig, _ = client_snapshot()

    # ---------------- 补偿同步发令 ----------------
    # 提前量 = 基准(按本机历史校准) + (已选数量-1) × 单文件增量
    # 单文件增量约 4ms/个，来自实测：删 1 个网页本地段 ≈27ms、删 6 个 ≈47.5ms
    cal = load_cal()
    base_ms = float(cal.get("base_ms", LEAD_MS))
    per_file_ms = float(cal.get("per_file_ms", 4.0))

    try:
        n_sel = int(info["selected"])
    except (TypeError, ValueError):
        n_sel = 1

    # 两种同步方式：
    #   事件驱动（默认）—— 等网页端删除请求**真的发出去**，再立刻点客户端。
    #       不再猜"网页端要花多久"：实测同样勾 8 个，本地段能在 175.8ms 和 356.0ms
    #       之间乱跳（差一倍），任何按数量算出来的提前量都会偏掉一两百毫秒。
    #   时间预置（--lead=N）—— 页面点完固定等 N 毫秒再点客户端，保留作手动对照。
    manual = False
    lead_ms = 0.0
    for a in sys.argv:
        if a.startswith("--lead="):
            lead_ms = float(a.split("=", 1)[1])
            manual = True
    event_mode = not manual
    lead_ns = int(lead_ms * 1e6)

    if event_mode:
        print("同步方式: 事件驱动 —— 网页端请求一发出就立刻点客户端（不再预测提前量）")
    else:
        print(f"同步方式: 时间预置 —— 网页端点完 {lead_ms:+.0f} ms 后点客户端（手动指定）")

    barrier = threading.Barrier(2)
    web_clicked = threading.Event()
    clip = {"gone": None, "refresh": None, "done_page": None, "done": False, "err": None}

    def client_worker():
        try:
            barrier.wait()
            if event_mode:
                # 等网页端把删除请求**真正发出去**（不是"网页端点完了"）
                # 这一步用实测代替预测，网页端快也好慢也好，都紧跟着点
                if not sent_event.wait(3.0):
                    clip["err"] = "等网页端请求发出超时(3s)"
                    return
            elif lead_ns > 0:
                web_clicked.wait()
                target = ts["web_click"] + lead_ns
                while time.perf_counter_ns() < target:   # 忙等到目标时刻
                    pass
            ts["client_click"] = time.perf_counter_ns()
            # 直接向弹窗投递鼠标消息(不动物理光标、不受 DPI/屏幕坐标影响)
            user32.PostMessageW(dlg_hwnd, WM_MOUSEMOVE, 0, lparam(*cxy))
            user32.PostMessageW(dlg_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam(*cxy))
            user32.PostMessageW(dlg_hwnd, WM_LBUTTONUP, 0, lparam(*cxy))
            ts["client_click_done"] = time.perf_counter_ns()
            # 完成信号: ①确认弹窗消失 ②主窗口列表刷新(≈服务器已处理)
            t_click = ts["client_click"] / 1e9
            fb_done = False
            deadline = t_click + 6.0
            while time.perf_counter_ns() / 1e9 < deadline:
                if clip["gone"] is None and not user32.IsWindowVisible(dlg_hwnd):
                    clip["gone"] = time.perf_counter_ns()
                # 主窗口变成「清理完成」页 = 删除真正完成（绿勾像素够多）
                if clip["done_page"] is None and base_sig is not None:
                    s, g = client_snapshot()
                    if g >= 35:
                        clip["done_page"] = time.perf_counter_ns()
                    elif s is not None and s != base_sig and clip["refresh"] is None:
                        # 兜底信号：列表区变了，但可能只是过渡页，不一定可信
                        clip["refresh"] = time.perf_counter_ns()
                if clip["gone"] is not None and (clip["done_page"] or clip["refresh"]):
                    break
                # 1 秒后弹窗仍未关闭 → SendMessage 同步兜底再点一次
                if (clip["gone"] is None and not fb_done
                        and time.perf_counter_ns() / 1e9 - t_click > 1.0):
                    user32.SendMessageW(dlg_hwnd, WM_MOUSEMOVE, 0, lparam(*cxy))
                    user32.SendMessageW(dlg_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam(*cxy))
                    user32.SendMessageW(dlg_hwnd, WM_LBUTTONUP, 0, lparam(*cxy))
                    fb_done = True
                    clip["fallback"] = time.perf_counter_ns()
                time.sleep(0.001)
        except Exception as e:
            clip["err"] = repr(e)
        finally:
            clip["done"] = True

    th = threading.Thread(target=client_worker, daemon=True)
    th.start()
    barrier.wait()
    ts["web_click"] = time.perf_counter_ns()
    web_clicked.set()
    cdp = ctx.new_cdp_session(page)
    cdp.send("Input.dispatchMouseEvent",
             {"type": "mousePressed", "x": info["confirm"]["x"], "y": info["confirm"]["y"],
              "button": "left", "clickCount": 1})
    cdp.send("Input.dispatchMouseEvent",
             {"type": "mouseReleased", "x": info["confirm"]["x"], "y": info["confirm"]["y"],
              "button": "left", "clickCount": 1})
    ts["web_click_done"] = time.perf_counter_ns()

    # 关键: 用 wait_for_timeout 驱动 Playwright 事件循环。
    # 事件驱动模式下，request 事件派发得越快，客户端点得越贴近网页端发请求的那一刻，
    # 所以这里轮询间隔要短（20ms 太粗，会让残差直接多出 20ms）。
    for _ in range(3000):
        page.wait_for_timeout(1)
        if clip["done"] and ev["resp"]:
            break
    page.wait_for_timeout(400)

    # ---------------- 报告 ----------------
    wc = ts["web_click"]
    cc = ts["client_click"]
    print("\n===== ① 点击时刻 =====")
    print(f"客户端按下 {cc}")
    print(f"网页端按下 {wc}")
    # 全程序统一符号约定：正数 = 客户端晚，负数 = 客户端早
    print(f">>> 客户端比网页端晚按下 {(cc-wc)/1e6:+.3f} ms（正数=客户端晚）")

    print("\n===== ② 网页端请求链路 (点击→真正发出) =====")
    if ev["req"]:
        print(f"{ev['req_m']} 发出: 距点击 {(ev['req']-wc)/1e6:+.1f} ms   {ev['req_url'][:110]}")
        if ev["resp"]:
            print(f"响应返回: 距点击 {(ev['resp']-wc)/1e6:+.1f} ms  (网络+服务器 {(ev['resp']-ev['req'])/1e6:.1f} ms)")
        if ev["req_body"]:
            print(f"请求体: {ev['req_body'][:280]}")
    else:
        print("未捕获 POST/DELETE 请求")

    print("\n===== ③ 客户端链路 =====")
    if clip["gone"]:
        print(f"确认弹窗消失(UI 立即关闭): 距点击 {(clip['gone']-cc)/1e6:+.1f} ms")
    else:
        print("确认弹窗未关闭")
    if clip["refresh"]:
        print(f"列表刷新(服务器已处理完): 距点击 {(clip['refresh']-cc)/1e6:+.1f} ms")
    else:
        print("列表刷新未捕获")
    if clip["done_page"]:
        print(f"「清理完成」页出现(可信信号): 距点击 {(clip['done_page']-cc)/1e6:+.1f} ms")
    if clip.get("fallback"):
        print("(触发了 SendMessage 兜底)")
    if clip["err"]:
        print("客户端错误:", clip["err"])

    # ④ 真实删除时间差：两端「删除真正生效」的时刻差，结论放到最后大字号输出
    client_done = clip["done_page"] or clip["refresh"]
    delta_ms = None
    delta_src = ""
    if ev["resp"] and client_done:
        delta_ms = (client_done - ev["resp"]) / 1e6
        delta_src = "清理完成页" if clip["done_page"] else "列表区变化"

    web_local_ms = None
    if ev["req"]:
        web_local_ms = (ev["req"] - wc) / 1e6
        print("\n===== ⑤ 链路分解 =====")
        print(f"   网页端: 点击 → 请求发出 = {web_local_ms:.1f} ms")
        if event_mode:
            lag = (cc - ev["req"]) / 1e6
            print(f"   事件驱动: 网页端请求发出 → 客户端点击 = {lag:.1f} ms")
            print("     （这段是 CDP 事件派发延迟，不含网络；越短越好）")
        print(f"   客户端: 点击 → 请求发出 = {CLIENT_LOCAL_MS:.0f} ms（经验值，无法直接测）")

        # 仍然把「网页端本地段」记进历史：不是为了预测（预测已证明不靠谱），
        # 而是为了看清它到底能波动多大
        if web_local_ms < 10:
            print("   → 网页端本地段异常(<10ms，可能没抓到真实请求)，跳过记录")
        else:
            hist = [h for h in (cal.get("history") or []) if isinstance(h, dict)]
            new_pt = {"n": n_sel, "ms": round(web_local_ms, 1)}
            hist = (hist + [new_pt])[-12:]
            fit_note = ""
            if len(hist) >= 2 and len({h["n"] for h in hist}) >= 2 \
                    and must_spread([h["n"] for h in hist]):
                xs = [h["n"] for h in hist]
                ys = [h["ms"] for h in hist]
                mx = sum(xs) / len(xs)
                my = sum(ys) / len(ys)
                sxx = sum((x - mx) ** 2 for x in xs)
                if sxx > 0:
                    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                    b = max(0.3, min(8.0, b))
                    a1 = my + b * (1 - mx)        # 单个文件时的本地段
                    cal["per_file_ms"] = round(b, 2)
                    cal["base_ms"] = round(max(5.0, min(300.0, a1 - CLIENT_LOCAL_MS)), 1)
                    fit_note = f"，拟合 {a1:.0f}+({b:.2f})/个"
            cal.update({"history": hist,
                        "last_web_local_ms": round(web_local_ms, 1),
                        "last_files": n_sel,
                        "updated": time.strftime("%Y-%m-%d %H:%M:%S")})
            if save_cal(cal):
                print(f"   → 已记下「{n_sel} 个 ≈ {web_local_ms:.0f} ms」，累计 {len(hist)} 次样本"
                      f"{fit_note}")
                if not event_mode:
                    print(f"   → 下次勾选数量接近时，直接用实测值，不再靠公式猜")
            else:
                print("   （校准值保存失败）")

    print("\n--- 本次窗口内请求(调试) ---")
    for t, m, u in all_req[:20]:
        print(f"  +{(t-wc)/1e6:8.1f}ms {m:6s} {u[:100]}")

    page.wait_for_timeout(400)
    after = page.evaluate(r"""() => {
      const t=(document.body.innerText||'').replace(/\s+/g,' ');
      const m=t.match(/(\d+)个重复文件/);
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      return {count:m?m[1]:'?', dialogVisible: dlg? dlg.getBoundingClientRect().width>0 : false};
    }""")
    print(f"\n网页端删除后: 重复={after['count']} 确认框={after['dialogVisible']}")

    if main_win:
        im2 = capture(main_win[0])
        if im2:
            im2.save(f"{IMG_DIR}\\_v2_after_client.png")
            print("客户端主窗口截图 _v2_after_client.png")
    page.screenshot(path=f"{IMG_DIR}\\_v2_after_web.png")

    # ==================== 大字号结论（放在最后，一眼看到） ====================
    bar = "=" * 62
    print("\n" + bar)

    # 指标一：两端「请求发出」时刻差 —— 由提前量直接决定，是能调到 0 的那个
    send_diff = None
    if ev["req"]:
        send_diff = ((cc + int(CLIENT_LOCAL_MS * 1e6)) - ev["req"]) / 1e6
    if send_diff is not None:
        print(f"  ① 两端请求「发出」时刻差 = {send_diff:+.1f} ms")
        if abs(send_diff) < 5:
            print("     >>> 两端几乎同时发出请求 <<<")
        elif send_diff > 0:
            print(f"     >>> 客户端晚发出 {send_diff:.1f} ms <<<")
        else:
            print(f"     >>> 客户端早发出 {-send_diff:.1f} ms <<<")
        print("     这个差就是客户端比网页端晚发出多少，是能调到 0 的那个")
    else:
        print("  ① 两端请求「发出」时刻差：没抓到网页端请求，这轮无法判断")

    print()
    # 指标二：两端「删除生效」时刻差 —— 含服务器处理抖动，天然有下限
    if delta_ms is None:
        print("  ② 两端删除「生效」时刻差：没算出来")
        print("     （缺网页端响应时刻，或缺客户端完成信号）")
    else:
        print(f"  ② 两端删除「生效」时刻差 = {delta_ms:+.1f} ms")
        if abs(delta_ms) < 5:
            print("     >>> 两端几乎同时生效 <<<")
        elif delta_ms > 0:
            print(f"     >>> 网页端先删，客户端晚 {delta_ms:.1f} ms <<<")
        else:
            print(f"     >>> 客户端先删，网页端晚 {-delta_ms:.1f} ms <<<")
        if not clip["done_page"]:
            print(f"     ⚠ 没抓到「清理完成」页，客户端信号是「{delta_src}」→ 这个数不准")
        hist_d = [v for v in (cal.get("delta_history") or [])
                  if isinstance(v, (int, float))]
        if hist_d:
            recent = " | ".join(f"{v:+.0f}" for v in hist_d[-5:])
            print(f"     最近几次(仅参考): {recent}  →  本次 {delta_ms:+.0f}")
        cal["delta_history"] = (hist_d + [round(delta_ms, 1)])[-9:]
        cal["last_delta_ms"] = round(delta_ms, 1)
        save_cal(cal)

    # 事件驱动模式下没有"下次建议"——提前量这个概念已经不用了，
    # 客户端是跟着网页端实际发出请求的那一刻动的，不用猜。
    if not event_mode and web_local_ms is not None:
        best_lead = max(0.0, web_local_ms - CLIENT_LOCAL_MS)
        print()
        print(f"  下次建议: 勾选数量差不多时，提前量用 {best_lead:.0f} ms"
              f"（本轮实际用了 {lead_ms:.0f} ms）")
    print(bar)

    try:
        cdp.detach()
    except Exception:
        pass
    p.stop()
    print("完成")


if __name__ == "__main__":
    main()
