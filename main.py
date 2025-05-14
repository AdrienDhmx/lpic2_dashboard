import tkinter as tk
from tkinter import ttk, scrolledtext
from utils import *
import os
import time
import datetime
import threading
import queue
import subprocess

# Create queues for log updates
system_log_queue = queue.Queue()
mail_log_queue = queue.Queue()

def refresh_data():
    # Update all dynamic variables
    try:
        local_time.set(get_local_time())
    except:
        local_time.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    try:
        timezone.set(get_timezone())
    except:
        timezone.set(datetime.datetime.now().astimezone().tzname() or "Unknown")
        
    try:
        postfix_info.set(f"Postfix: {get_postfix_status()}")
    except:
        try:
            # Try to check Postfix status using systemctl
            result = subprocess.run(
                ["systemctl", "is-active", "postfix"],
                capture_output=True,
                text=True,
                timeout=2
            )
            status = result.stdout.strip()
            if status == "active":
                postfix_info.set("Postfix: Active ✅")
            else:
                postfix_info.set(f"Postfix: Inactive ❌ ({status})")
        except:
            postfix_info.set("Postfix: Status unknown")
    
    # System resources data
    try:
        cpu_usage.set(get_cpu_usage())
    except:
        try:
            # Fallback to reading /proc/stat for CPU usage
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                if line.startswith('cpu '):
                    parts = line.split()
                    total = sum(float(x) for x in parts[1:])
                    idle = float(parts[4])
                    usage = 100.0 * (1.0 - idle / total)
                    cpu_usage.set(f"{usage:.1f}%")
                else:
                    cpu_usage.set("N/A")
        except:
            cpu_usage.set("N/A")
    
    try:
        memory_usage.set(get_memory_usage())
    except:
        try:
            # Fallback to reading /proc/meminfo for memory usage
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_total = None
                mem_available = None
                
                for line in lines:
                    if line.startswith('MemTotal:'):
                        mem_total = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        mem_available = int(line.split()[1])
                
                if mem_total and mem_available:
                    used_percent = 100.0 * (1.0 - mem_available / mem_total)
                    memory_usage.set(f"{used_percent:.1f}%")
                else:
                    memory_usage.set("N/A")
        except:
            memory_usage.set("N/A")
    
    try:
        disk_usage.set(get_disk_usage())
    except:
        try:
            # Fallback to df command for disk usage
            result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True,
                timeout=2
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    disk_usage.set(f"{parts[4]} ({parts[2]} used of {parts[1]})")
                else:
                    disk_usage.set("N/A")
            else:
                disk_usage.set("N/A")
        except:
            disk_usage.set("N/A")
    
    # Process any pending log updates
    process_log_updates()
    
    root.after(1000, refresh_data)  # refresh every second

def process_log_updates():
    # Process system logs
    try:
        while True:  # Process all available updates
            log_entry = system_log_queue.get_nowait()
            system_logs.config(state=tk.NORMAL)
            system_logs.insert(tk.END, log_entry + "\n")
            system_logs.see(tk.END)  # Auto-scroll to the end
            system_logs.config(state=tk.DISABLED)
            system_log_queue.task_done()
    except queue.Empty:
        pass  # No more updates
        
    # Process mail logs
    try:
        while True:  # Process all available updates
            log_entry = mail_log_queue.get_nowait()
            mail_logs.config(state=tk.NORMAL)
            mail_logs.insert(tk.END, log_entry + "\n")
            mail_logs.see(tk.END)  # Auto-scroll to the end
            mail_logs.config(state=tk.DISABLED)
            mail_log_queue.task_done()
    except queue.Empty:
        pass  # No more updates

