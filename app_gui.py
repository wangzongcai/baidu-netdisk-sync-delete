# -*- coding: utf-8 -*-
"""双端同步删除 —— 双击即用的图形界面

设计原则：
  1. 默认只核对，不删除。必须手动点『同步删除』才真正执行。
  2. 所有输出实时显示在窗口里，出问题看得到。
  3. 勾选文件、调出确认框仍由小康自己操作，程序不代劳。
"""
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import sync_delete_v2 as core


class Redirect:
    """把 print 的输出转到队列，供界面显示。"""

    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(s)

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.busy = False

        root.title("双端同步删除")
        root.geometry("820x620")
        root.minsize(640, 460)

        # 顶部操作区
        top = tk.Frame(root, padx=10, pady=8)
        top.pack(fill="x")

        tk.Button(top, text="① 启动 Edge 调试端口", command=self.do_launch,
                  width=20).pack(side="left", padx=(0, 6))

        tk.Label(top, text="同步方式:").pack(side="left", padx=(14, 2))
        # 留空 = 事件驱动（推荐）：等网页端请求真的发出去再点客户端。
        # 填数字 = 时间预置：网页端点完固定等这么多毫秒，保留作对照用。
        self.lead = tk.Entry(top, width=8)
        self.lead.pack(side="left")

        # 只看不删，放在右边当次要功能
        tk.Button(top, text="只看不删", command=lambda: self.run(True),
                  bg="#e8f0fe").pack(side="right")

        # 主按钮：点一次就干，程序内部自动核对，核对不过会自动中止
        mid = tk.Frame(root, padx=10)
        mid.pack(fill="x", pady=(0, 6))
        tk.Button(mid, text="② 同步删除（自动核对后直接执行）", command=lambda: self.run(False),
                  bg="#d93025", fg="white", height=2,
                  font=("Microsoft YaHei", 11, "bold")).pack(fill="x")

        # 输出区
        self.txt = scrolledtext.ScrolledText(root, wrap="word",
                                             font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.txt.configure(state="disabled")

        self.log("使用顺序：\n"
                 "  1. 点『启动 Edge 调试端口』——会直接打开清理页；\n"
                 "     第一次没登录，在那里扫码登录一次，登录完自动回到清理页。\n"
                 "     等扫描完成再往下走。\n"
                 "  2. 打开客户端重复文件清理页，等扫描完成。\n"
                 "  3. 两端勾选要删的文件（勾几个都行），点『删除』把确认框调出来。\n"
                 "  4. 点『② 同步删除』——程序自动核对两端，通过后立即执行。\n"
                 "     核对不通过（比如确认框没调出来）会自动中止，不会乱点。\n"
                 "─────────────────────────────────────────────\n")

        self.log("同步方式：默认『事件驱动』——网页端删除请求一发出，客户端立刻跟着点，\n"
                 "不需要预测提前量，也不用校准。上面的输入框留空即可。\n"
                 "只有在需要做对照时，才在里面填一个毫秒数（时间预置模式）。\n\n")

        self.pump()

    # ---------- 界面输出 ----------
    def log(self, s):
        self.txt.configure(state="normal")
        self.txt.insert("end", s)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def pump(self):
        """把队列里的输出刷到界面。"""
        try:
            while True:
                self.log(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(80, self.pump)

    # ---------- 动作 ----------
    def do_launch(self):
        if self.busy:
            return
        self.busy = True
        self.log("\n>>> 启动 Edge...\n")

        def work():
            old = sys.stdout
            sys.stdout = Redirect(self.q)
            try:
                core.launch_edge()
            except Exception as e:
                print(f"ERROR: {e}")
            finally:
                sys.stdout = old
                self.busy = False
                self.q.put("\n")

        threading.Thread(target=work, daemon=True).start()

    def run(self, dry):
        if self.busy:
            messagebox.showinfo("请稍等", "上一个操作还没结束。")
            return

        self.busy = True
        self.log("\n" + "=" * 52 + "\n")
        self.log(">>> " + ("只看不删" if dry else "同步删除") + "\n")

        args = []
        if dry:
            args.append("--dry")
        lead = self.lead.get().strip()
        if lead:
            try:
                float(lead)
                args.append(f"--lead={lead}")
            except ValueError:
                self.log(f"同步方式填的 '{lead}' 不是数字，按事件驱动处理\n")

        def work():
            old_argv, old_out = sys.argv, sys.stdout
            sys.argv = ["sync_delete_v2"] + args
            sys.stdout = Redirect(self.q)
            try:
                core.main()
            except Exception as e:
                import traceback
                print(f"\nERROR: {e}\n")
                traceback.print_exc()
            finally:
                sys.stdout = old_out
                sys.argv = old_argv
                self.busy = False
                self.q.put("\n>>> 完成\n")

        threading.Thread(target=work, daemon=True).start()


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
