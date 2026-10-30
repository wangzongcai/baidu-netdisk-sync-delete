# -*- coding: utf-8 -*-
"""柚子双删 —— 迷你悬浮窗

界面只有两件事：
  上：启动 Edge（浅灰带边框的普通按钮）
  下：同步删除（红底大字），跑的过程中在标题右侧用括号提示
      （检测中…）→（删除中…），结束后 2 秒自动回到初始界面。

窗口 327px 宽，启动时落在屏幕右下角，默认置顶。
最小化走任务栏（不是托盘），点任务栏图标就能恢复。
勾选文件、调出确认框仍由小康自己操作，程序只负责两端同步那一下。
详细日志不显示在界面上，全量仍然写进 sync_delete_log.txt。
"""
import ctypes
import os
import sys
import threading
import tkinter as tk

import sync_delete_v2 as core


def asset(name):
    """打包成 exe 后资源在 _MEIPASS 临时目录，源码运行时就在同目录。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

FONT = "Microsoft YaHei"

# 配色照 HTML 原型（ui_prototype.html）
C_BORDER = "#c8ccd0"
C_BAR = "#f1f3f4"
C_TITLE = "#3c4043"
C_WHITE = "#ffffff"
C_BTN = "#f8f9fa"
C_BTN_H = "#eef0f2"
C_TEXT = "#202124"
C_RED = "#d93025"
C_RED_H = "#c5221f"
C_GREY = "#9aa0a6"
C_GREEN = "#137333"
C_ICON = "#5f6368"
C_CHECK = "#1a73e8"      # 检测中的蓝
C_DEL = "#d93025"        # 删除中的红

WIN_W = 327              # 窗口宽度（196 再放大 2/3）
BAR_H = 60               # 标题栏高度
PAD = 18                 # 内容区留白

CHECK_MS = 1200          # 点下去先显示「检测中…」，这么久后切「删除中…」
BACK_MS = 2000           # 结束后 2 秒回到初始界面


class NullOut:
    """打包成窗口程序后 stdout 可能为空，统一吞掉输出。

    core 会再包一层 _Tee 把日志写进 sync_delete_log.txt，
    所以排查问题仍然看那个文件，界面上不再显示。
    """

    def write(self, s):
        pass

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.busy = False
        self._off = (0, 0)
        self._moved = False
        self._check_job = None

        root.title("柚子双删V:11149778")   # 任务栏上显示的名字
        root.overrideredirect(True)        # 自绘迷你标题栏，不要系统边框
        root.attributes("-topmost", True)  # 默认置顶
        root.configure(bg=C_BORDER)        # 外圈 1px 描边靠留白实现

        outer = tk.Frame(root, bg=C_WHITE)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_bar(outer)

        self.body = tk.Frame(outer, bg=C_WHITE, padx=PAD, pady=PAD)
        self.body.pack(fill="both", expand=True)

        # Edge 图标：从 msedge.exe 提取的 32×32，打包时一起带上
        try:
            self.edge_img = tk.PhotoImage(file=asset("edge_icon.png"))
        except Exception:
            self.edge_img = None

        # 浅灰底 + 细边框：tk 的 solid 边框是黑的，用外层 Frame 垫 1px 画出原型里的浅灰边
        edge_wrap = tk.Frame(self.body, bg=C_BORDER)
        edge_wrap.pack(fill="x", pady=(0, PAD))
        btn_kw = dict(image=self.edge_img, compound="left") if self.edge_img else {}
        self.edge_btn = tk.Button(
            edge_wrap, text="   启动 Edge", command=self.do_launch,
            bg=C_BTN, fg=C_TEXT, activebackground=C_BTN_H, activeforeground=C_TEXT,
            relief="flat", bd=0, font=(FONT, 17), cursor="hand2", **btn_kw)
        self.edge_btn.pack(fill="x", padx=1, pady=1, ipady=8)

        self.main_btn = tk.Button(
            self.body, text="同步删除", command=self.do_run,
            bg=C_RED, fg=C_WHITE, activebackground=C_RED_H, activeforeground=C_WHITE,
            relief="flat", bd=0, font=(FONT, 19, "bold"), cursor="hand2",
            disabledforeground=C_WHITE)
        self.main_btn.pack(fill="x", ipady=18)

        root.update_idletasks()
        self._install_taskbar()
        self._place()

    # ---------- 标题栏 ----------
    def _build_bar(self, parent):
        bar = tk.Frame(parent, bg=C_BAR, height=BAR_H)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        title = tk.Label(bar, text="柚子双删V:11149778", bg=C_BAR, fg=C_TITLE,
                         font=(FONT, 11), anchor="w")
        title.pack(side="left", padx=(PAD, 0))

        # 运行状态：标题右边括号提示，两个阶段颜色分开
        self.state_lbl = tk.Label(bar, text="", bg=C_BAR, fg=C_CHECK,
                                  font=(FONT, 10), anchor="w")
        self.state_lbl.pack(side="left", padx=(6, 0))

        # 关闭：悬停变红底白字，跟系统窗口一致
        close = tk.Label(bar, text="×", bg=C_BAR, fg=C_ICON,
                         font=("Segoe UI", 20), padx=10, cursor="hand2")
        close.pack(side="right", padx=(0, 6))
        close.bind("<Button-1>", lambda e: self.root.destroy())
        close.bind("<Enter>", lambda e: close.configure(bg=C_RED, fg=C_WHITE))
        close.bind("<Leave>", lambda e: close.configure(bg=C_BAR, fg=C_ICON))

        # 最小化：一根短横线（比「—」字符短一半）
        minc = tk.Canvas(bar, width=43, height=43, bg=C_BAR,
                         highlightthickness=0, cursor="hand2")
        minc.create_line(16, 21, 28, 21, fill=C_ICON, width=2)
        minc.pack(side="right")
        minc.bind("<Button-1>", lambda e: self.do_minimize())
        minc.bind("<Enter>", lambda e: minc.configure(bg=C_BTN_H))
        minc.bind("<Leave>", lambda e: minc.configure(bg=C_BAR))

        # 拖窗口
        for w in (bar, title):
            w.bind("<Button-1>", self._press)
            w.bind("<B1-Motion>", self._drag)
            w.bind("<ButtonRelease-1>", self._release)

    def _install_taskbar(self):
        """无边框窗口默认不进任务栏，补上 WS_EX_APPWINDOW，
        最小化后才会有任务栏按钮可点。"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ex = ctypes.windll.user32.GetWindowLongW(hwnd, -20)   # GWL_EXSTYLE
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex | 0x00040000)
            self.hwnd = hwnd
        except Exception:
            self.hwnd = None

    def _place(self):
        """启动位置：屏幕右下，右沿固定、底边避开任务栏。"""
        h = self.root.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - WIN_W - 325
        y = sh - 52 - h - 8
        self.root.geometry(f"{WIN_W}x{h}+{x}+{y}")

    def _press(self, e):
        self._off = (e.x_root - self.root.winfo_x(),
                     e.y_root - self.root.winfo_y())
        self._moved = False

    def _drag(self, e):
        x = e.x_root - self._off[0]
        y = e.y_root - self._off[1]
        if abs(x - self.root.winfo_x()) > 2 or abs(y - self.root.winfo_y()) > 2:
            self._moved = True
        self.root.geometry(f"+{x}+{y}")

    def _release(self, e):
        self._moved = False

    def do_minimize(self):
        """最小化进任务栏（不是托盘），点任务栏图标恢复。"""
        if not self.hwnd:
            self._install_taskbar()
        if self.hwnd:
            ctypes.windll.user32.ShowWindow(self.hwnd, 6)   # SW_MINIMIZE

    # ---------- 动作 ----------
    def do_launch(self):
        if self.busy:
            return
        self.busy = True
        self.edge_btn.configure(state="disabled")
        threading.Thread(target=self._launch_work, daemon=True).start()

    def _launch_work(self):
        old = sys.stdout
        sys.stdout = NullOut()
        try:
            core.launch_edge()
        except Exception:
            pass
        finally:
            sys.stdout = old
            self.root.after(0, self._launch_done)

    def _launch_done(self):
        self.busy = False
        self.edge_btn.configure(state="normal")

    def do_run(self):
        if self.busy:
            return
        self.busy = True
        core.LAST_RESULT.clear()
        self.edge_btn.configure(state="disabled")
        self._set_stage("check")
        # core 内部先核对再删除，这里按时间切一次阶段提示
        self._check_job = self.root.after(CHECK_MS, self._to_delete_stage)
        threading.Thread(target=self._run_work, daemon=True).start()

    def _set_stage(self, stage):
        # 提示类文字比主按钮字号小一档，长句子才塞得进按钮宽度
        small = (FONT, 14, "bold")
        if stage == "check":
            self.state_lbl.configure(text="（检测中…）", fg=C_CHECK)
            self.main_btn.configure(state="disabled", bg=C_GREY,
                                    text="请稍候", font=small, cursor="")
        else:
            self.state_lbl.configure(text="（删除中…）", fg=C_DEL)
            self.main_btn.configure(state="disabled", bg=C_GREY,
                                    text="删除中…", font=small, cursor="")

    def _to_delete_stage(self):
        self._check_job = None
        if self.busy:
            self._set_stage("delete")

    def _run_work(self):
        old_argv, old_out = sys.argv, sys.stdout
        sys.argv = ["sync_delete_v2"]
        sys.stdout = NullOut()
        try:
            core.main()
        except Exception:
            pass
        finally:
            sys.stdout = old_out
            sys.argv = old_argv
            self.root.after(0, self._show_result)

    def _show_result(self):
        """结果直接写在「同步删除」按钮上，2 秒后自动回初始界面。

        成功只显示「双删已完成」；失败显示具体原因（没找到哪一端的确定按钮、
        哪一端没删成），免得只看到一句「失败」还要去翻日志。
        """
        self.busy = False
        if self._check_job:
            self.root.after_cancel(self._check_job)
            self._check_job = None
        self.edge_btn.configure(state="normal")
        self.state_lbl.configure(text="")

        r = dict(core.LAST_RESULT)
        err = getattr(core, "LAST_ERROR", "") or ""
        web_ok, cli_ok = r.get("web_ok"), r.get("client_ok")

        if web_ok is True and cli_ok is True:
            text, bg = "双删已完成", C_GREEN
        elif err:
            text, bg = err, C_RED
        elif web_ok is False:
            text, bg = "网页端没删成", C_RED
        elif cli_ok is False:
            text, bg = "客户端没删成", C_RED
        else:
            text, bg = "未完成，重试", C_RED

        self.main_btn.configure(state="disabled", bg=bg, text=text,
                                font=(FONT, 14, "bold"), cursor="")
        self.root.after(BACK_MS, self._reset)

    def _reset(self):
        """回到初始界面：红色「同步删除」，标题栏不留状态。"""
        self.state_lbl.configure(text="")
        if not self.busy:
            self.main_btn.configure(state="normal", bg=C_RED,
                                    text="同步删除",
                                    font=(FONT, 19, "bold"), cursor="hand2")


def main():
    # 先声明 DPI 感知，tk 拿到的屏幕尺寸才和真实像素一致，
    # 否则 125% 缩放下窗口位置会飘到屏幕外
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
