# Fitts' Law Experiment Application
# This application is designed to conduct an experiment based on Fitts' Law, measuring the efficiency of users in pointing and clicking targets on a screen.

import tkinter as tk
from tkinter import messagebox  # Used for providing feedback to the user
import random  # Necessary for shuffling the trial order
import time  # Used for timing the trials
import csv  # For recording trial data to a CSV file
from itertools import product  # For generating combinations of trial configurations
import pyautogui  # For moving the cursor automatically
from datetime import datetime
# Define the constants and configurations for the experiment
MAX_TRIALS_PER_CONFIG = 10
trial_counter = 0  # Keeps track of the number of trials conducted
trial_data = []  # Stores the data for each trial
current_trial = {}  # Holds the data for the current trial

# Define the possible properties for the target circles
circle_sizes = [10, 20, 30, 40]
circle_distances = [100, 200, 300, 400]
circle_directions = ['left', 'right']
trial_configurations = list(product(circle_sizes, circle_distances, circle_directions))
random.shuffle(trial_configurations)  # Ensure trials are presented in a random order

# Function to determine if the user's click was inside the target circle
def is_inside_circle(circle_center, circle_radius, click_point):
    # Calculate the Euclidean distance from the click point to the circle's center
    distance = ((click_point[0] - circle_center[0])**2 + (click_point[1] - circle_center[1])**2)**0.5
    return distance <= circle_radius  # Return True if the click was inside the circle

# Event handler for mouse clicks during the experiment
def handle_click(event):
    global current_trial, trial_counter
    click_position = (event.x, event.y)
    
    # Calculate the distance from the click position to the circle's center
    distance = ((click_position[0] - current_trial['circle_center'][0])**2 + (click_position[1] - current_trial['circle_center'][1])**2)**0.5
    current_trial['distance'] = distance  # Record the distance for the current trial
    
    # Check if the click was successful (inside the circle)
    if is_inside_circle(current_trial['circle_center'], current_trial['circle_radius'], click_position):
        # Click was successful
        current_trial['time_taken'] = time.time() - current_trial['start_time']  # Record the time taken for the trial
        current_trial['success'] = True
        trial_data.append(current_trial)  # Add the current trial's data to the overall trial data
        canvas.delete("all")  # Prepare the canvas for the next trial
        messagebox.showinfo("Success", "Well done! Click OK for the next trial.")  # Provide positive feedback
        if trial_counter < len(trial_configurations) * MAX_TRIALS_PER_CONFIG:
            start_trial()  # Initiate the next trial
        else:
            end_experiment()  # If all trials are completed, end the experiment
    else:
        # Click was unsuccessful
        current_trial['errors'] += 1  # Increment the error count for the current trial
        messagebox.showwarning("Missed", "Oops! You missed. Try again.")  # Provide feedback about the miss

# Function to start a new trial
def start_trial():
    global current_trial, trial_counter
    canvas.delete("all")  # Clear the canvas for the new trial

    # Update the root window to ensure the canvas size is set
    root.update_idletasks()
    root.update()

    # Randomly select a circle size
    circle_radius = random.choice(circle_sizes)

    # Randomly position the circle within the canvas boundaries, ensuring it's fully visible
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    circle_x = random.randint(circle_radius, canvas_width - circle_radius)
    circle_y = random.randint(circle_radius, canvas_height - circle_radius)

    # Draw the circle on the canvas at the new position
    canvas.create_oval(circle_x - circle_radius, circle_y - circle_radius, circle_x + circle_radius, circle_y + circle_radius, fill='blue')

    # Initialize the data for the current trial
    current_trial = {
        'circle_radius': circle_radius,
        'circle_center': (circle_x, circle_y),
        'start_time': time.time(),
        'errors': 0,
        'success': False,
        'direction': 'random'
    }

    trial_counter += 1  # Increment the trial counter

    # Move the cursor to the center of the screen using pyautogui (if installed and imported)
    screen_width, screen_height = pyautogui.size()  # Get the size of the screen
    center_x, center_y = screen_width / 2, screen_height / 2
    pyautogui.moveTo(center_x, center_y)



# Function to save trial data to a CSV file
import csv
from datetime import datetime
import os

