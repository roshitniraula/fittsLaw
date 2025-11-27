# Fitts' Law Experiment Application
# This application is designed to conduct an experiment based on Fitts' Law,
# measuring the efficiency of users in pointing and clicking targets on a screen.

import tkinter as tk
from tkinter import messagebox
import random
import time
import csv
from itertools import product
import pyautogui
from datetime import datetime
import os

# Optional sound on Windows
try:
    import winsound
except ImportError:
    winsound = None

# ================= Global config & state =================

MAX_TRIALS_PER_CONFIG = 10
trial_counter = 0          # number of successful trials completed
trial_data = []            # list of dicts, one per successful trial
current_trial = {}         # data for current trial (including errors)
participant_id = ""
counter_label = None       # label "X / TOTAL"

# circle parameters
circle_sizes = [10, 20, 30, 40]
circle_distances = [100, 200, 300, 400]
circle_directions = ['left', 'right']
trial_configurations = list(product(circle_sizes, circle_distances, circle_directions))
random.shuffle(trial_configurations)

TOTAL_TRIALS = len(trial_configurations) * MAX_TRIALS_PER_CONFIG  # 320


# ================= Helper functions =================

def is_inside_circle(circle_center, circle_radius, click_point):
    """Return True if click_point is inside the circle."""
    distance = ((click_point[0] - circle_center[0]) ** 2 +
                (click_point[1] - circle_center[1]) ** 2) ** 0.5
    return distance <= circle_radius


# ================= Main click handling =================

def handle_click(event):
    """Handles clicks on the canvas when a blue target circle is shown."""
    global current_trial, trial_counter

    if not current_trial:
        return  # safety

    click_position = (event.x, event.y)

    # Distance from center
    distance = ((click_position[0] - current_trial['circle_center'][0]) ** 2 +
                (click_position[1] - current_trial['circle_center'][1]) ** 2) ** 0.5
    current_trial['distance'] = distance

    # SUCCESS ----------------------------------------------------
    if is_inside_circle(current_trial['circle_center'],
                        current_trial['circle_radius'],
                        click_position):
        current_trial['time_taken'] = time.time() - current_trial['start_time']
        current_trial['success'] = True

        # record this completed trial (includes errors)
        trial_data.append(current_trial)
        trial_counter += 1

        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2 - 120,
            text="Well done! Click the yellow circle to continue.",
            fill="black",
            font=("Arial", 24)
        )

        # if this was the last trial, yellow button will end experiment
        if trial_counter >= TOTAL_TRIALS:
            show_yellow_continue_button(callback=end_experiment)
        else:
            show_yellow_continue_button(callback=start_trial)

    # ERROR ------------------------------------------------------
    else:
        current_trial['errors'] += 1

        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2 - 120,
            text="Error. Try again. Click the yellow circle.",
            fill="red",
            font=("Arial", 24)
        )

        # yellow button will re-show the SAME circle
        show_yellow_continue_button(callback=repeat_same_trial)


def show_yellow_continue_button(callback):
    """
    Draw a yellow circle in the center.
    When clicked, it calls `callback()` (either start_trial, repeat_same_trial, or end_experiment).
    """
    center_x = canvas.winfo_width() // 2
    center_y = canvas.winfo_height() // 2
    radius = 40

    # Disable normal click handling while the yellow circle is active
    canvas.unbind("<Button-1>")

    # Draw the yellow circle
    canvas.create_oval(
        center_x - radius, center_y - radius,
        center_x + radius, center_y + radius,
        fill="yellow", outline="black", width=3,
        tags="yellow_next"
    )

    def yellow_click(event):
        dist = ((event.x - center_x) ** 2 + (event.y - center_y) ** 2) ** 0.5
        if dist <= radius:
            canvas.delete("yellow_next")
            canvas.unbind("<Button-1>")
            # Restore normal click handler for future blue circles
            canvas.bind("<Button-1>", handle_click)
            # Perform the chosen action
            callback()

    canvas.bind("<Button-1>", yellow_click)


def repeat_same_trial():
    """Redraws the SAME blue circle and restarts timing, preserving error count."""
    canvas.delete("all")

    circle_x, circle_y = current_trial['circle_center']
    radius = current_trial['circle_radius']

    canvas.create_oval(
        circle_x - radius, circle_y - radius,
        circle_x + radius, circle_y + radius,
        fill='blue'
    )

    current_trial['start_time'] = time.time()


