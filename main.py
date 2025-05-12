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
        return Task(data['name'], data['duration'])

class TaskApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Focus Flow")
        self.geometry("500x850")

        self.tasks = []
        self.task_widgets = []
        self.rotation_thread = None
        self.running = False
        self.paused = False
        self.current_task_index = 0
        self.selected_index = None

        self.name_label = ctk.CTkLabel(self, text="Task Name:")
        self.name_label.pack(anchor="w", padx=10)
        self.task_name_entry = ctk.CTkEntry(self)
        self.task_name_entry.pack(fill="x", padx=10, pady=5)

        self.duration_label = ctk.CTkLabel(self, text="Duration (min):")
        self.duration_label.pack(anchor="w", padx=10)
        self.duration_entry = ctk.CTkEntry(self)
        self.duration_entry.pack(fill="x", padx=10, pady=5)

        self.save_task_button = ctk.CTkButton(self, text="Save Task", command=self.save_task)
        self.save_task_button.pack(pady=5)

        self.new_task_button = ctk.CTkButton(self, text="Add New Task", command=self.prepare_new_task)
        self.new_task_button.pack(pady=5)

        self.move_up_button = ctk.CTkButton(self, text="Move Up", command=self.move_task_up)
        self.move_up_button.pack(pady=5)

        self.move_down_button = ctk.CTkButton(self, text="Move Down", command=self.move_task_down)
        self.move_down_button.pack(pady=5)

        self.delete_button = ctk.CTkButton(self, text="Delete Task", command=self.delete_task)
        self.delete_button.pack(pady=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=250)
        self.scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.start_button = ctk.CTkButton(self, text="Start Rotation", command=self.toggle_rotation)
        self.start_button.pack(pady=5)

        self.stop_button = ctk.CTkButton(self, text="Stop Rotation", command=self.stop_rotation)
        self.stop_button.pack(pady=5)

        self.save_button = ctk.CTkButton(self, text="Save Tasks to File", command=self.save_tasks)
        self.save_button.pack(pady=5)

        self.load_button = ctk.CTkButton(self, text="Load Tasks from File", command=self.load_tasks)
        self.load_button.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="")
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
                pady=4
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
            self.tasks[self.selected_index], self.tasks[self.selected_index - 1] = self.tasks[self.selected_index - 1], self.tasks[self.selected_index]
            self.selected_index -= 1
            self.refresh_task_list()

    def move_task_down(self):
        if self.selected_index is not None and self.selected_index < len(self.tasks) - 1:
            self.tasks[self.selected_index], self.tasks[self.selected_index + 1] = self.tasks[self.selected_index + 1], self.tasks[self.selected_index]
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

    def toggle_rotation(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.start_button.configure(text="Pause Rotation")
            self.rotation_thread = threading.Thread(target=self.run_rotation, daemon=True)
            self.rotation_thread.start()
        elif not self.paused:
            self.paused = True
            self.start_button.configure(text="Resume Rotation")
            self.safe_ui_update("Rotation paused")
        else:
            self.paused = False
            self.start_button.configure(text="Pause Rotation")
            self.safe_ui_update("Rotation resumed")

    def stop_rotation(self):
        self.running = False
        self.paused = False
        self.current_task_index = 0
        self.start_button.configure(text="Start Rotation")
        self.safe_ui_update("Rotation stopped")

    def safe_ui_update(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def show_task_dialog(self, task):
        def _():
            dialog = ctk.CTkToplevel(self)
            dialog.geometry("400x200")
            dialog.title("Task Info")
            label = ctk.CTkLabel(dialog, text=f"{task.name}\nDuration: {task.duration} min", font=ctk.CTkFont(size=28, weight="bold"))
            label.pack(expand=True, fill="both", padx=20, pady=20)
        self.after(0, _)

    def run_rotation(self):
        while self.running and self.current_task_index < len(self.tasks):
            task = self.tasks[self.current_task_index]
            self.safe_ui_update(f"Working on: {task.name}")
            self.show_task_dialog(task)
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
        self.after(0, lambda: self.start_button.configure(text="Start Rotation"))

if __name__ == '__main__':
    app = TaskApp()
    app.mainloop()
