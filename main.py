import sys
print("ready")
sys.stdout.flush()

import time, threading, datetime, os, json, traceback

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

from gamestatetooutput import gamestate_to_output

logs_path = os.path.join(dir_path, "logs")
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

def main(app):
    app.print("Automaton started")
    while True:
        try:
            game_state = sys.stdin.readline().strip()
            
            s = f"{game_state}\n\n\n\n\n\n"
            app.print("got game state")
            jsonified = json.loads(game_state.replace(",\n        ...", ""))
            if "error" not in jsonified:
                app.last_game_state = game_state
            else:
                app.print("game state contains error")

            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
            with open(os.path.join(logs_path, filename), "w") as f:
                json.dump(json.loads(game_state), f, indent=4)
        
        except Exception as e:
            s = f"An error occurred: {e}\n\n\n\n\n\n"
            with open(os.path.join(dir_path, "log_com_mod.txt"), "a") as f:
                f.write(s)
            app.debug_print(s)
            break


import tkinter as tk
from tkinter import scrolledtext, ttk

class SlayTheSpireModUI:
    def __init__(self, master):
        self.master = master
        master.title("Automaton")
        master.geometry("1200x800")
        master.configure(bg='#2b2b2b')

        self.messages = []
        self.last_game_state = None
        self.queued_commands = []

        self.create_widgets()

    def create_widgets(self):
        # Status Title
        self.status_label = tk.Label(self.master, text="Status: Idle", font=("Arial", 16, "bold"), bg='#2b2b2b', fg='white')
        self.status_label.pack(pady=10)

        # Main frame for text areas
        main_frame = tk.Frame(self.master, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Main Text Area
        self.main_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=30, bg='#1e1e1e', fg='white')
        self.main_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Debug Text Area
        self.debug_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=40, height=30, bg='#1e1e1e', fg='#00ff00')
        self.debug_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Control Frame
        control_frame = tk.Frame(self.master, bg='#2b2b2b')
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Do Action Button
        self.do_action_button = tk.Button(control_frame, text="Do Action", command=self.do_action)
        self.do_action_button.pack(side=tk.LEFT, padx=(0, 10))

        # Auto Do Action Checkbox
        self.auto_do_action_var = tk.BooleanVar()
        self.auto_do_action_check = tk.Checkbutton(control_frame, text="Auto Do Action", variable=self.auto_do_action_var, bg='#2b2b2b', fg='white', selectcolor='#1e1e1e')
        self.auto_do_action_check.pack(side=tk.LEFT, padx=(0, 20))

        # Start/Stop Button
        self.start_stop_button = tk.Button(control_frame, text="Start", command=self.toggle_start_stop)
        self.start_stop_button.pack(side=tk.LEFT, padx=(0, 10))

        # Auto Generate Checkbox
        self.auto_generate_var = tk.BooleanVar()
        self.auto_generate_check = tk.Checkbutton(control_frame, text="Auto Generate", variable=self.auto_generate_var, bg='#2b2b2b', fg='white', selectcolor='#1e1e1e')
        self.auto_generate_check.pack(side=tk.LEFT)

    def print(self, *text):
        self.main_text.insert(tk.END, " ".join([str(x) for x in text]) + '\n')
        self.main_text.see(tk.END)

    def debug_print(self, *text):
        self.debug_text.insert(tk.END, " ".join([str(x) for x in text]) + '\n')
        self.debug_text.see(tk.END)

    def set_status(self, status):
        self.status_label.config(text=f"Status: {status}")

    def do_action(self):
        for command in self.queued_commands:
            self.master.update()
            self.print("Performing action: " + command)
            print(command)
            sys.stdout.flush()
            time.sleep(1)
            
        if self.auto_generate_var.get():
            time.sleep(1)
            if self.is_in_combat():
                time.sleep(1.5)
            self.toggle_start_stop()
        
        self.queued_commands = []

    def toggle_start_stop(self):
        if self.last_game_state is None:
            self.debug_print("last game state is none")
            return
        
        if self.start_stop_button.cget('text') == 'Stop':
            self.debug_print("Not finished generating. Can't stop.")
            return
        
        self.start_stop_button.config(text='Stop')
        self.set_status("Generating...")

        try:
            commands, self.is_in_combat = gamestate_to_output(self.last_game_state, self.print, self.debug_print, self.messages)
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.debug_print(f"An error occurred in the gamestate_to_output func: {e}\nFull stack trace:\n{stack_trace}")
            commands = []

        self.start_stop_button.config(text='Start')
        self.set_status("Idle")

        self.last_game_state = None
        self.queued_commands = commands
        self.print("Actions:", commands)

        if self.auto_do_action_var.get():
            self.do_action()

if __name__ == "__main__":
    root = tk.Tk()
    app = SlayTheSpireModUI(root)
    threading.Thread(target=main, args=(app,)).start()
    root.mainloop()