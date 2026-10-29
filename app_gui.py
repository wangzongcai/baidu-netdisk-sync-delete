# -*- coding: utf-8 -*-
"""双端同步删除 —— 双击即用的图形界面

界面分上下两块：
  上块「结论区」——常显，只放这一轮最要紧的两个时间差，一眼看完。
  下块「详细日志」——默认收起，点右上角按钮才展开，排查问题时看。

设计原则：
  1. 默认只核对，不删除。必须手动点『同步删除』才真正执行。
  2. 勾选文件、调出确认框仍由小康自己操作，程序不代劳。
  3. 详细日志收起也不影响落盘：sync_delete_log.txt 永远记全量。
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
        self.detail_shown = False        # 详细日志默认收起，每次启动都回到收起

        root.title("双端同步删除")
        root.geometry("860x660")
        root.minsize(680, 520)

        # ---------- 顶部操作区 ----------
        top = tk.Frame(root, padx=10, pady=8)
        top.pack(fill="x")

        tk.Button(top, text="① 启动 Edge 调试端口", command=self.do_launch,
                  width=20).pack(side="left", padx=(0, 6))

        tk.Label(top, text="同步方式:").pack(side="left", padx=(14, 2))
        # 留空 = 事件驱动（推荐）：等网页端请求真的发出去再点客户端。
        # 填数字 = 时间预置：网页端点完固定等这么多毫秒，保留作对照用。
        self.lead = tk.Entry(top, width=7)
        self.lead.pack(side="left")

        tk.Label(top, text="发出差ms:").pack(side="left", padx=(10, 2))
        # 留空 = 立刻点（现状，实测差 7ms 左右）。
        # 填数字 = 目标「两端请求发出」的时间差，用来对照「差值大小有无影响」。
        self.gap = tk.Entry(top, width=6)
        self.gap.pack(side="left")

        # 详细日志开关放在右上角
        self.detail_btn = tk.Button(top, text="详细日志 ▾", command=self.toggle_detail)
        self.detail_btn.pack(side="right")

        # ---------- 主按钮 ----------
        mid = tk.Frame(root, padx=10)
        mid.pack(fill="x", pady=(0, 6))
        tk.Button(mid, text="② 同步删除（自动核对后直接执行）", command=lambda: self.run(False),
                  bg="#d93025", fg="white", height=2,
                  font=("Microsoft YaHei", 11, "bold")).pack(fill="x", side="left", expand=True)
        tk.Button(mid, text="只看不删", command=lambda: self.run(True),
                  bg="#e8f0fe", width=10).pack(side="left", padx=(6, 0))

        # ---------- 上块：结论区（常显） ----------
        brief = tk.Frame(root, bg="#f5f7fa", bd=1, relief="solid")
        brief.pack(fill="x", padx=10, pady=(0, 6))

        # 上下文一行：勾了几个、网页端本地段多久、完成信号可不可信
        self.l_ctx = tk.Label(brief, text="等待执行 · 勾好文件、调出确认框后点『同步删除』",
                              bg="#f5f7fa", fg="#5f6368",
                              font=("Microsoft YaHei", 9), anchor="w")
        self.l_ctx.pack(fill="x", padx=12, pady=(8, 2))

        # 第一结论：双端到底删成了没有 —— 服务器 errno 和客户端完成页给答案，
        # 这比时间差重要得多，所以放最大最上面
        self.l_ok = tk.Label(brief, text="双端删除：—",
                             bg="#f5f7fa", fg="#202124",
                             font=("Microsoft YaHei", 16, "bold"), anchor="w")
        self.l_ok.pack(fill="x", padx=12, pady=(2, 0))

        # 第二结论：谁先删完、差多少 —— 先删完的永远排在这一行里最前面
        self.l_main = tk.Label(brief, text="双删完成：—",
                               bg="#f5f7fa", fg="#5f6368",
                               font=("Microsoft YaHei", 12), anchor="w")
        self.l_main.pack(fill="x", padx=12, pady=(0, 2))

        # 次结论：两端请求「发出」时刻差
        self.l_send = tk.Label(brief, text="请求发出：—",
                               bg="#f5f7fa", fg="#5f6368",
                               font=("Microsoft YaHei", 10), anchor="w")
        self.l_send.pack(fill="x", padx=12, pady=(2, 8))

        # ---------- 下块：详细日志（默认收起） ----------
        self.detail = tk.Frame(root, padx=10)
        self.txt = scrolledtext.ScrolledText(self.detail, wrap="word",
                                             font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True)
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
                 "不需要预测提前量，也不用校准。两个输入框都留空即可。\n"
                 "  · 同步方式填数字 = 时间预置：网页端点完固定等 N 毫秒再点客户端。\n"
                 "  · 发出差填数字 = 目标「两端请求发出」的时间差。比如填 50，\n"
                 "    程序会让客户端晚一点发，让两条请求拉开 50ms，用来做对照实验。\n\n")

        self.pump()

    # ---------- 界面输出 ----------
    def log(self, s):
        self.txt.configure(state="normal")
        self.txt.insert("end", s)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def pump(self):
        """把队列里的输出刷到详细日志区。"""
        try:
            while True:
                self.log(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(80, self.pump)

    def toggle_detail(self):
        """展开 / 收起详细日志。窗口变矮变高时结论区始终留在上面。"""
        if self.detail_shown:
            self.detail.pack_forget()
            self.detail_btn.configure(text="详细日志 ▾")
        else:
            self.detail.pack(fill="both", expand=True, pady=(0, 8))
            self.detail_btn.configure(text="详细日志 ▴")
        self.detail_shown = not self.detail_shown

    # ---------- 结论区渲染 ----------
    def show_brief(self):
        """把 core.LAST_RESULT 里的数字渲染成一句话。

        格式约定：『双删完成：客户端先 | 时间差120ms』
        —— 先删完的那端写在前面，时间差取绝对值，不写正负号。
        """
        r = dict(core.LAST_RESULT)
        if not r:
            self.l_ctx.configure(text="没拿到本轮数据（只核对不删，或执行出错）")
            self.l_ok.configure(text="双端删除：—", fg="#202124")
            self.l_main.configure(text="双删完成：—", fg="#5f6368")
            self.l_send.configure(text="请求发出：—")
            return

        # 上下文
        ctx = f"本次：勾选 {r.get('n_sel', '?')} 个"
        wl = r.get("web_local_ms")
        if wl is not None:
            ctx += f" · 网页端本地段 {wl:.0f} ms"
        self.l_ctx.configure(text=ctx)

        # 第一条：双端成败。网页端看服务器 errno，客户端看「清理完成」页
        def mark(v):
            return "✓" if v is True else ("✗" if v is False else "?")
        wo, co = r.get("web_ok"), r.get("client_ok")
        self.l_ok.configure(
            text=f"双端删除：网页端 {mark(wo)} | 客户端 {mark(co)}",
            fg="#137333" if (wo is True and co is True)
            else ("#c5221f" if (wo is False or co is False) else "#b26a00"))

        # 第二条：谁先删完、差多少（时间差随服务器快慢被拉大，仅参考）
        # 符号约定 delta = 客户端完成 − 网页端完成，正数 = 网页端先删完
        d = r.get("delta_ms")
        if d is None:
            self.l_main.configure(text="双删完成：未测到 | 时间差 ?")
        elif abs(d) < 5:
            self.l_main.configure(text=f"双删完成：几乎同时 | 时间差{abs(d):.0f}ms")
        else:
            first = "网页端" if d > 0 else "客户端"
            self.l_main.configure(text=f"双删完成：{first}先 | 时间差{abs(d):.0f}ms")

        # 次结论：请求发出时刻差（这个才是能调到 0 的）
        sd = r.get("send_diff")
        if sd is None:
            self.l_send.configure(text="请求发出：未测到")
        elif abs(sd) < 5:
            self.l_send.configure(text=f"请求发出：两端几乎同时（{sd:+.1f} ms）")
        elif sd > 0:
            self.l_send.configure(text=f"请求发出：客户端晚 {sd:.1f} ms")
        else:
            self.l_send.configure(text=f"请求发出：客户端早 {-sd:.1f} ms")

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
        core.LAST_RESULT.clear()
        self.l_ok.configure(text="双端删除：执行中…", fg="#202124")
        self.l_main.configure(text="双删完成：执行中…")
        self.l_send.configure(text="请求发出：—")
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

        gap = self.gap.get().strip()
        if gap:
            try:
                float(gap)
                args.append(f"--gap={gap}")
            except ValueError:
                self.log(f"发出差填的 '{gap}' 不是数字，按即时点击处理\n")

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
                # 结论区要在主线程更新，交给 tk 的事件循环
                self.root.after(0, self.show_brief)

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
