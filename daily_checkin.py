#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日打卡 · Daily Check-in
一款简洁的桌面打卡软件，数据保存在本地 JSON 文件中。
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import sys
from datetime import datetime, timedelta

# ── 数据路径 ──────────────────────────────────────────
def get_data_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")
    folder = os.path.join(base, "DailyCheckin")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "data.json")

DATA_FILE = get_data_path()

# ── 默认数据 ───────────────────────────────────────────
DEFAULT_TASKS = [
    {"id": 1, "emoji": "💧", "text": "喝够 8 杯水"},
    {"id": 2, "emoji": "📚", "text": "阅读 30 分钟"},
    {"id": 3, "emoji": "🏃", "text": "运动锻炼"},
]

# ── 颜色主题 ───────────────────────────────────────────
C = {
    "bg":        "#FAF8F4",
    "card":      "#FFFFFF",
    "border":    "#E8E2D8",
    "green":     "#4A7C59",
    "green_bg":  "#EDF4F0",
    "green_lt":  "#D4EADB",
    "amber":     "#C17F2A",
    "amber_bg":  "#FDF4E7",
    "red":       "#C0392B",
    "red_bg":    "#FDECEA",
    "text":      "#2C2820",
    "text2":     "#7A7267",
    "text3":     "#B5AFA6",
    "progress_bg": "#EDE8DF",
    "done_text": "#9BB8A4",
}

EMOJIS = ["📌","💪","📚","🏃","💧","🥗","😴","🧘","✍️","🎯","🌿","🎵","🎨","💊","🌅","🧹","🐾","☀️","🧴","🍎"]


def today_str():
    return datetime.today().strftime("%Y-%m-%d")


# ── 数据存取 ───────────────────────────────────────────
class DataStore:
    def __init__(self):
        self._data = {"tasks": DEFAULT_TASKS.copy(), "logs": {}}
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    self._data["tasks"] = d.get("tasks", DEFAULT_TASKS.copy())
                    self._data["logs"]  = d.get("logs", {})
            except Exception:
                pass

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    @property
    def tasks(self):
        return self._data["tasks"]

    @property
    def logs(self):
        return self._data["logs"]

    def today_log(self):
        return self._data["logs"].setdefault(today_str(), {})

    def toggle(self, task_id):
        log = self.today_log()
        tid = str(task_id)
        if tid in log:
            del log[tid]
        else:
            log[tid] = 1
        self.save()

    def is_done(self, task_id):
        return str(task_id) in self.today_log()

    def add_task(self, emoji, text):
        new_id = max((t["id"] for t in self.tasks), default=0) + 1
        self.tasks.append({"id": new_id, "emoji": emoji, "text": text})
        self.save()

    def delete_task(self, task_id):
        self._data["tasks"] = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    def done_count(self):
        return sum(1 for t in self.tasks if self.is_done(t["id"]))

    def streak(self):
        n = 0
        d = datetime.today()
        while True:
            s = d.strftime("%Y-%m-%d")
            log = self._data["logs"].get(s, {})
            done = sum(1 for t in self.tasks if str(t["id"]) in log)
            if self.tasks and done == len(self.tasks):
                n += 1
                d -= timedelta(days=1)
            else:
                break
            if n > 3650:
                break
        return n


