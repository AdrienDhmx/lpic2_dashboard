import re
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import datetime
import queue
import threading
import os
import time
import json
import csv
from utils import *

def tail_log_file(file_path, log_queue, stop_event, log_store):
    try:
        with open(file_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    category = categorize_log(line)
                    log_entry = {
                        'category': category,
                        'line': line.strip()
                    }
                    log_store.append(log_entry)
                    log_queue.put(log_entry)
                else:
                    time.sleep(0.5)
    except Exception as e:
        log_queue.put({'category': 'Error', 'line': f"[ERROR] {file_path}: {e}"})

def update_log_widget(widget, log_queue, filter_var):
    try:
        while True:
            log_entry = log_queue.get_nowait()
            if filter_var.get() == "Tous" or log_entry['category'] == filter_var.get():
                widget.config(state=tk.NORMAL)
                widget.insert(tk.END, log_entry['line'] + "\n")
                widget.see(tk.END)
                widget.config(state=tk.DISABLED)
    except queue.Empty:
        pass
    root.after(500, update_log_widget, widget, log_queue, filter_var)

def filter_logs(widget, log_queue, filter_var, log_store):
        new_lines = []
        while not log_queue.empty():
            line = log_queue.get_nowait()
            if log_store is not None:
                log_store.append(line)
            new_lines.append(line)

        # Apply filter before inserting into widget
        selected_filter = filter_var.get()

        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)

        for line in (log_store or new_lines):
            category = categorize_log(line['line'])
            if selected_filter == "Tous" or category == selected_filter:
                widget.insert(tk.END, line['line'] + "\n")

        widget.config(state=tk.DISABLED)

def export_logs(log_store, selected_category):
    filtered = [
        log for log in log_store
        if selected_category == "Tous" or log['category'] == selected_category
    ]

    filetypes = [("JSON file", "*.json"), ("CSV file", "*.csv")]
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=filetypes)

    if not file_path:
        return

    try:
        if file_path.endswith(".json"):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(filtered, f, indent=2)
        elif file_path.endswith(".csv"):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["category", "line"])
                writer.writeheader()
                for row in filtered:
                    writer.writerow(row)
    except Exception as e:
        print(f"Export failed: {e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Dashboard Client")
root.geometry("1200x800")
root.configure(bg="#f4f4f4")

local_time = tk.StringVar()
timezone = tk.StringVar()
postfix_info = tk.StringVar()
cpu_usage = tk.StringVar()
memory_usage = tk.StringVar()
disk_usage = tk.StringVar()

system_log_queue = queue.Queue()
mail_log_queue = queue.Queue()
system_log_store = []
mail_log_store = []

style = ttk.Style()
style.configure("TLabel", font=("Arial", 12))
style.configure("TFrame", background="#f0f0f0")

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(2, weight=3)

