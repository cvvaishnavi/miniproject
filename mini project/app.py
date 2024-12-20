from flask import Flask, request, jsonify, render_template
import os
import pyttsx3
import pywhatkit as kit
from datetime import datetime, timedelta
from plyer import notification
import threading
import time
import re
import winsound  # For playing a sound on Windows
import tkinter as tk

app = Flask(__name__)

def speak(text):
    """Convert text to speech with a new engine instance."""
    try:
        local_engine = pyttsx3.init()  # Create a new engine instance
        local_engine.setProperty("rate", 150)
        local_engine.say(text)
        local_engine.runAndWait()
        local_engine.stop()  # Stop the engine to release resources
    except Exception as e:
        print(f"Error in speak: {e}")

@app.route('/')
def index():
    """Serve the frontend."""
    return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    """Handle commands from the frontend."""
    data = request.json
    command = data.get("command", "").lower()

    if not command:
        return jsonify({"message": "No command received."}), 400

    # Process the command
    if "play song" in command or "play video" in command:
        song = command.replace("play song", "").replace("play video", "").strip()
        response = f"Playing {song} on YouTube."
        speak(f"Playing {song} on YouTube.")
        try:
            kit.playonyt(song)
        except Exception as e:
            response = f"Could not play the song. Error: {str(e)}"
        return jsonify({"message": response})

    elif "set alarm" in command:
        alarm_time = command.replace("set alarm", "").strip()
        try:
            threading.Thread(target=set_alarm, args=(alarm_time,)).start()
            return jsonify({"message": f"Alarm set for {alarm_time}."})
        except ValueError:
            return jsonify({"message": "Invalid alarm format. Use HH:MM."})

    elif "set timer" in command or "timer" in command:
        # Extract the timer duration
        match = re.search(r'(\d+)', command)
        if match:
            timer_duration = int(match.group(1))  # Extract first number from the command
            threading.Thread(target=set_timer_with_countdown, args=(timer_duration,)).start()
            return jsonify({"message": f"Timer set for {timer_duration} seconds."})
        else:
            return jsonify({"message": "No valid duration found for the timer. Please specify in seconds."})

    elif "shut down" in command or "shutdown" in command:
        threading.Thread(target=shutdown_laptop).start()
        return jsonify({"message": "Shutting down the laptop."})

    elif "exit" in command or "stop veera" in command:
        speak("Bye until next time")
        return jsonify({"message": "Goodbye!"})

    else:
        return jsonify({"message": "I didn't understand that. Can you try again?"})

def set_alarm(alarm_time):
    """Sets an alarm for the given time in HH:MM format."""
    try:
        # Clean up and extract time
        alarm_time = alarm_time.strip()
        print(f"Original input for alarm time: '{alarm_time}'")

        match = re.search(r'\b(\d{1,2}:\d{2})\b', alarm_time)
        if not match:
            raise ValueError("Invalid time format. Please use HH:MM format.")

        alarm_time = match.group(1)
        print(f"Extracted time: '{alarm_time}'")

        alarm_hour, alarm_minute = map(int, alarm_time.split(":"))
        if not (0 <= alarm_hour < 24) or not (0 <= alarm_minute < 60):
            raise ValueError("Invalid time. Hours must be 0-23 and minutes 0-59.")

        speak(f"Setting an alarm for {alarm_hour:02d}:{alarm_minute:02d}.")
        print(f"Alarm set for {alarm_hour:02d}:{alarm_minute:02d}")

        # Use datetime for precise timing
        now = datetime.now()
        alarm_datetime = now.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
        if alarm_datetime <= now:
            # If the alarm time is earlier today, set it for tomorrow
            alarm_datetime += timedelta(days=1)

        print(f"Alarm scheduled for: {alarm_datetime}")

        # Wait until the alarm time
        while True:
            now = datetime.now()
            time_difference = (alarm_datetime - now).total_seconds()

            if time_difference <= 0:  # Trigger the alarm
                notification.notify(
                    title="Alarm Notification",
                    message="Time to wake up!",
                    app_name="Voice Assistant",
                    timeout=10
                )
                speak("Your alarm is here! ")
                winsound.Beep(440, 3000)  
                print("Alarm Triggered at:", now.strftime("%H:%M:%S"))
                break
            elif time_difference < 60:
                time.sleep(1)  # Check every second in the last minute
            else:
                time.sleep(10)  # Sleep in 10-second intervals during the wait
    except ValueError as ve:
        speak(str(ve))
        print("Error:", ve)
    except Exception as e:
        speak(f"An unexpected error occurred: {str(e)}")
        print("Error in set_alarm:", e)

def set_timer_with_countdown(seconds):
    """Sets a timer with a countdown displayed on the desktop."""
    def show_countdown():
        root = tk.Tk()
        root.title("Countdown Timer")
        label = tk.Label(root, font=("Helvetica", 48), text="")
        label.pack(pady=20)

        for remaining in range(seconds, -1, -1):
            mins, secs = divmod(remaining, 60)
            timer_text = f"{mins:02d}:{secs:02d}"
            label.config(text=timer_text)
            root.update()
            time.sleep(1)

        root.destroy()

    try:
        speak(f"Setting a timer for {seconds} seconds.")
        countdown_thread = threading.Thread(target=show_countdown)
        countdown_thread.start()
        countdown_thread.join()
        notification.notify(
            title="Timer Notification",
            message="Your timer has ended.",
            app_name="Voice Assistant",
            timeout=10
        )
        winsound.Beep(440, 3000)  
        speak("Time's up!")
    except ValueError:
        speak("Invalid input. Please provide a number for the timer.")
    except Exception as e:
        speak(f"An error occurred: {str(e)}")

def shutdown_laptop():
    """Shut down the laptop."""
    speak("Shutting down the laptop. Goodbye!")
    os.system("shutdown /s /t 1")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