# ── 圆角矩形辅助 ─────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1+r, y1,  x2-r, y1,
        x2,   y1,  x2,   y1+r,
        x2,   y2-r,x2,   y2,
        x2-r, y2,  x1+r, y2,
        x1,   y2,  x1,   y2-r,
        x1,   y1+r,x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ── 主界面 ────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = DataStore()
        self.title("每日打卡")
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        # 居中窗口
        w, h = 460, 720
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._emoji_cycle = [0]  # emoji index for add field

        self._build_ui()
        self._refresh()

    # ── 构建 UI ────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        # 顶栏
        top = tk.Frame(outer, bg=C["bg"])
        top.pack(fill="x", pady=(0, 10))

        left = tk.Frame(top, bg=C["bg"])
        left.pack(side="left")

        self.lbl_date = tk.Label(left, bg=C["bg"], fg=C["text3"],
                                 font=("", 10), anchor="w")
        self.lbl_date.pack(anchor="w")

        tk.Label(left, text="今日打卡", bg=C["bg"], fg=C["text"],
                 font=("", 20, "bold"), anchor="w").pack(anchor="w")

        right = tk.Frame(top, bg=C["amber_bg"], relief="flat",
                         bd=1, padx=12, pady=6)
        right.pack(side="right", anchor="n")
        tk.Label(right, text="🔥", bg=C["amber_bg"],
                 font=("", 14)).pack(side="left")
        self.lbl_streak = tk.Label(right, text="0 天连续",
                                   bg=C["amber_bg"], fg=C["amber"],
                                   font=("", 11, "bold"))
        self.lbl_streak.pack(side="left")

        # 进度
        prog_head = tk.Frame(outer, bg=C["bg"])
        prog_head.pack(fill="x", pady=(4, 3))
        tk.Label(prog_head, text="今日进度", bg=C["bg"],
                 fg=C["text2"], font=("", 10)).pack(side="left")
        self.lbl_count = tk.Label(prog_head, text="0 / 0",
                                  bg=C["bg"], fg=C["text"],
                                  font=("", 10, "bold"))
        self.lbl_count.pack(side="right")

        self.canvas_prog = tk.Canvas(outer, height=8, bg=C["progress_bg"],
                                     highlightthickness=0, bd=0)
        self.canvas_prog.pack(fill="x", pady=(0, 10))

        # 完成横幅（隐藏）
        self.banner = tk.Label(outer,
                               text="🎉  太棒了！今日任务全部完成！",
                               bg=C["green_bg"], fg=C["green"],
                               font=("", 11, "bold"),
                               pady=8, relief="flat")

        # 任务滚动区
        task_frame = tk.Frame(outer, bg=C["bg"])
        task_frame.pack(fill="both", expand=True)

        self.canvas_tasks = tk.Canvas(task_frame, bg=C["bg"],
                                      highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(task_frame, orient="vertical",
                                  command=self.canvas_tasks.yview)
        self.canvas_tasks.configure(yscrollcommand=scrollbar.set)
        self.canvas_tasks.pack(side="left", fill="both", expand=True)

        self.task_inner = tk.Frame(self.canvas_tasks, bg=C["bg"])
        self._window_id = self.canvas_tasks.create_window(
            (0, 0), window=self.task_inner, anchor="nw")
        self.task_inner.bind("<Configure>", self._on_task_resize)
        self.canvas_tasks.bind("<Configure>", self._on_canvas_resize)

        # 鼠标滚轮
        self.canvas_tasks.bind_all("<MouseWheel>",
            lambda e: self.canvas_tasks.yview_scroll(-1*(e.delta//120), "units"))
        self.canvas_tasks.bind_all("<Button-4>",
            lambda e: self.canvas_tasks.yview_scroll(-1, "units"))
        self.canvas_tasks.bind_all("<Button-5>",
            lambda e: self.canvas_tasks.yview_scroll(1, "units"))

        # 添加区
        add_card = tk.Frame(outer, bg=C["card"],
                            relief="flat", bd=0, pady=8, padx=12)
        add_card.pack(fill="x", pady=(10, 8))
        add_card.config(highlightbackground=C["border"],
                        highlightthickness=1)

        self.lbl_emoji_pick = tk.Label(add_card, text=EMOJIS[0],
                                       bg=C["bg"], font=("", 16),
                                       cursor="hand2", padx=6, pady=4,
                                       relief="flat")
        self.lbl_emoji_pick.pack(side="left")
        self.lbl_emoji_pick.bind("<Button-1>", self._cycle_emoji)

        self.entry_task = tk.Entry(add_card, bd=0, relief="flat",
                                   bg=C["card"], fg=C["text"],
                                   font=("", 13), insertbackground=C["text"])
        self.entry_task.pack(side="left", fill="x", expand=True, padx=6)
        self.entry_task.insert(0, "新增打卡事项…")
        self.entry_task.config(fg=C["text3"])
        self.entry_task.bind("<FocusIn>",  self._entry_focus_in)
        self.entry_task.bind("<FocusOut>", self._entry_focus_out)
        self.entry_task.bind("<Return>", lambda e: self._add_task())

        add_btn = tk.Button(add_card, text="添加",
                            bg=C["green"], fg="white",
                            font=("", 11, "bold"),
                            relief="flat", bd=0,
                            padx=12, pady=4, cursor="hand2",
                            command=self._add_task,
                            activebackground="#3d6b4c",
                            activeforeground="white")
        add_btn.pack(side="right")

        # 历史
        tk.Label(outer, text="近 30 天记录", bg=C["bg"],
                 fg=C["text3"], font=("", 9)).pack(anchor="w", pady=(4, 5))
        self.hist_frame = tk.Frame(outer, bg=C["bg"])
        self.hist_frame.pack(fill="x")

    # ── 刷新 ───────────────────────────────────────────
    def _refresh(self):
        self._refresh_date()
        self._refresh_progress()
        self._refresh_tasks()
        self._refresh_history()
        self._refresh_streak()

    def _refresh_date(self):
        d = datetime.today()
        weekdays = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
        wd = weekdays[d.weekday()]
        self.lbl_date.config(
            text=f"{d.year}年{d.month}月{d.day}日  {wd}")

    def _refresh_progress(self):
        done  = self.store.done_count()
        total = len(self.store.tasks)
        self.lbl_count.config(text=f"{done} / {total}")

        # 进度条
        self.canvas_prog.update_idletasks()
        w = self.canvas_prog.winfo_width()
        h = 8
        self.canvas_prog.delete("all")
        r = 4
        # 背景
        rounded_rect(self.canvas_prog, 0, 0, w, h, r,
                     fill=C["progress_bg"], outline="")
        # 前景
        if total > 0:
            pw = max(int(w * done / total), 0)
            if pw >= r*2:
                rounded_rect(self.canvas_prog, 0, 0, pw, h, r,
                             fill=C["green"], outline="")
            elif pw > 0:
                self.canvas_prog.create_rectangle(
                    0, 0, pw, h, fill=C["green"], outline="")

        # 横幅
        if total > 0 and done == total:
            self.banner.pack(fill="x", pady=(0, 6))
        else:
            self.banner.pack_forget()

    def _refresh_tasks(self):
        for w in self.task_inner.winfo_children():
            w.destroy()

        if not self.store.tasks:
            tk.Label(self.task_inner,
                     text="✨  还没有事项，添加第一个吧！",
                     bg=C["bg"], fg=C["text3"],
                     font=("", 12), pady=30).pack()
            return

        for task in self.store.tasks:
            self._make_task_row(task)

    def _make_task_row(self, task):
        done = self.store.is_done(task["id"])
        bg   = C["green_bg"] if done else C["card"]

        row = tk.Frame(self.task_inner, bg=bg, pady=10, padx=14,
                       relief="flat", bd=0,
                       highlightbackground=C["green_lt"] if done else C["border"],
                       highlightthickness=1)
        row.pack(fill="x", pady=4)

        # 圆形复选框
        chk_canvas = tk.Canvas(row, width=24, height=24, bg=bg,
                               highlightthickness=0, bd=0)
        chk_canvas.pack(side="left", padx=(0, 8))
        if done:
            chk_canvas.create_oval(0, 0, 23, 23, fill=C["green"], outline="")
            chk_canvas.create_line(5, 12, 10, 18, fill="white", width=2,
                                   capstyle="round")
            chk_canvas.create_line(10, 18, 19, 6, fill="white", width=2,
                                   capstyle="round")
        else:
            chk_canvas.create_oval(0, 0, 23, 23, fill="white",
                                   outline=C["border"], width=1.5)

        # emoji
        tk.Label(row, text=task["emoji"], bg=bg,
                 font=("", 16), width=2).pack(side="left")

        # 文字
        fg_text = C["done_text"] if done else C["text"]
        lbl = tk.Label(row, text=task["text"], bg=bg,
                       fg=fg_text, font=("", 13),
                       anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))
        if done:
            lbl.config(font=("", 13, "overstrike"))

        # 删除按钮
        del_btn = tk.Label(row, text="✕", bg=bg,
                           fg=C["text3"], font=("", 12),
                           cursor="hand2", padx=6)
        del_btn.pack(side="right")
        del_btn.bind("<Button-1>",
                     lambda e, tid=task["id"]: self._delete_task(tid))
        del_btn.bind("<Enter>",
                     lambda e, b=del_btn: b.config(fg=C["red"]))
        del_btn.bind("<Leave>",
                     lambda e, b=del_btn: b.config(fg=C["text3"]))

        # 点击整行切换
        for widget in (row, lbl, chk_canvas):
            widget.bind("<Button-1>",
                        lambda e, tid=task["id"]: self._toggle(tid))
        row.bind("<Enter>",
                 lambda e, r=row, d=done: r.config(
                     cursor="hand2"))
        row.bind("<Leave>",
                 lambda e, r=row: r.config(cursor=""))

    def _refresh_history(self):
        for w in self.hist_frame.winfo_children():
            w.destroy()
        today = today_str()
        for i in range(29, -1, -1):
            d   = datetime.today() - timedelta(days=i)
            s   = d.strftime("%Y-%m-%d")
            log = self.store.logs.get(s, {})
            done  = sum(1 for t in self.store.tasks
                        if str(t["id"]) in log)
            total = len(self.store.tasks)

            if total > 0 and done == total:
                bg, fg = C["green"], "white"
            elif done > 0:
                bg, fg = C["green_lt"], C["green"]
            else:
                bg, fg = C["progress_bg"], C["text3"]

            cell = tk.Label(self.hist_frame,
                            text=str(d.day),
                            bg=bg, fg=fg,
                            font=("", 9, "bold"),
                            width=3, height=1,
                            relief="flat", bd=0,
                            padx=0, pady=4)
            cell.pack(side="left", padx=1, pady=1)
            if s == today:
                cell.config(relief="solid", bd=1,
                            highlightbackground=C["green"])

            tip_text = f"{d.month}/{d.day} {done}/{total}"
            cell.bind("<Enter>",
                      lambda e, c=cell, t=tip_text:
                      c.config(relief="solid"))
            cell.bind("<Leave>",
                      lambda e, c=cell:
                      c.config(relief="flat", bd=0))

    def _refresh_streak(self):
        n = self.store.streak()
        self.lbl_streak.config(
            text=f"{n} 天连续" if n > 0 else "今日开始")

    # ── 交互 ───────────────────────────────────────────
    def _toggle(self, task_id):
        self.store.toggle(task_id)
        self._refresh()

    def _delete_task(self, task_id):
        task = next((t for t in self.store.tasks
                     if t["id"] == task_id), None)
        if task and messagebox.askyesno(
                "删除确认",
                f"确认删除「{task['text']}」吗？"):
            self.store.delete_task(task_id)
            self._refresh()

    def _add_task(self):
        text = self.entry_task.get().strip()
        if not text or text == "新增打卡事项…":
            return
        emoji = self.lbl_emoji_pick.cget("text")
        self.store.add_task(emoji, text)
        self.entry_task.delete(0, tk.END)
        self.entry_task.insert(0, "新增打卡事项…")
        self.entry_task.config(fg=C["text3"])
        self._cycle_emoji(None)
        self._refresh()

    def _cycle_emoji(self, event):
        self._emoji_cycle[0] = (self._emoji_cycle[0] + 1) % len(EMOJIS)
        self.lbl_emoji_pick.config(text=EMOJIS[self._emoji_cycle[0]])

    def _entry_focus_in(self, event):
        if self.entry_task.get() == "新增打卡事项…":
            self.entry_task.delete(0, tk.END)
            self.entry_task.config(fg=C["text"])

    def _entry_focus_out(self, event):
        if not self.entry_task.get().strip():
            self.entry_task.insert(0, "新增打卡事项…")
            self.entry_task.config(fg=C["text3"])

    def _on_task_resize(self, event):
        self.canvas_tasks.configure(
            scrollregion=self.canvas_tasks.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas_tasks.itemconfig(
            self._window_id, width=event.width)


if __name__ == "__main__":
    app = App()
    app.mainloop()
