import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from PIL import ImageDraw
import random
import time
from datetime import datetime
import csv

MIN_TILE_SIZE = 60
DEFAULT_TILE_SIZE = 100
GAME_HISTORY_FILE = "game_results.csv"

class JigsawGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🧩 Jigsaw Puzzle Pro")
        self.root.geometry("1000x800")
        self.root.configure(bg="#121212")
        self.root.minsize(900, 700)

        self.size = 3
        self.tile_size = DEFAULT_TILE_SIZE
        self.moves = 0
        self.start_time = time.time()
        self.timer_running = True

        self.puzzle_names = []
        self.puzzle_index = 0
        self.dragged_index = None
        self.dragged_widget = None
        self.win_label = None
        self.reference_window = None
        self.reference_label = None
        self.reference_photo = None
        self.current_source_image = None
        self.resize_job = None
        self.is_updating_level = False
        self.username = ""
        self.current_game_start_ts = None
        self.current_game_start_str = ""
        self.current_game_active = False
        self.current_game_size = None
        self.current_game_puzzle = ""

        if not self.require_username():
            self.root.destroy()
            return
        self.setup_ui()
        self.setup_puzzles()
        self.maximize_window()
        self.load_current_puzzle()
        self.create_game()
        self.update_timer()
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def require_username(self):
        self.root.update_idletasks()
        dialog = tk.Toplevel(self.root)
        dialog.title("Player Login")
        dialog.configure(bg="#121212")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        card = tk.Frame(dialog, bg="#1b1b1b", bd=1, relief="solid")
        card.pack(padx=18, pady=18, fill="both", expand=True)

        tk.Label(
            card,
            text="🧩 Welcome to Jigsaw Puzzle Pro",
            font=("Segoe UI", 14, "bold"),
            fg="#00ffcc",
            bg="#1b1b1b",
        ).pack(padx=16, pady=(16, 8))

        tk.Label(
            card,
            text="Enter your username to start the game",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1b1b1b",
        ).pack(padx=16, pady=(0, 10))

        username_var = tk.StringVar()
        entry = tk.Entry(
            card,
            textvariable=username_var,
            font=("Segoe UI", 11),
            bg="#262626",
            fg="white",
            insertbackground="white",
            relief="flat",
            width=28,
        )
        entry.pack(padx=16, pady=(0, 6), ipady=6)
        entry.focus_set()

        error_label = tk.Label(
            card,
            text="",
            font=("Segoe UI", 9),
            fg="#ff7b7b",
            bg="#1b1b1b",
        )
        error_label.pack(padx=16, pady=(0, 10))

        result = {"ok": False}

        def submit_username(event=None):
            cleaned = username_var.get().strip()
            if not cleaned:
                error_label.config(text="Username is required.")
                return
            self.username = cleaned
            result["ok"] = True
            dialog.destroy()

        def close_dialog():
            should_exit = messagebox.askyesno(
                "Exit Game",
                "Username is required. Do you want to exit?",
                parent=dialog
            )
            if should_exit:
                dialog.destroy()

        button_row = tk.Frame(card, bg="#1b1b1b")
        button_row.pack(pady=(0, 16))

        start_btn = tk.Button(
            button_row,
            text="Start",
            command=submit_username,
            bg="#00c7a4",
            fg="black",
            activebackground="#00ffcc",
            activeforeground="black",
            font=("Segoe UI", 10, "bold"),
            width=10,
            relief="flat",
            cursor="hand2",
        )
        start_btn.pack(side="left", padx=6)

        exit_btn = tk.Button(
            button_row,
            text="Exit",
            command=close_dialog,
            bg="#2f2f2f",
            fg="white",
            activebackground="#404040",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            width=10,
            relief="flat",
            cursor="hand2",
        )
        exit_btn.pack(side="left", padx=6)

        dialog.bind("<Return>", submit_username)
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
        dialog.geometry(f"+{max(x, 20)}+{max(y, 20)}")

        self.root.wait_window(dialog)
        return result["ok"]

    def get_current_puzzle_name(self):
        if not self.puzzle_names:
            return ""
        if 0 <= self.puzzle_index < len(self.puzzle_names):
            return self.puzzle_names[self.puzzle_index]
        return ""

    def log_game_end(self, end_reason, result=""):
        if not self.current_game_active or self.current_game_start_ts is None:
            return

        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = int(time.time() - self.current_game_start_ts)
        headers = [
            "username",
            "start_time",
            "end_time",
            "total_time_seconds",
            "size",
            "puzzle",
            "result",
            "moves",
            "end_reason",
        ]
        new_row = [
            self.username,
            self.current_game_start_str,
            end_time_str,
            elapsed,
            self.current_game_size,
            self.current_game_puzzle,
            result,
            self.moves,
            end_reason,
        ]

        try:
            existing_rows = []
            try:
                with open(GAME_HISTORY_FILE, "r", newline="", encoding="utf-8") as read_file:
                    reader = csv.reader(read_file)
                    existing_rows = list(reader)
            except FileNotFoundError:
                existing_rows = []

            data_rows = existing_rows
            if existing_rows and existing_rows[0] == headers:
                data_rows = existing_rows[1:]

            with open(GAME_HISTORY_FILE, "w", newline="", encoding="utf-8") as write_file:
                writer = csv.writer(write_file)
                writer.writerow(headers)
                writer.writerow(new_row)
                for row in data_rows:
                    if row:
                        writer.writerow(row)
        except Exception:
            pass
        finally:
            self.current_game_active = False
            self.current_game_start_ts = None

    # ---------------- UI ----------------
    def setup_ui(self):
        title = tk.Label(self.root, text="🧩 Jigsaw Puzzle Pro",
                         font=("Segoe UI", 22, "bold"),
                         fg="#00ffcc", bg="#121212")
        title.pack(pady=10)

        self.info_label = tk.Label(self.root, text="",
                                  font=("Segoe UI", 12),
                                  fg="white", bg="#121212")
        self.info_label.pack()

        control_frame = tk.Frame(self.root, bg="#121212")
        control_frame.pack(pady=10)

        def styled_btn(text, cmd):
            btn = tk.Button(
                control_frame,
                text=text,
                command=cmd,
                bg="#2c2c2c",
                fg="white",
                activebackground="#00ffcc",
                activeforeground="black",
                font=("Segoe UI", 10, "bold"),
                width=10,
                relief="flat",
                bd=0,
                cursor="hand2"
            )
            btn.bind("<Enter>", lambda e: btn.config(bg="#00ffcc", fg="black"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#2c2c2c", fg="white"))
            return btn

        styled_btn("3x3", lambda: self.set_level(3)).grid(row=0, column=0, padx=6)
        styled_btn("4x4", lambda: self.set_level(4)).grid(row=0, column=1, padx=6)
        styled_btn("5x5", lambda: self.set_level(5)).grid(row=0, column=2, padx=6)
        styled_btn("Puzzle", self.next_puzzle).grid(row=0, column=3, padx=6)
        styled_btn("Reference", self.show_reference).grid(row=0, column=4, padx=6)
        styled_btn("Restart", self.restart).grid(row=0, column=5, padx=6)

        self.frame = tk.Frame(self.root, bg="#000")
        self.frame.pack(pady=20, expand=True)

    def maximize_window(self):
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

    # ---------------- Image ----------------
    def setup_puzzles(self):
        base_size = 800
        self.puzzles = {}

        try:
            self.puzzles["My Image"] = Image.open("image.jpg").convert("RGB")
        except Exception:
            pass

        self.puzzles["Mountain Valley"] = self.make_mountain_valley_puzzle(base_size)
        self.puzzles["Forest Lake"] = self.make_forest_lake_puzzle(base_size)
        self.puzzles["Blue Bird"] = self.make_blue_bird_puzzle(base_size)
        self.puzzles["Cute Cat"] = self.make_cute_cat_puzzle(base_size)
        self.puzzles["Butterfly Meadow"] = self.make_butterfly_meadow_puzzle(base_size)

        self.puzzle_names = list(self.puzzles.keys())

    def load_current_puzzle(self):
        if not self.puzzle_names:
            raise ValueError("No puzzle images available.")
        current_name = self.puzzle_names[self.puzzle_index]
        self.current_source_image = self.puzzles[current_name]
        self.resize_current_image()
        self.root.title(f"🧩 Jigsaw Puzzle Pro - {current_name}")

    def resize_current_image(self):
        target_side = self.size * self.tile_size
        if hasattr(Image, "Resampling"):
            resample_filter = Image.Resampling.LANCZOS
        else:
            resample_filter = Image.LANCZOS
        self.image = self.current_source_image.resize((target_side, target_side), resample_filter)
        self.refresh_reference_window()

    def show_reference(self):
        if self.reference_window is None or not self.reference_window.winfo_exists():
            self.reference_window = tk.Toplevel(self.root)
            self.reference_window.title("Reference Image")
            self.reference_window.configure(bg="#121212")
            self.reference_window.resizable(False, False)
            self.reference_window.transient(self.root)

            self.reference_label = tk.Label(self.reference_window, bg="#121212")
            self.reference_label.pack(padx=10, pady=10)
        self.refresh_reference_window()
        self.reference_window.lift()
        self.reference_window.focus_force()

    def refresh_reference_window(self):
        if (
            self.reference_window is None
            or not self.reference_window.winfo_exists()
            or self.reference_label is None
        ):
            return

        self.reference_photo = ImageTk.PhotoImage(self.image)
        self.reference_label.config(image=self.reference_photo)

    def make_mountain_valley_puzzle(self, side):
        image = Image.new("RGB", (side, side), "#9fd6ff")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, side * 0.6, side, side), fill="#79b85f")
        draw.polygon([(80, 520), (280, 180), (470, 520)], fill="#607d8b")
        draw.polygon([(280, 210), (330, 300), (230, 300)], fill="white")
        draw.polygon([(330, 540), (540, 220), (740, 540)], fill="#546e7a")
        draw.polygon([(540, 250), (590, 340), (490, 340)], fill="white")
        draw.ellipse((95, 95, 200, 200), fill="#ffd54f")
        return image

    def make_forest_lake_puzzle(self, side):
        image = Image.new("RGB", (side, side), "#b3e5fc")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, side * 0.58, side, side), fill="#4caf50")
        draw.ellipse((120, 420, 680, 760), fill="#42a5f5")
        for x in (120, 250, 380, 510, 640):
            draw.rectangle((x, 260, x + 25, 560), fill="#5d4037")
            draw.polygon([(x - 60, 320), (x + 12, 190), (x + 85, 320)], fill="#2e7d32")
            draw.polygon([(x - 55, 385), (x + 12, 255), (x + 80, 385)], fill="#388e3c")
        return image

    def make_blue_bird_puzzle(self, side):
        image = Image.new("RGB", (side, side), "#e1f5fe")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, side * 0.75, side, side), fill="#9ccc65")
        draw.ellipse((180, 250, 620, 560), fill="#42a5f5")
        draw.ellipse((530, 290, 700, 430), fill="#64b5f6")
        draw.polygon([(670, 360), (760, 340), (670, 395)], fill="#ffb74d")
        draw.ellipse((620, 335, 650, 365), fill="white")
        draw.ellipse((631, 345, 643, 357), fill="black")
        draw.ellipse((260, 310, 520, 520), fill="#1e88e5")
        draw.arc((210, 250, 620, 560), start=200, end=340, fill="#1565c0", width=8)
        return image

    def make_cute_cat_puzzle(self, side):
        image = Image.new("RGB", (side, side), "#fff8e1")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, side * 0.72, side, side), fill="#d7ccc8")
        draw.ellipse((220, 220, 580, 610), fill="#ffcc80")
        draw.polygon([(255, 275), (320, 150), (365, 305)], fill="#ffb74d")
        draw.polygon([(435, 305), (480, 150), (545, 275)], fill="#ffb74d")
        draw.ellipse((295, 340, 360, 395), fill="white")
        draw.ellipse((440, 340, 505, 395), fill="white")
        draw.ellipse((322, 362, 342, 382), fill="#4e342e")
        draw.ellipse((467, 362, 487, 382), fill="#4e342e")
        draw.polygon([(390, 410), (410, 440), (370, 440)], fill="#f06292")
        draw.line((280, 445, 355, 435), fill="#6d4c41", width=3)
        draw.line((280, 465, 355, 460), fill="#6d4c41", width=3)
        draw.line((445, 435, 520, 445), fill="#6d4c41", width=3)
        draw.line((445, 460, 520, 465), fill="#6d4c41", width=3)
        return image

    def make_butterfly_meadow_puzzle(self, side):
        image = Image.new("RGB", (side, side), "#b3e5fc")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, side * 0.62, side, side), fill="#66bb6a")
        draw.ellipse((285, 280, 515, 520), fill="#f06292")
        draw.ellipse((350, 280, 580, 520), fill="#ba68c8")
        draw.ellipse((225, 350, 455, 590), fill="#ff8a65")
        draw.ellipse((410, 350, 640, 590), fill="#ffd54f")
        draw.rectangle((392, 300, 408, 560), fill="#263238")
        draw.line((400, 300, 365, 250), fill="#263238", width=3)
        draw.line((400, 300, 435, 250), fill="#263238", width=3)
        for x in (100, 180, 690):
            draw.line((x, 700, x, 590), fill="#2e7d32", width=6)
            draw.ellipse((x - 25, 555, x + 25, 605), fill="#ef5350")
        return image

    # ---------------- Game Setup ----------------
    def build_tiles(self):
        self.tiles = []
        self.correct_order = []

        for i in range(self.size):
            for j in range(self.size):
                box = (
                    j * self.tile_size,
                    i * self.tile_size,
                    (j + 1) * self.tile_size,
                    (i + 1) * self.tile_size,
                )
                tile = self.image.crop(box)
                self.tiles.append(ImageTk.PhotoImage(tile))
                self.correct_order.append(len(self.correct_order))

    def create_game(self):
        self.build_tiles()

        self.order = list(range(len(self.tiles)))
        random.shuffle(self.order)

        self.moves = 0
        self.start_time = time.time()
        self.timer_running = True
        if self.win_label is not None:
            self.win_label.destroy()
            self.win_label = None

        self.current_game_start_ts = time.time()
        self.current_game_start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_game_active = True
        self.current_game_size = self.size
        self.current_game_puzzle = self.get_current_puzzle_name()

        self.draw_tiles()

    def rebuild_board_for_resize(self):
        if not hasattr(self, "order"):
            return

        previous_order = list(self.order)
        self.build_tiles()
        tile_count = len(self.tiles)

        is_valid_previous_order = (
            len(previous_order) == tile_count
            and all(0 <= idx < tile_count for idx in previous_order)
        )

        if is_valid_previous_order:
            self.order = previous_order
        else:
            self.order = list(range(tile_count))
            random.shuffle(self.order)
            self.moves = 0
            self.start_time = time.time()
            self.timer_running = True
            if self.win_label is not None:
                self.win_label.destroy()
                self.win_label = None

        self.draw_tiles()

    # ---------------- Draw ----------------
    def draw_tiles(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        for index, tile_index in enumerate(self.order):
            lbl = tk.Label(self.frame, image=self.tiles[tile_index],
                           bd=2, relief="raised", bg="black")

            lbl.grid(row=index//self.size, column=index%self.size)

            lbl.bind("<Button-1>", lambda e, i=index: self.start_drag(e, i))
            lbl.bind("<B1-Motion>", self.on_drag)
            lbl.bind("<ButtonRelease-1>", self.drop_tile)

        self.update_info()

    def start_drag(self, event, index):
        if not self.timer_running:
            return
        self.dragged_index = index
        self.dragged_widget = event.widget
        self.dragged_widget.lift()

    def on_drag(self, event):
        if self.dragged_widget:
            x = event.x_root - self.frame.winfo_rootx() - self.tile_size // 2
            y = event.y_root - self.frame.winfo_rooty() - self.tile_size // 2
            self.dragged_widget.place(x=x, y=y)

    def drop_tile(self, event):
        if self.dragged_index is None:
            return

        frame_x = event.x_root - self.frame.winfo_rootx()
        frame_y = event.y_root - self.frame.winfo_rooty()

        col = frame_x // self.tile_size
        row = frame_y // self.tile_size
        target_index = row * self.size + col

        is_inside_board = (
            0 <= col < self.size
            and 0 <= row < self.size
            and 0 <= target_index < len(self.order)
        )

        if is_inside_board and self.dragged_index != target_index:
            self.order[self.dragged_index], self.order[target_index] = (
                self.order[target_index],
                self.order[self.dragged_index],
            )
            self.moves += 1
            self.draw_tiles()
            self.check_win()
        else:
            self.draw_tiles()

        self.dragged_index = None
        self.dragged_widget = None

    # ---------------- Game Logic ----------------
    def check_win(self):
        if self.order == self.correct_order:
            self.timer_running = False
            if self.current_game_active:
                self.log_game_end(end_reason="win", result="win")
            if self.win_label is None:
                self.win_label = tk.Label(
                    self.root, text="🎉 YOU WIN!",
                    font=("Segoe UI", 18, "bold"),
                    fg="#00ffcc", bg="#121212"
                )
                self.win_label.pack(pady=10)

    # ---------------- Timer ----------------
    def update_timer(self):
        if self.timer_running:
            elapsed = int(time.time() - self.start_time)
            self.time_str = f"Time: {elapsed}s"
            self.update_info()
        self.root.after(1000, self.update_timer)

    def update_info(self):
        self.info_label.config(
            text=(
                f"User: {self.username} | "
                f"Moves: {self.moves} | "
                f"{getattr(self, 'time_str', 'Time: 0s')}"
            )
        )

    # ---------------- Controls ----------------
    def restart(self):
        self.log_game_end(end_reason="restart")
        self.create_game()

    def set_level(self, size):
        if self.is_updating_level:
            return
        self.is_updating_level = True
        try:
            self.log_game_end(end_reason="size_change")
            self.size = size
            self.update_responsive_layout()
            self.load_current_puzzle()
            self.create_game()
        finally:
            self.is_updating_level = False

    def next_puzzle(self):
        self.log_game_end(end_reason="puzzle_change")
        self.puzzle_index = (self.puzzle_index + 1) % len(self.puzzle_names)
        self.load_current_puzzle()
        self.create_game()

    def on_window_resize(self, event):
        if event.widget is not self.root:
            return
        if self.is_updating_level:
            return
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(120, self.update_responsive_layout)

    def update_responsive_layout(self):
        self.resize_job = None
        if not hasattr(self, "order"):
            return

        available_width = max(300, self.root.winfo_width() - 80)
        available_height = max(300, self.root.winfo_height() - 260)
        board_side = min(available_width, available_height)
        new_tile_size = max(MIN_TILE_SIZE, board_side // self.size)

        if new_tile_size == self.tile_size:
            return

        self.tile_size = new_tile_size
        self.resize_current_image()
        self.rebuild_board_for_resize()

    def on_app_close(self):
        self.log_game_end(end_reason="app_close")
        self.root.destroy()


# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = JigsawGame(root)
    root.mainloop()