def monitor_system_logs():
    """Monitor system logs for authentication and other system events."""
    system_log_path = "/var/log/auth.log"  # Path to auth log
    
    # First, try to use journalctl to read logs (works even without root)
    try:
        # Show initial message
        system_log_queue.put("Starting system log monitor...")
        system_log_queue.put("Attempting to read system logs using journalctl...")
        
        # Use journalctl to monitor system logs (works as regular user)
        process = subprocess.Popen(
            ["journalctl", "-f", "-n", "10", "_COMM=sshd", "_COMM=sudo", "_COMM=login"],
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Read from the process output
        for line in iter(process.stdout.readline, ''):
            system_log_queue.put(line.strip())
            
        process.stdout.close()
        process.wait()
        
    except Exception as journalctl_error:
        system_log_queue.put(f"Journalctl error: {journalctl_error}")
        system_log_queue.put("Falling back to direct log file access...")
        
        # Fall back to direct file reading
        try:
            if not os.path.exists(system_log_path):
                system_log_queue.put(f"Log file {system_log_path} not found!")
                system_log_queue.put("Please run the application with sudo or add your user to the adm group.")
                
            # Get the current file size
            file_size = os.path.getsize(system_log_path)
            
            # Show some recent lines from the log
            try:
                with open(system_log_path, 'r') as f:
                    # Try to show the last 10 lines initially
                    last_lines = []
                    for line in f:
                        last_lines.append(line.strip())
                        if len(last_lines) > 10:
                            last_lines.pop(0)
                    
                    for line in last_lines:
                        system_log_queue.put(line)
            except PermissionError:
                system_log_queue.put("Permission denied when trying to read existing log lines.")
            
            # Now monitor for new lines
            with open(system_log_path, 'r') as f:
                # Move to the end of the file
                f.seek(file_size)
                
                while True:
                    line = f.readline()
                    if line:
                        # Include ALL auth log entries - removed filtering
                        system_log_queue.put(line.strip())
                    else:
                        time.sleep(1)  # Sleep briefly before checking for new content
                        
        except PermissionError:
            system_log_queue.put(f"Permission denied: Cannot access {system_log_path}")
            system_log_queue.put("Please run this application with sudo or add your user to the adm group.")
            system_log_queue.put("Showing simulated system log data instead.")
            
            # Simulate some system logs for display purposes
            while True:
                time.sleep(5)
                timestamp = datetime.datetime.now().strftime("%b %d %H:%M:%S")
                hostname = os.uname()[1]
                
                # Sample log messages that might appear in auth.log
                messages = [
                    f"{timestamp} {hostname} sudo: adrien : TTY=pts/0 ; PWD=/home/adrien ; USER=root ; COMMAND=/usr/bin/apt update",
                    f"{timestamp} {hostname} sshd[1234]: Accepted publickey for adrien from 192.168.1.10 port 55555 ssh2",
                    f"{timestamp} {hostname} systemd-logind[123]: New session 456 of user adrien."
                ]
                
                import random
                system_log_queue.put(f"(SIMULATED) {random.choice(messages)}")
        
        except Exception as e:
            system_log_queue.put(f"Error monitoring system logs: {str(e)}")
            
            # Simulate some system logs for display purposes
            while True:
                time.sleep(5)
                timestamp = datetime.datetime.now().strftime("%b %d %H:%M:%S")
                hostname = os.uname()[1]
                system_log_queue.put(f"(SIMULATED) {timestamp} {hostname} - Error accessing real logs: {str(e)}")

def monitor_mail_logs():
    """Monitor mail logs for Postfix events."""
    mail_log_path = "/var/log/mail.log"  # Path to mail log
    
    try:
        if not os.path.exists(mail_log_path):
            mail_log_queue.put(f"Log file {mail_log_path} not found.")
            mail_log_queue.put("Please run the application with sudo or add your user to the adm group.")
            return
            
        # Get the current file size
        file_size = os.path.getsize(mail_log_path)
        
        # Show some recent lines from the log
        try:
            with open(mail_log_path, 'r') as f:
                # Try to show the last 10 lines initially
                last_lines = []
                for line in f:
                    last_lines.append(line.strip())
                    if len(last_lines) > 10:
                        last_lines.pop(0)
                
                for line in last_lines:
                    mail_log_queue.put(line)
        except PermissionError:
            mail_log_queue.put("Permission denied when trying to read existing log lines.")
        
        # Now monitor for new lines
        with open(mail_log_path, 'r') as f:
            # Move to the end of the file
            f.seek(file_size)
            
            while True:
                line = f.readline()
                if line:
                    # Include ALL mail log entries
                    mail_log_queue.put(line.strip())
                else:
                    time.sleep(1)  # Sleep briefly before checking for new content
                    
    except PermissionError:
        mail_log_queue.put(f"Permission denied: Cannot access {mail_log_path}")
        mail_log_queue.put("Please run this application with sudo or add your user to the adm group.")
    
    except Exception as e:
        mail_log_queue.put(f"Error monitoring mail logs: {str(e)}")

# --- Interface Tkinter ---
root = tk.Tk()
root.title("Dashboard Client")
root.geometry("1200x800")
root.configure(bg="#f4f4f4")

# Variables dynamiques
local_time = tk.StringVar()
timezone = tk.StringVar()
postfix_info = tk.StringVar()
cpu_usage = tk.StringVar()
memory_usage = tk.StringVar()
disk_usage = tk.StringVar()

style = ttk.Style()
style.configure("TLabel", font=("Arial", 12))
style.configure("TFrame", background="#f0f0f0")

# Main container frame
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Configure grid layout
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(0, weight=1)  # Status blocks
main_frame.rowconfigure(1, weight=2)  # System resources
main_frame.rowconfigure(2, weight=3)  # Logs section - more space

# --- Time Block (Top Left) ---
time_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
time_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(time_frame, text="⏰ Informations Temporelles", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

time_content = ttk.Frame(time_frame)
time_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(time_content, text="⏰ Heure locale :", style="TLabel").grid(row=0, column=0, sticky="w", pady=5)
ttk.Label(time_content, textvariable=local_time, style="TLabel").grid(row=0, column=1, sticky="w", pady=5)

ttk.Label(time_content, text="🌐 Fuseau Horaire :", style="TLabel").grid(row=1, column=0, sticky="w", pady=5)
ttk.Label(time_content, textvariable=timezone, style="TLabel").grid(row=1, column=1, sticky="w", pady=5)

# --- Mail Block (Top Right) ---
mail_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(mail_frame, text="📧 Informations Mail", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

mail_content = ttk.Frame(mail_frame)
mail_content.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Label(mail_content, text="📧 État de ", style="TLabel").grid(row=0, column=0, sticky="w", pady=5)
ttk.Label(mail_content, textvariable=postfix_info, style="TLabel").grid(row=0, column=1, sticky="w", pady=5)

# --- Resources Block (Middle) ---
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

# --- System Logs Block (Bottom Left) ---
system_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
system_logs_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(system_logs_frame, text="🔒 Logs Système (Auth)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

# Add clear button for system logs
sys_logs_buttons = ttk.Frame(system_logs_frame)
sys_logs_buttons.pack(fill="x", padx=10, pady=0)

def clear_system_logs():
    system_logs.config(state=tk.NORMAL)
    system_logs.delete(1.0, tk.END)
    system_logs.config(state=tk.DISABLED)

ttk.Button(sys_logs_buttons, text="Vider les Logs", command=clear_system_logs).pack(side=tk.RIGHT)

# Scrolled text widget for system logs
system_logs = scrolledtext.ScrolledText(system_logs_frame, height=10, wrap=tk.WORD)
system_logs.pack(fill="both", expand=True, padx=10, pady=10)
system_logs.config(state=tk.DISABLED)  # Make it read-only

# --- Mail Logs Block (Bottom Right) ---
mail_logs_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
mail_logs_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(mail_logs_frame, text="📨 Logs Mail (Postfix)", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

# Add clear button for mail logs
mail_logs_buttons = ttk.Frame(mail_logs_frame)
mail_logs_buttons.pack(fill="x", padx=10, pady=0)

def clear_mail_logs():
    mail_logs.config(state=tk.NORMAL)
    mail_logs.delete(1.0, tk.END)
    mail_logs.config(state=tk.DISABLED)

ttk.Button(mail_logs_buttons, text="Vider les Logs", command=clear_mail_logs).pack(side=tk.RIGHT)

# Scrolled text widget for mail logs
mail_logs = scrolledtext.ScrolledText(mail_logs_frame, height=10, wrap=tk.WORD)
mail_logs.pack(fill="both", expand=True, padx=10, pady=10)
mail_logs.config(state=tk.DISABLED)  # Make it read-only

# Add a status bar at the bottom
status_frame = ttk.Frame(root)
status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

# Status message
status_message = tk.StringVar()

# Check if running with elevated permissions and update status
try:
    with open('/var/log/auth.log', 'r') as f:
        # If we can open this file, we have the right permissions
        status_message.set("✅ Running with correct permissions")
except:
    # If we can't open the file, check if journalctl is available
    try:
        result = subprocess.run(
            ["journalctl", "-n", "1"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            status_message.set("⚠️ Utilisation de journalctl pour les logs (limite)")
        else:
            status_message.set("⚠️ Application sans permissions eleve (limite)")
    except:
        status_message.set("⚠️ Application sans permissions eleve (limite)")

status_label = ttk.Label(status_frame, textvariable=status_message, font=("Arial", 10))
status_label.pack(side=tk.LEFT)

# Start monitoring threads
try:
    # Start log monitoring in separate threads
    system_thread = threading.Thread(target=monitor_system_logs, daemon=True)
    system_thread.start()
    
    mail_thread = threading.Thread(target=monitor_mail_logs, daemon=True)
    mail_thread.start()
except Exception as e:
    print(f"Error starting log monitor threads: {e}")

refresh_data()

root.mainloop()