# Time frame
time_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
time_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(time_frame, text="⏰ Informations Temporelles", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
time_content = ttk.Frame(time_frame)
time_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(time_content, text="⏰ Heure locale :", style="TLabel").grid(row=0, column=0, sticky="w")
ttk.Label(time_content, textvariable=local_time, style="TLabel").grid(row=0, column=1, sticky="w")
ttk.Label(time_content, text="🌐 Fuseau Horaire :", style="TLabel").grid(row=1, column=0, sticky="w")
ttk.Label(time_content, textvariable=timezone, style="TLabel").grid(row=1, column=1, sticky="w")

# Mail status frame
mail_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(mail_frame, text="📧 Informations Mail", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
mail_content = ttk.Frame(mail_frame)
mail_content.pack(fill="both", expand=True, padx=20, pady=10)
ttk.Label(mail_content, text="📧 État de ", style="TLabel").grid(row=0, column=0, sticky="w")
ttk.Label(mail_content, textvariable=postfix_info, style="TLabel").grid(row=0, column=1, sticky="w")

# System resources frame
resources_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
resources_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
ttk.Label(resources_frame, text="💻 Ressources Système", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
resources_content = ttk.Frame(resources_frame)
resources_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(resources_content, text="💻 Utilisation CPU :", style="TLabel").grid(row=0, column=0, sticky="w")
ttk.Label(resources_content, textvariable=cpu_usage, style="TLabel").grid(row=0, column=1, sticky="w")
ttk.Label(resources_content, text="🧠 Utilisation Mémoire :", style="TLabel").grid(row=1, column=0, sticky="w")
ttk.Label(resources_content, textvariable=memory_usage, style="TLabel").grid(row=1, column=1, sticky="w")
ttk.Label(resources_content, text="💾 Utilisation Disque :", style="TLabel").grid(row=2, column=0, sticky="w")
ttk.Label(resources_content, textvariable=disk_usage, style="TLabel").grid(row=2, column=1, sticky="w")

# --- Logs ---
# System Logs
system_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
system_logs_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
ttk.Label(system_logs_frame, text="🔒 Logs Système (Auth)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

sys_logs_buttons = ttk.Frame(system_logs_frame)
sys_logs_buttons.pack(fill="x", padx=10, pady=0)
sys_filter_var = tk.StringVar(value="Tous")

ttk.Label(sys_logs_buttons, text="Filtrer :").pack(side=tk.LEFT)

ttk.Combobox(
    sys_logs_buttons,
    textvariable=sys_filter_var,
    values=[
        "Tous",
        "Connexion Réussie",
        "Échec d’Authentification",
        "Fin de Session",
        "Session Sudo Démarrée",
        "Session Sudo Terminée",
        "Commande avec Privilèges (sudo)",
        "Autre"
    ],
    state="readonly"
).pack(side=tk.LEFT)


def export_system_logs():
    export_logs(system_log_store, sys_filter_var.get())

ttk.Button(sys_logs_buttons, text="Exporter", command=export_system_logs).pack(side=tk.RIGHT)

system_logs = scrolledtext.ScrolledText(system_logs_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
system_logs.pack(fill="both", expand=True, padx=10, pady=10)

def on_sys_filter_change(event=None):
    filter_logs(system_logs, system_log_queue, sys_filter_var, system_log_store)

sys_filter_var.trace_add("write", lambda *args: on_sys_filter_change())


# Mail Logs
mail_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_logs_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
ttk.Label(mail_logs_frame, text="📨 Logs Mail (Postfix)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

mail_logs_buttons = ttk.Frame(mail_logs_frame)
mail_logs_buttons.pack(fill="x", padx=10, pady=0)
mail_filter_var = tk.StringVar(value="Tous")

ttk.Label(mail_logs_buttons, text="Filtrer :").pack(side=tk.LEFT)

ttk.Combobox(
    mail_logs_buttons,
    textvariable=mail_filter_var,
    values=[
        "Tous",
        "Mail Envoyé",
        "Mail Reçu",
        "Échec d’Envoi de Mail",
        "Autre"
    ],
    state="readonly"
).pack(side=tk.LEFT)


def on_mail_filter_change(event=None):
    filter_logs(mail_logs, mail_log_queue, mail_filter_var, mail_log_store)

mail_filter_var.trace_add("write", lambda *args: on_mail_filter_change())


def export_mail_logs():
    export_logs(mail_log_store, mail_filter_var.get())

ttk.Button(mail_logs_buttons, text="Exporter", command=export_mail_logs).pack(side=tk.RIGHT)

mail_logs = scrolledtext.ScrolledText(mail_logs_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
mail_logs.pack(fill="both", expand=True, padx=10, pady=10)

# Status bar
status_frame = ttk.Frame(root)
status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
status_message = tk.StringVar()
status_label = ttk.Label(status_frame, textvariable=status_message, font=("Arial", 10))
status_label.pack(side=tk.LEFT)

try:
    with open('/var/log/auth.log', 'r') as f:
        status_message.set("✅ Exécution avec les permissions appropriées")
except:
    status_message.set("⚠️ Permissions limitées (essayez avec sudo)")

# Data Refresh Function
def refresh_data():
    try: local_time.set(get_local_time())
    except: local_time.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try: timezone.set(get_timezone())
    except: timezone.set("Unknown")
    try: postfix_info.set(f"Postfix: {get_postfix_status()}")
    except: postfix_info.set("Postfix: Status unknown")
    try: cpu_usage.set(get_cpu_usage())
    except: cpu_usage.set("N/A")
    try: memory_usage.set(get_memory_usage())
    except: memory_usage.set("N/A")
    try: disk_usage.set(get_disk_usage())
    except: disk_usage.set("N/A")
    root.after(1000, refresh_data)

# Start threads
stop_event = threading.Event()
auth_log_path = '/var/log/auth.log' if os.path.exists('/var/log/auth.log') else '/var/log/secure'
mail_log_path = '/var/log/mail.log' if os.path.exists('/var/log/mail.log') else '/var/log/maillog'

threading.Thread(target=tail_log_file, args=(auth_log_path, system_log_queue, stop_event, system_log_store), daemon=True).start()
threading.Thread(target=tail_log_file, args=(mail_log_path, mail_log_queue, stop_event, mail_log_store), daemon=True).start()

update_log_widget(system_logs, system_log_queue, sys_filter_var)
update_log_widget(mail_logs, mail_log_queue, mail_filter_var)

def on_closing():
    stop_event.set()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

refresh_data()
root.mainloop()
