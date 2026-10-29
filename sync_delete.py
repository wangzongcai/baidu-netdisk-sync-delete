# -*- coding: utf-8 -*-
"""双端同步点击『确定』：
- 网页端: 用 CDP Input.dispatchMouseEvent 在视口坐标精确点击(不动物理光标)
- 客户端: SendInput 物理鼠标点击
- 同步: threading.Barrier 发令枪, 同一时刻触发
- 记录: 两端按下时刻差, 网页端删除请求发出延迟
仅在用户已确认、两端确认框都已弹出时运行。"""
import ctypes
from ctypes import wintypes
import threading, time
from playwright.sync_api import sync_playwright

CLIENT_CONFIRM_OFFSET = (829, 483)   # 相对客户端窗口左上(截图测得)
CLIENT_HWND = 918428
HOST="127.0.0.1"; PORT=9222

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

r = wintypes.RECT(); user32.GetWindowRect(CLIENT_HWND, ctypes.byref(r))
cx, cy = r.left + CLIENT_CONFIRM_OFFSET[0], r.top + CLIENT_CONFIRM_OFFSET[1]
print(f"客户端窗口@({r.left},{r.top}) 确定按钮屏幕坐标=({cx},{cy})")

p = sync_playwright().start()
b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
ctx = b.contexts[0]
page = None
for pg in ctx.pages:
    if "/disk/clear" in pg.url: page = pg; break
if not page:
    print("ERROR: 未找到清理页"); p.stop(); raise SystemExit

# 取网页端确定按钮视口坐标 + 校验确认框
web_btn = page.evaluate("""() => {
  const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
  if(!dlg) return null; if(dlg.getBoundingClientRect().width<=0) return null;
  let best=null;
  dlg.querySelectorAll('button,span,div,a').forEach(n=>{
    const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
    if((n.innerText||'').trim()==='确定'){ if(!best||r.width*r.height<best.area) best={x:r.x+r.width/2,y:r.y+r.height/2,area:r.width*r.height}; }
  });
  return best;
}""")
if not web_btn:
    print("ERROR: 网页端确认框未检测到，中止(不点击)"); p.stop(); raise SystemExit
print("网页端确定按钮视口坐标:", web_btn)

# 记录网页端删除请求发出时刻
req = {"t": None, "url": None}
cdp = ctx.new_cdp_session(page)
cdp.send("Network.enable")
def on_req(ev):
    u=ev.get("request",{}).get("url",""); m=ev.get("request",{}).get("method","")
    if req["t"] is None and ("delete" in u.lower() or "del" in u.lower() or m=="POST"):
        req["t"]=time.perf_counter_ns(); req["url"]=u[:140]
cdp.on("Network.requestWillBeSent", on_req)

# 预热客户端光标
user32.SetCursorPos(cx, cy)
time.sleep(0.3)

barrier = threading.Barrier(2)
ts = {}
errs = {}
MOUSEEVENTF_LEFTDOWN=0x0002; MOUSEEVENTF_LEFTUP=0x0004

def client_thread():
    try:
        barrier.wait()
        ts["client"]=time.perf_counter_ns()
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        ts["client_up"]=time.perf_counter_ns()
        user32.mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0)
    except Exception as e:
        errs["client"]=repr(e)

th=threading.Thread(target=client_thread); th.start()
barrier.wait()
ts["web"]=time.perf_counter_ns()
# 网页端 CDP 精确点击(视口坐标)
cdp.send("Input.dispatchMouseEvent", {"type":"mousePressed","x":web_btn["x"],"y":web_btn["y"],"button":"left","clickCount":1})
cdp.send("Input.dispatchMouseEvent", {"type":"mouseReleased","x":web_btn["x"],"y":web_btn["y"],"button":"left","clickCount":1})
ts["web_up"]=time.perf_counter_ns()
th.join()

print("\n===== 同步点击结果 =====")
if errs: print("错误:",errs)
print(f"客户端按下: {ts.get('client')}")
print(f"网页端按下: {ts.get('web')}")
if ts.get("client") and ts.get("web"):
    print(f">>> 两端『按下』时间差: {abs(ts['web']-ts['client'])/1e6:.3f} ms")

# 等删除结果 + 捕获请求
for _ in range(60):
    if req["t"]: break
    time.sleep(0.02)
if req["t"]:
    print(f">>> 网页端删除请求发出(距网页端按下): {(req['t']-ts['web'])/1e6:.1f} ms")
    print(f"    request url: {req['url']}")
else:
    print("未捕获网络请求(可能走 XHR 其他匹配)")

time.sleep(1.5)
try: cdp.detach()
except Exception: pass
p.stop()
print("完成")