# ================= Trial creation =================

def start_trial():
    """Starts a NEW trial with a new blue circle (only called after a success)."""
    global current_trial

    if trial_counter >= TOTAL_TRIALS:
        end_experiment()
        return

    canvas.delete("all")

    # update counter label: show "next trial number / TOTAL"
    if counter_label is not None:
        counter_label.config(text=f"{trial_counter + 1} / {TOTAL_TRIALS}")

    root.update_idletasks()
    root.update()

    # choose random circle size & random position
    circle_radius = random.choice(circle_sizes)
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    circle_x = random.randint(circle_radius, canvas_width - circle_radius)
    circle_y = random.randint(circle_radius, canvas_height - circle_radius)

    # draw blue target
    canvas.create_oval(
        circle_x - circle_radius, circle_y - circle_radius,
        circle_x + circle_radius, circle_y + circle_radius,
        fill='blue'
    )

    # initialize current trial record
    current_trial = {
        'circle_radius': circle_radius,
        'circle_center': (circle_x, circle_y),
        'start_time': time.time(),
        'errors': 0,
        'success': False,
        'direction': 'random',
        'participant': participant_id
    }

    # move mouse to center of screen
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width / 2, screen_height / 2
    pyautogui.moveTo(center_x, center_y)


# ================= Data & summary =================

def save_data():
    """Save all completed trials to CSV."""
    filename = os.path.join(os.path.expanduser('~'),
                            'Documents',
                            'fitts_law_experiment_data.csv')

    file_exists = os.path.isfile(filename)

    fieldnames = [
        'trial',
        'participant',
        'circle_radius',
        'circle_center_x',
        'circle_center_y',
        'time_taken',
        'distance',
        'errors',
        'direction',
        'success',
        'start_time'
    ]

    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for i, data in enumerate(trial_data):
            row = {
                'trial': i + 1,
                'participant': data['participant'],
                **data,
                'circle_center_x': int(data['circle_center'][0]),
                'circle_center_y': int(data['circle_center'][1])
            }
            row = {key: row[key] for key in fieldnames}
            writer.writerow(row)

    print(f"Data appended to {filename}")


def calculate_summary():
    if not trial_data:
        return {"avg_time": 0, "avg_errors": 0, "success_rate": 0}

    total_time = 0
    total_errors = 0
    successes = 0

    for t in trial_data:
        if t["success"]:
            total_time += t["time_taken"]
            successes += 1
        total_errors += t["errors"]

    avg_time = total_time / successes if successes > 0 else 0
    avg_errors = total_errors / len(trial_data)
    success_rate = (successes / len(trial_data)) * 100

    return {
        "avg_time": avg_time,
        "avg_errors": avg_errors,
        "success_rate": success_rate
    }


