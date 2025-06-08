import asyncio
import json
import flet as ft
from flet import Icons

class Task:
    def __init__(self, name: str, duration: int):
        self.name = name
        self.duration = duration

    def to_dict(self):
        return {"name": self.name, "duration": self.duration}

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(data["name"], data["duration"])


async def main(page: ft.Page):
    page.title = "Focus Flow"
    tasks: list[Task] = []
    selected_index: int | None = None
    running = False
    paused = False
    current_task_index = 0
    rotation_job: asyncio.Task | None = None

    task_name = ft.TextField(label="Task Name", expand=True)
    task_duration = ft.TextField(label="Duration (min)", width=150)
    status = ft.Text()
    tasks_column = ft.ListView(expand=True, spacing=2)

    timer_label = ft.Text(size=36, weight="bold")
    main_view = ft.Column(
        [
            task_name,
            task_duration,
            ft.Row(
                [
                    ft.IconButton(Icons.CHECK, on_click=lambda e: save_task()),
                    ft.IconButton(Icons.ADD, on_click=lambda e: prepare_new()),
                    ft.IconButton(Icons.ARROW_UPWARD, on_click=lambda e: move_up()),
                    ft.IconButton(Icons.ARROW_DOWNWARD, on_click=lambda e: move_down()),
                    ft.IconButton(Icons.DELETE, on_click=lambda e: delete_task()),
                ]
            ),
            ft.Container(
                tasks_column,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                expand=True,
                scroll=ft.ScrollMode.ALWAYS,
                padding=5,
                border_radius=5,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Row(
                [
                    ft.IconButton(Icons.PLAY_ARROW, on_click=lambda e: start_rotation()),
                    ft.IconButton(Icons.STOP, on_click=lambda e: stop_rotation()),
                    ft.IconButton(Icons.SAVE, on_click=lambda e: save_tasks()),
                    ft.IconButton(Icons.DOWNLOAD, on_click=lambda e: load_tasks()),
                ]
            ),
            status,
        ],
        expand=True,
    )
    rotation_view = ft.Column([
        timer_label,
        ft.IconButton(Icons.PAUSE, on_click=lambda e: pause_rotation()),
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)

    page.add(ft.Stack([main_view, rotation_view]))
    rotation_view.visible = False

    def refresh_tasks():
        tasks_column.controls.clear()
        for i, t in enumerate(tasks):
            selected = i == selected_index
            tile = ft.ListTile(
                title=ft.Text(f"{t.name} - {t.duration} min"),
                selected=selected,
                on_click=lambda e, idx=i: select_task(idx),
            )
            tasks_column.controls.append(tile)
        page.update()

    def select_task(index: int):
        nonlocal selected_index
        selected_index = index
        t = tasks[index]
        task_name.value = t.name
        task_duration.value = str(t.duration)
        status.value = f"Editing task {index + 1}"
        refresh_tasks()

    def prepare_new():
        nonlocal selected_index
        selected_index = None
        task_name.value = ""
        task_duration.value = ""
        status.value = "Creating new task"
        page.update()

    def save_task():
        nonlocal selected_index
        name = task_name.value.strip()
        try:
            duration = int(task_duration.value)
        except ValueError:
            status.value = "Duration must be a number"
            page.update()
            return
        if selected_index is not None:
            tasks[selected_index] = Task(name, duration)
            status.value = "Task updated"
        else:
            tasks.append(Task(name, duration))
            status.value = "New task added"
        refresh_tasks()

    def delete_task():
        nonlocal selected_index
        if selected_index is not None:
            tasks.pop(selected_index)
            selected_index = None
            refresh_tasks()
            status.value = "Task deleted"
            page.update()

    def move_up():
        nonlocal selected_index
        if selected_index is not None and selected_index > 0:
            tasks[selected_index - 1], tasks[selected_index] = tasks[selected_index], tasks[selected_index - 1]
            selected_index -= 1
            refresh_tasks()

    def move_down():
        nonlocal selected_index
        if selected_index is not None and selected_index < len(tasks) - 1:
            tasks[selected_index], tasks[selected_index + 1] = tasks[selected_index + 1], tasks[selected_index]
            selected_index += 1
            refresh_tasks()

    def save_tasks():
        with open("tasks.json", "w") as f:
            json.dump([t.to_dict() for t in tasks], f)
        status.value = "Tasks saved"
        page.update()

    def load_tasks():
        nonlocal tasks, selected_index
        try:
            with open("tasks.json", "r") as f:
                tasks = [Task.from_dict(d) for d in json.load(f)]
            selected_index = None
            refresh_tasks()
            status.value = "Tasks loaded"
        except FileNotFoundError:
            status.value = "No saved tasks found"
        page.update()

    async def run_rotation():
        nonlocal running, paused, current_task_index, rotation_job
        while running and current_task_index < len(tasks):
            t = tasks[current_task_index]
            timer_label.value = f"Working on: {t.name}"
            page.update()
            remaining = t.duration * 60
            while remaining > 0 and running:
                if paused:
                    await asyncio.sleep(1)
                    continue
                m, s = divmod(remaining, 60)
                timer_label.value = f"{t.name} - {m}:{s:02d} left"
                page.update()
                await asyncio.sleep(1)
                remaining -= 1
            if not running:
                break
            current_task_index += 1
        if running:
            timer_label.value = "All tasks completed"
            page.update()
        running = False
        paused = False
        current_task_index = 0
        rotation_job = None
        main_view.visible = True
        rotation_view.visible = False
        page.update()

    def start_rotation():
        nonlocal running, paused, rotation_job
        if not running:
            running = True
            paused = False
            main_view.visible = False
            rotation_view.visible = True
            page.update()
            rotation_job = page.run_task(run_rotation)
        elif paused:
            paused = False
            main_view.visible = False
            rotation_view.visible = True
            page.update()

    def pause_rotation():
        nonlocal paused
        if not paused:
            paused = True
            main_view.visible = True
            rotation_view.visible = False
            page.update()

    def stop_rotation():
        nonlocal running, paused, current_task_index, rotation_job
        running = False
        paused = False
        current_task_index = 0
        if rotation_job:
            rotation_job.cancel()
            rotation_job = None

    refresh_tasks()

ft.app(target=main)
