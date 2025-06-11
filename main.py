import tkinter as tk
from tkinter import ttk, scrolledtext
from utils import *
import datetime
import queue
import subprocess
import threading
import os
import time

# --- Setup root window ---
root = tk.Tk()
root.title("Dashboard Client")
root.geometry("1200x800")
root.configure(bg="#f4f4f4")

# --- Dynamic Variables ---
local_time = tk.StringVar()
timezone = tk.StringVar()
postfix_info = tk.StringVar()
cpu_usage = tk.StringVar()
memory_usage = tk.StringVar()
disk_usage = tk.StringVar()

# --- Queues for thread communication ---
system_log_queue = queue.Queue()
mail_log_queue = queue.Queue()

# --- Styles ---
style = ttk.Style()
style.configure("TLabel", font=("Arial", 12))
style.configure("TFrame", background="#f0f0f0")

# --- Main Frame ---
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(0, weight=1)
main_frame.rowconfigure(1, weight=2)
main_frame.rowconfigure(2, weight=3)

# --- Time Block ---
time_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
time_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(time_frame, text="⏰ Informations Temporelles", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

time_content = ttk.Frame(time_frame)
time_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(time_content, text="⏰ Heure locale :", style="TLabel").grid(row=0, column=0, sticky="w", pady=5)
ttk.Label(time_content, textvariable=local_time, style="TLabel").grid(row=0, column=1, sticky="w", pady=5)

ttk.Label(time_content, text="🌐 Fuseau Horaire :", style="TLabel").grid(row=1, column=0, sticky="w", pady=5)
ttk.Label(time_content, textvariable=timezone, style="TLabel").grid(row=1, column=1, sticky="w", pady=5)

# --- Mail Block ---
mail_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(mail_frame, text="📧 Informations Mail", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

mail_content = ttk.Frame(mail_frame)
mail_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(mail_content, text="📧 État de Postfix :", style="TLabel").grid(row=0, column=0, sticky="w", pady=5)
ttk.Label(mail_content, textvariable=postfix_info, style="TLabel").grid(row=0, column=1, sticky="w", pady=5)

# --- Resources Block ---
resources_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
resources_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

ttk.Label(resources_frame, text="💻 Ressources Système", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

resources_content = ttk.Frame(resources_frame)
resources_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(resources_content, text="💻 Utilisation CPU :", style="TLabel").grid(row=0, column=0, sticky="w", pady=5)
ttk.Label(resources_content, textvariable=cpu_usage, style="TLabel").grid(row=0, column=1, sticky="w", pady=5)

ttk.Label(resources_content, text="🧠 Utilisation Mémoire :", style="TLabel").grid(row=1, column=0, sticky="w", pady=5)
ttk.Label(resources_content, textvariable=memory_usage, style="TLabel").grid(row=1, column=1, sticky="w", pady=5)

ttk.Label(resources_content, text="💾 Utilisation Disque :", style="TLabel").grid(row=2, column=0, sticky="w", pady=5)
ttk.Label(resources_content, textvariable=disk_usage, style="TLabel").grid(row=2, column=1, sticky="w", pady=5)

# --- System Logs Block ---
system_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
system_logs_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(system_logs_frame, text="🔒 Logs Système (Auth)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

def clear_system_logs():
    system_logs.config(state=tk.NORMAL)
    system_logs.delete('1.0', tk.END)
    system_logs.config(state=tk.DISABLED)

sys_logs_buttons = ttk.Frame(system_logs_frame)
sys_logs_buttons.pack(fill="x", padx=10, pady=0)
ttk.Button(sys_logs_buttons, text="Vider les Logs", command=clear_system_logs).pack(side=tk.RIGHT)

system_logs = scrolledtext.ScrolledText(system_logs_frame, height=10, wrap=tk.WORD)
system_logs.pack(fill="both", expand=True, padx=10, pady=10)
system_logs.config(state=tk.DISABLED)

# --- Mail Logs Block ---
mail_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_logs_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(mail_logs_frame, text="📨 Logs Mail (Postfix)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

def clear_mail_logs():
    mail_logs.config(state=tk.NORMAL)
    mail_logs.delete('1.0', tk.END)
    mail_logs.config(state=tk.DISABLED)

mail_logs_buttons = ttk.Frame(mail_logs_frame)
mail_logs_buttons.pack(fill="x", padx=10, pady=0)
ttk.Button(mail_logs_buttons, text="Vider les Logs", command=clear_mail_logs).pack(side=tk.RIGHT)

mail_logs = scrolledtext.ScrolledText(mail_logs_frame, height=10, wrap=tk.WORD)
mail_logs.pack(fill="both", expand=True, padx=10, pady=10)
mail_logs.config(state=tk.DISABLED)

# --- Status Bar ---
status_frame = ttk.Frame(root)
status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

status_message = tk.StringVar()
try:
    with open('/var/log/auth.log', 'r'):
        status_message.set("✅ Running with correct permissions")
except:
    status_message.set("⚠️ Application sans permissions élevées")
        

ttk.Label(status_frame, textvariable=status_message, font=("Arial", 10)).pack(side=tk.LEFT)

# --- Background log monitoring ---
def tail_log_file(file_path, log_queue, stop_event):
    try:
        with open(file_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    log_queue.put(line.strip())
                else:
                    time.sleep(0.5)
    except Exception as e:
        log_queue.put(f"[ERREUR] {file_path}: {e}")

def update_log_widget(widget, log_queue):
    try:
        while True:
            line = log_queue.get_nowait()
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, line + "\n")
            widget.see(tk.END)
            widget.config(state=tk.DISABLED)
    except queue.Empty:
        pass
    root.after(500, update_log_widget, widget, log_queue)

# --- Refresh dynamic system data ---
def refresh_data():
    try:
        local_time.set(get_local_time())
    except:
        local_time.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    try:
        timezone.set(get_timezone())
    except:
        timezone.set(datetime.datetime.now().astimezone().tzname() or "Unknown")
        
    try:
        postfix_info.set(get_postfix_status())
    except:
        postfix_info.set("Postfix: Status unknown")
    
    try:
        cpu_usage.set(get_cpu_usage())
    except:
        cpu_usage.set("N/A")
    
    try:
        memory_usage.set(get_memory_usage())
    except:
        memory_usage.set("N/A")
    
    try:
        disk_usage.set(get_disk_usage())
    except:
        disk_usage.set("N/A")
    
    root.after(1000, refresh_data)

# --- Start Threads and UI Pollers ---
stop_event = threading.Event()

auth_log_path = '/var/log/auth.log' if os.path.exists('/var/log/auth.log') else '/var/log/secure'
mail_log_path = '/var/log/mail.log' if os.path.exists('/var/log/mail.log') else '/var/log/maillog'

threading.Thread(target=tail_log_file, args=(auth_log_path, system_log_queue, stop_event), daemon=True).start()
threading.Thread(target=tail_log_file, args=(mail_log_path, mail_log_queue, stop_event), daemon=True).start()

update_log_widget(system_logs, system_log_queue)
update_log_widget(mail_logs, mail_log_queue)

# --- Exit Handling ---
def on_closing():
    stop_event.set()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

refresh_data()
root.mainloop()