# Function to save trial data to a CSV file, appending to the same file for each experiment
def save_data():
    # Define the filename for the CSV
    filename = os.path.join(os.path.expanduser('~'), 'Desktop', 'fitts_law_experiment_data.csv')

    # Check if the file exists to decide whether to write headers
    file_exists = os.path.isfile(filename)

    # Define the fieldnames for the CSV
    fieldnames = [
        'trial',
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

    # Open the file in append mode
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header only if the file did not exist
        if not file_exists:
            writer.writeheader()
        
        # Write each row of trial data
        for i, data in enumerate(trial_data):
            # Prepare data for writing
            row = {
                'trial': i + 1,
                **data,
                'circle_center_x': data['circle_center'][0],
                'circle_center_y': data['circle_center'][1]
            }
            # Remove keys not in fieldnames
            row = {key: row[key] for key in fieldnames}
            writer.writerow(row)

    print(f"Data appended to {filename}")  # Print confirmation message

def end_experiment():
    save_data()  # Save the data collected so far
    show_results()  # Show the results screen

# Function to display the results and end the experiment
def show_results():
    results_window = tk.Tk()
    results_window.title("Experiment Completed")
    # Display completion message
    results_text = "The experiment is complete. Thank you for your participation!"
    results_label = tk.Label(results_window, text=results_text)
    results_label.pack()
    # Close button to exit the results window
    close_button = tk.Button(results_window, text="Close", command=results_window.destroy)
    close_button.pack()
    results_window.mainloop()

# Function to abort the experiment and close the application immediately
def abort_experiment():
    save_data()  # Optional: Save the data collected so far before exiting
    root.quit()  # This will close the Tkinter window and exit the application
    root.destroy()  # Ensures that the application is terminated

# Function to show the welcome screen with the informed consent
def show_welcome_screen():
    welcome_screen = tk.Tk()
    welcome_screen.title("Welcome to the Fitts' Law Experiment")
    # Display the informed consent text
    consent_text =  """
    INFORMED CONSENT DOCUMENT
    Please read the following informed consent document. If you consent to the study, click 'I Agree'.
    If you do not consent and would like to cancel your participation in the study, click 'Cancel'.
    
    Project Title: CIS-482/582 HCI – Fitts’ Law study

    Thank you for agreeing to participate in this research study! This document provides important
    information about what you will be asked to do during the research study, about the risks and benefits
    of the study, and about your rights as a research subject. If you have any questions about or do not
    understand something in this document, you should ask questions to the members of the research team
    listed above. Do not agree to participate in this research study unless the research team has answered
    your questions and you decide that you want to be part of this study.
    
    By clicking 'I Agree', you hereby acknowledge that you are at least 18 years of age. You also indicate that you agree to the following statement:
    “I have read this consent form and I understand the risks, benefits, and procedures involved with
    participation in this research study. I hereby agree to participate in this research study.”
    """
    consent_label = tk.Label(welcome_screen, text=consent_text, wraplength=600, justify="left")
    consent_label.pack(padx=10, pady=10)

    # Function to handle agreement to participate
    def on_agree():
        # Log the consent
        with open("consent_log.txt", "a") as file:
            file.write(f"Consent given at {time.asctime(time.localtime())}\n")
        welcome_screen.destroy()
        start_experiment()  # Start the main experiment

    # Function to handle cancellation of participation
    def on_cancel():
        welcome_screen.destroy()
        messagebox.showinfo("Cancelled", "You have cancelled your participation. Thank you.")

    # Buttons for agreeing or cancelling participation
    agree_button = tk.Button(welcome_screen, text="I Agree", command=on_agree)
    agree_button.pack(side=tk.LEFT, padx=20, pady=20)
    cancel_button = tk.Button(welcome_screen, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, padx=20, pady=20)
    welcome_screen.mainloop()

# Function to start the main experiment
def start_experiment():
    global root, canvas
    root = tk.Tk()
    root.title("Fitts' Law Experiment")
    root.attributes('-fullscreen', True)
    # Set up the canvas for drawing circles
    canvas = tk.Canvas(root, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.bind("<Button-1>", handle_click)  # Bind mouse click event to handle_click function

    root.attributes('-fullscreen', True)

    def exit_fullscreen(event=None):
        root.attributes('-fullscreen', False)

    root.bind('<Escape>', exit_fullscreen)

    start_button = tk.Button(root, text="Start Experiment", command=start_trial)
    start_button.pack()

    abort_button = tk.Button(root, text="Abort Experiment", command=abort_experiment)
    abort_button.pack()
    root.mainloop()

# Start the application by showing the welcome screen
show_welcome_screen()