def play_completion_sound():
    if winsound is not None:
        try:
            winsound.PlaySound("SystemAsterisk",
                               winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass


def show_final_message():
    """Animated final screen with summary, participant ID, confetti, sound, and close button."""
    canvas.delete("all")
    canvas.unbind("<Button-1>")
    root.update_idletasks()

    width = canvas.winfo_width()
    height = canvas.winfo_height()

    # Dim background
    canvas.create_rectangle(
        0, 0, width, height,
        fill="black",
        stipple="gray50",
        outline="",
        tags="dim"
    )

    summary = calculate_summary()
    display_participant = participant_id if participant_id else "N/A"

    lines = [
        "🎉 You Did It! 🎉",
        f"Participant: {display_participant}",
        f"Trials completed: {trial_counter} / {TOTAL_TRIALS}",
        f"Average click time (successes): {summary['avg_time']:.3f} s",
        f"Average errors per trial: {summary['avg_errors']:.2f}",
        f"Success rate: {summary['success_rate']:.1f}%",
        "",
        "Thank you for completing all trials!"
    ]

    y_start = height // 2 - len(lines) * 15
    typing_delay = 50  # ms

    text_ids = []
    for i in range(len(lines)):
        tid = canvas.create_text(
            width // 2,
            y_start + i * 35,
            text="",
            fill="white",
            font=("Arial", 24),
            justify="center"
        )
        text_ids.append(tid)

    def start_confetti():
        confetti_items = []
        colors = ["red", "yellow", "blue", "green", "magenta", "cyan", "orange"]

        for _ in range(80):
            x = random.randint(0, width)
            y = random.randint(-height, 0)
            size = random.randint(4, 8)
            color = random.choice(colors)
            cid = canvas.create_oval(x, y, x + size, y + size,
                                     fill=color, outline="")
            speed = random.uniform(2, 6)
            confetti_items.append((cid, speed))

        def animate():
            for cid, speed in confetti_items:
                canvas.move(cid, 0, speed)
                x1, y1, x2, y2 = canvas.coords(cid)
                if y1 > height:
                    new_x = random.randint(0, width)
                    dy = -height - random.randint(0, height)
                    canvas.coords(cid, new_x, dy,
                                  new_x + (x2 - x1),
                                  dy + (y2 - y1))
            canvas.after(50, animate)

        animate()

    def show_close_button():
        btn = tk.Button(root, text="Close",
                        font=("Arial", 16), command=root.destroy)
        btn.place(relx=0.5, rely=0.9, anchor="center")

    def type_line(line_index, char_index=0):
        if line_index >= len(lines):
            start_confetti()
            play_completion_sound()
            show_close_button()
            return

        line = lines[line_index]
        if char_index <= len(line):
            canvas.itemconfig(text_ids[line_index],
                              text=line[:char_index])
            canvas.after(typing_delay,
                         lambda: type_line(line_index,
                                           char_index + 1))
        else:
            canvas.after(400,
                         lambda: type_line(line_index + 1, 0))

    type_line(0, 0)


def end_experiment():
    save_data()
    show_final_message()


# ================= UI & startup =================

def abort_experiment():
    save_data()
    root.quit()
    root.destroy()


def show_welcome_screen():
    welcome_screen = tk.Tk()
    welcome_screen.title("Welcome to the Fitts' Law Experiment")

    consent_text = """
    INFORMED CONSENT DOCUMENT
    Please read the following informed consent document. If you consent to the study, click 'I Agree'.
    If you do not consent and would like to cancel your participation in the study, click 'Cancel'.

    Project Title: CS470 HCI – Fitts’ Law study

    Thank you for agreeing to participate in this research study!
    """

    consent_label = tk.Label(welcome_screen, text=consent_text,
                             wraplength=600, justify="left")
    consent_label.pack(padx=10, pady=10)

    def on_agree():
        with open("consent_log.txt", "a") as file:
            file.write(f"Consent given at {time.asctime(time.localtime())}\n")
        welcome_screen.destroy()
        participant_entry_window()

    def on_cancel():
        welcome_screen.destroy()
        messagebox.showinfo("Cancelled",
                            "You have cancelled your participation. Thank you.")

    agree_button = tk.Button(welcome_screen, text="I Agree",
                             command=on_agree)
    agree_button.pack(side=tk.LEFT, padx=20, pady=20)
    cancel_button = tk.Button(welcome_screen, text="Cancel",
                              command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, padx=20, pady=20)

    welcome_screen.mainloop()


def participant_entry_window():
    global participant_id

    entry_window = tk.Tk()
    entry_window.title("Participant Information")

    label = tk.Label(entry_window,
                     text="Enter Participant ID (e.g., Person A):")
    label.pack(pady=10)

    entry = tk.Entry(entry_window)
    entry.pack(pady=5)

    def submit_id():
        global participant_id
        participant_id = entry.get().strip()
        if participant_id == "":
            messagebox.showerror("Error",
                                 "Participant ID cannot be empty.")
        else:
            entry_window.destroy()
            start_experiment()

    submit_btn = tk.Button(entry_window, text="Start Experiment",
                           command=submit_id)
    submit_btn.pack(pady=10)

    entry_window.mainloop()


def start_experiment():
    global root, canvas, counter_label

    root = tk.Tk()
    root.title("Fitts' Law Experiment")
    root.attributes('-fullscreen', True)

    canvas = tk.Canvas(root, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)

    counter_label = tk.Label(root,
                             text=f"0 / {TOTAL_TRIALS}",
                             font=("Arial", 20),
                             bg="white")
    counter_label.place(x=20, y=20)
    counter_label.lift()

    canvas.bind("<Button-1>", handle_click)

    def exit_fullscreen(event=None):
        root.attributes('-fullscreen', False)

    root.bind('<Escape>', exit_fullscreen)

    start_button = tk.Button(root, text="Start Experiment",
                             command=start_trial)
    start_button.pack()

    abort_button = tk.Button(root, text="Abort Experiment",
                             command=abort_experiment)
    abort_button.pack()

    root.mainloop()


# Start the application
show_welcome_screen()
