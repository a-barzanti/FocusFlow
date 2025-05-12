import customtkinter as ctk
import json
import time
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Task:
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration  # in minutes

    def to_dict(self):
        return {"name": self.name, "duration": self.duration}

    @staticmethod
    def from_dict(data):
        return Task(data["name"], data["duration"])


class TaskApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Focus Flow")
        self.geometry("500x600")

        self.tasks = []
        self.task_widgets = []
        self.rotation_thread = None
        self.running = False
        self.paused = False
        self.current_task_index = 0
        self.selected_index = None

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.rotation_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.rotation_label = ctk.CTkLabel(
            self.rotation_frame,
            text="",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.rotation_label.pack(expand=True, fill="both", padx=20, pady=20)
        self.pause_button = ctk.CTkButton(
            self.rotation_frame,
            text="⏸️",
            command=self.pause_rotation,
            width=40,
            fg_color="#d1d5db",  # Tailwind gray-300
            hover_color="#9ca3af",  # gray-400
            text_color="#1f2937",  # gray-800
        )
        self.pause_button.pack(anchor="e", padx=20, pady=20)

        self.name_label = ctk.CTkLabel(self.main_frame, text="Task Name:")
        self.name_label.pack(anchor="w", padx=10)
        self.task_name_entry = ctk.CTkEntry(self.main_frame)
        self.task_name_entry.pack(fill="x", padx=10, pady=5)

        self.duration_label = ctk.CTkLabel(self.main_frame, text="Duration (min):")
        self.duration_label.pack(anchor="w", padx=10)
        self.duration_entry = ctk.CTkEntry(self.main_frame)
        self.duration_entry.pack(fill="x", padx=10, pady=5)

        self.task_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.task_buttons_frame.pack(pady=5, padx=5, anchor="w")

        self.save_task_button = ctk.CTkButton(
            self.task_buttons_frame,
            text="✅",
            command=self.save_task,
            width=40,
            fg_color="#d1d5db",
            hover_color="#b0b8c4",
            text_color="#1f2937",
        )
        self.save_task_button.grid(row=0, column=0, padx=5)

        self.new_task_button = ctk.CTkButton(
            self.task_buttons_frame,
            text="➕",
            command=self.prepare_new_task,
            width=40,
            fg_color="#d1d5db",
            hover_color="#b0b8c4",
            text_color="#1f2937",
        )
        self.new_task_button.grid(row=0, column=1, padx=5)

        self.move_up_button = ctk.CTkButton(
            self.task_buttons_frame,
            text="⬆️",
            command=self.move_task_up,
            width=40,
            fg_color="#d1d5db",
            hover_color="#b0b8c4",
            text_color="#1f2937",
        )
        self.move_up_button.grid(row=0, column=2, padx=5)

        self.move_down_button = ctk.CTkButton(
            self.task_buttons_frame,
            text="⬇️",
            command=self.move_task_down,
            width=40,
            fg_color="#d1d5db",
            hover_color="#b0b8c4",
            text_color="#1f2937",
        )
        self.move_down_button.grid(row=0, column=3, padx=5)

        self.delete_button = ctk.CTkButton(
            self.task_buttons_frame,
            text="🗑️",
            command=self.delete_task,
            width=40,
            fg_color="#d1d5db",
            hover_color="#b0b8c4",
            text_color="#1f2937",
        )
        self.delete_button.grid(row=0, column=4, padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_frame, width=450, height=250
        )
        self.scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.rotation_buttons = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.rotation_buttons.pack(pady=10, anchor="w")

        self.start_button = ctk.CTkButton(
            self.rotation_buttons,
            text="▶️",
            command=self.start_rotation,
            width=40,
            fg_color="#d1d5db",  # Tailwind gray-300
            hover_color="#9ca3af",  # gray-400
            text_color="#1f2937",  # gray-800
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ctk.CTkButton(
            self.rotation_buttons,
            text="⏹️",
            command=self.stop_rotation,
            width=40,
            fg_color="#d1d5db",
            hover_color="#9ca3af",
            text_color="#1f2937",
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.save_button = ctk.CTkButton(
            self.rotation_buttons,
            text="⮕💾",
            command=self.save_tasks,
            width=40,
            fg_color="#d1d5db",
            hover_color="#9ca3af",
            text_color="#1f2937",
        )
        self.save_button.grid(row=0, column=2, padx=5)

        self.load_button = ctk.CTkButton(
            self.rotation_buttons,
            text="💾⮕",
            command=self.load_tasks,
            width=40,
            fg_color="#d1d5db",
            hover_color="#9ca3af",
            text_color="#1f2937",
        )
        self.load_button.grid(row=0, column=3, padx=5)

        self.status_label = ctk.CTkLabel(self.main_frame, text="")
        self.status_label.pack(pady=10)

        self.bind("<Up>", lambda event: self.move_task_up())
        self.bind("<Down>", lambda event: self.move_task_down())
        self.bind("<Delete>", lambda event: self.delete_task())

    def prepare_new_task(self):
        self.selected_index = None
        self.task_name_entry.delete(0, "end")
        self.duration_entry.delete(0, "end")
        self.status_label.configure(text="Creating new task")

    def save_task(self):
        name = self.task_name_entry.get()
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            self.status_label.configure(text="Duration must be a number")
            return
        if self.selected_index is not None:
            self.tasks[self.selected_index] = Task(name, duration)
            self.status_label.configure(text="Task updated")
        else:
            self.tasks.append(Task(name, duration))
            self.status_label.configure(text="New task added")
        self.refresh_task_list()

    def delete_task(self):
        if self.selected_index is not None:
            self.tasks.pop(self.selected_index)
            self.selected_index = None
            self.refresh_task_list()
            self.status_label.configure(text="Task deleted")

    def refresh_task_list(self):
        for widget in self.task_widgets:
            widget.destroy()
        self.task_widgets.clear()
        for i, task in enumerate(self.tasks):
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.grid(row=i, column=0, sticky="nsew", padx=5, pady=2)
            self.scroll_frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            bg_color = "#444444" if i == self.selected_index else "transparent"
            text_color = "white" if i == self.selected_index else None

            label = ctk.CTkLabel(
                frame,
                text=f"{task.name} - {task.duration} min",
                anchor="w",
                fg_color=bg_color,
                text_color=text_color,
                corner_radius=5,
                padx=10,
                pady=4,
            )
            label.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            label.bind("<Button-1>", lambda e, idx=i: self.select_task(idx))
            self.task_widgets.append(frame)

    def select_task(self, index):
        self.selected_index = index
        task = self.tasks[index]
        self.task_name_entry.delete(0, "end")
        self.task_name_entry.insert(0, task.name)
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(task.duration))
        self.status_label.configure(text=f"Editing task {index + 1}")
        self.refresh_task_list()

    def move_task_up(self):
        if self.selected_index is not None and self.selected_index > 0:
            self.tasks[self.selected_index], self.tasks[self.selected_index - 1] = (
                self.tasks[self.selected_index - 1],
                self.tasks[self.selected_index],
            )
            self.selected_index -= 1
            self.refresh_task_list()

    def move_task_down(self):
        if (
            self.selected_index is not None
            and self.selected_index < len(self.tasks) - 1
        ):
            self.tasks[self.selected_index], self.tasks[self.selected_index + 1] = (
                self.tasks[self.selected_index + 1],
                self.tasks[self.selected_index],
            )
            self.selected_index += 1
            self.refresh_task_list()

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump([t.to_dict() for t in self.tasks], f)
        self.status_label.configure(text="Tasks saved")

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(d) for d in data]
                self.refresh_task_list()
                self.status_label.configure(text="Tasks loaded")
        except FileNotFoundError:
            self.status_label.configure(text="No saved tasks found")

    def start_rotation(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.main_frame.pack_forget()
            self.rotation_frame.pack(fill="both", expand=True, padx=0, pady=0)
            self.rotation_thread = threading.Thread(
                target=self.run_rotation, daemon=True
            )
            self.rotation_thread.start()
        elif self.paused:
            self.paused = False
            self.main_frame.pack_forget()
            self.rotation_frame.pack(fill="both", expand=True, padx=0, pady=0)

    def pause_rotation(self):
        if not self.paused:
            self.paused = True
            self.rotation_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

    def stop_rotation(self):
        self.running = False
        self.paused = False
        self.current_task_index = 0

    def safe_ui_update(self, text):
        self.after(0, lambda: self.rotation_label.configure(text=text))

    def run_rotation(self):
        while self.running and self.current_task_index < len(self.tasks):
            task = self.tasks[self.current_task_index]
            self.safe_ui_update(f"Working on: {task.name}")
            remaining = task.duration * 60
            while remaining > 0 and self.running:
                if self.paused:
                    time.sleep(1)
                    continue
                mins, secs = divmod(remaining, 60)
                self.safe_ui_update(f"{task.name} - {mins}:{secs:02d} left")
                time.sleep(1)
                remaining -= 1
            if not self.running:
                break
            self.current_task_index += 1
        if self.running:
            self.safe_ui_update("All tasks completed")
        self.running = False
        self.paused = False
        self.current_task_index = 0


if __name__ == "__main__":
    app = TaskApp()
    app.mainloop()
