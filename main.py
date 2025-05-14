import tkinter as tk
from tkinter import ttk
import subprocess
import time
import threading
import datetime
import pytz
import os

# --- Fonctions utiles ---

def get_local_time():
    tz = time.tzname[0]
    now = datetime.datetime.now()
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({tz})"

def get_ntp_status():
    try:
        output = subprocess.check_output(["chronyc", "tracking"], stderr=subprocess.DEVNULL)
        return output.decode()
    except:
        return "Chrony non disponible"

def get_postfix_status():
    try:
        output = subprocess.check_output(["systemctl", "is-active", "postfix"], stderr=subprocess.DEVNULL)
        return output.decode().strip()
    except:
        return "Postfix non disponible"

def refresh_data():
    local_time.set(get_local_time())
    ntp_info.set(get_ntp_status())
    postfix_info.set(f"Postfix: {get_postfix_status()}")
    root.after(10000, refresh_data)  # actualiser toutes les 10 secondes

# --- Interface Tkinter ---

root = tk.Tk()
root.title("Dashboard Client Debian")
root.geometry("700x400")

style = ttk.Style()
style.configure("TLabel", font=("Arial", 12))
style.configure("TFrame", background="#f0f0f0")

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Variables dynamiques
local_time = tk.StringVar()
ntp_info = tk.StringVar()
postfix_info = tk.StringVar()

# Éléments
ttk.Label(main_frame, text="⏰ Heure locale :").grid(row=0, column=0, sticky="w")
ttk.Label(main_frame, textvariable=local_time).grid(row=0, column=1, sticky="w")

ttk.Label(main_frame, text="🔁 Synchronisation NTP :").grid(row=1, column=0, sticky="nw")
ttk.Label(main_frame, textvariable=ntp_info, wraplength=500).grid(row=1, column=1, sticky="w")

ttk.Label(main_frame, text="📧 État de Postfix :").grid(row=2, column=0, sticky="w")
ttk.Label(main_frame, textvariable=postfix_info).grid(row=2, column=1, sticky="w")

# Lancer l'actualisation
refresh_data()

# Boucle Tkinter
root.mainloop()
