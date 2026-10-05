import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import sys

try:
    import winsound
except ImportError:
    winsound = None


class MiniRamenTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("ラーメンタイマー")
        self.root.geometry("250x132+40+40")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.bg = "#202124"
        self.fg = "#f1f3f4"
        self.muted = "#9aa0a6"
        self.accent = "#f6c344"
        self.done = "#ff6b6b"

        self.root.configure(bg=self.bg)

        self.remaining = 180
        self.running = False
        self.end_time = None
        self.after_id = None
        self.drag_x = 0
        self.drag_y = 0

        self.build_ui()
        self.update_display()

    def build_ui(self):
        top = tk.Frame(self.root, bg=self.bg, height=26)
        top.pack(fill="x")
        top.pack_propagate(False)

        title = tk.Label(
            top, text="🍜 RAMEN TIMER",
            bg=self.bg, fg=self.muted,
            font=("Yu Gothic UI", 9, "bold")
        )
        title.pack(side="left", padx=9)

        close_btn = tk.Label(
            top, text="×", bg=self.bg, fg=self.muted,
            font=("Arial", 13, "bold"), cursor="hand2"
        )
        close_btn.pack(side="right", padx=8)
        close_btn.bind("<Button-1>", lambda e: self.close())

        custom_btn = tk.Label(
            top, text="+", bg=self.bg, fg=self.accent,
            font=("Arial", 13, "bold"), cursor="hand2"
        )
        custom_btn.pack(side="right", padx=(0, 5))
        custom_btn.bind("<Button-1>", lambda e: self.custom_time())

        for widget in (top, title):
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)

        self.time_label = tk.Label(
            self.root,
            text="03:00",
            bg=self.bg,
            fg=self.fg,
            font=("Consolas", 34, "bold")
        )
        self.time_label.pack(pady=(0, 2))
        self.time_label.bind("<Button-1>", self.pause_resume)

        btn_frame = tk.Frame(self.root, bg=self.bg)
        btn_frame.pack(pady=(0, 7))

        for label, sec in [("3", 180), ("4", 240), ("5", 300)]:
            b = tk.Button(
                btn_frame,
                text=f"{label}分",
                width=5,
                relief="flat",
                bd=0,
                bg="#303134",
                fg=self.fg,
                activebackground="#3c4043",
                activeforeground=self.fg,
                font=("Yu Gothic UI", 9, "bold"),
                command=lambda s=sec: self.set_timer(s)
            )
            b.pack(side="left", padx=3)

        reset_btn = tk.Button(
            btn_frame,
            text="↻",
            width=3,
            relief="flat",
            bd=0,
            bg="#303134",
            fg=self.muted,
            activebackground="#3c4043",
            activeforeground=self.fg,
            font=("Arial", 10, "bold"),
            command=self.reset
        )
        reset_btn.pack(side="left", padx=(5, 0))

        self.status = tk.Label(
            self.root,
            text="数字を押すとスタート / 時間表示クリックで一時停止",
            bg=self.bg,
            fg=self.muted,
            font=("Yu Gothic UI", 7)
        )
        self.status.pack()

        # 右クリックでも自由時間設定
        for widget in (self.root, top, self.time_label, btn_frame, self.status):
            widget.bind("<Button-3>", lambda e: self.custom_time())

    def start_drag(self, event):
        self.drag_x = event.x_root - self.root.winfo_x()
        self.drag_y = event.y_root - self.root.winfo_y()

    def do_drag(self, event):
        x = event.x_root - self.drag_x
        y = event.y_root - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def set_timer(self, seconds):
        self.cancel_after()
        self.remaining = int(seconds)
        self.time_label.config(fg=self.fg)
        self.running = True
        self.end_time = time.monotonic() + self.remaining
        self.status.config(text="計測中… 🍜")
        self.tick()

    def custom_time(self):
        value = simpledialog.askstring(
            "好きな時間",
            "時間を入力してね。\n例: 3:30  または 210（秒）",
            parent=self.root
        )
        if value is None:
            return

        value = value.strip()
        try:
            if ":" in value:
                parts = value.split(":")
                if len(parts) != 2:
                    raise ValueError
                minutes = int(parts[0])
                seconds = int(parts[1])
                total = minutes * 60 + seconds
            else:
                total = int(value)

            if total <= 0 or total > 24 * 60 * 60:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "入力エラー",
                "「3:30」のように分:秒、または「210」のように秒数で入力してね。",
                parent=self.root
            )
            return

        self.set_timer(total)

    def tick(self):
        if not self.running:
            return

        self.remaining = max(0, int(round(self.end_time - time.monotonic())))
        self.update_display()

        if self.remaining <= 0:
            self.running = False
            self.after_id = None
            self.time_label.config(fg=self.done)
            self.status.config(text="できた！！！ 🍜✨")
            self.alert()
            self.flash()
            return

        self.after_id = self.root.after(200, self.tick)

    def update_display(self):
        mins, secs = divmod(max(0, int(self.remaining)), 60)
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")

    def pause_resume(self, event=None):
        if self.running:
            self.remaining = max(0, int(round(self.end_time - time.monotonic())))
            self.running = False
            self.cancel_after()
            self.status.config(text="一時停止中 / クリックで再開")
            self.update_display()
        elif self.remaining > 0:
            self.running = True
            self.end_time = time.monotonic() + self.remaining
            self.time_label.config(fg=self.fg)
            self.status.config(text="計測中… 🍜")
            self.tick()

    def reset(self):
        self.running = False
        self.cancel_after()
        self.remaining = 180
        self.time_label.config(fg=self.fg)
        self.status.config(text="3分にリセット")
        self.update_display()

    def alert(self):
        if winsound and sys.platform.startswith("win"):
            try:
                for i, freq in enumerate([880, 1047, 1319, 1568]):
                    self.root.after(i * 220, lambda f=freq: winsound.Beep(f, 180))
                return
            except Exception:
                pass

        for i in range(4):
            self.root.after(i * 250, self.root.bell)

    def flash(self):
        sequence = [self.done, self.bg] * 3
        for i, color in enumerate(sequence):
            self.root.after(i * 180, lambda c=color: self.root.configure(bg=c))
        self.root.after(len(sequence) * 180, lambda: self.root.configure(bg=self.bg))

    def cancel_after(self):
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def close(self):
        self.cancel_after()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MiniRamenTimer(root)
    root.mainloop()
