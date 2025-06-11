import re
import subprocess
import psutil
import time
import datetime
import os

def get_local_time():
    tz = time.tzname[0]
    now = datetime.datetime.now()
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({tz})"

def get_timezone():
    try:
        output = subprocess.check_output(["timedatectl", "show"], stderr=subprocess.DEVNULL)
        for line in output.decode().split("\n"):
            if line.startswith("Timezone="):
                return line.split("=")[1]
    except Exception:
        pass
    
    return time.tzname[0]

def get_ntp_status():
    try:
        output = subprocess.check_output(["chronyc", "tracking"], stderr=subprocess.DEVNULL)
        return output.decode()
    except:
        try:
            # Try ntpstat as alternative
            output = subprocess.check_output(["ntpstat"], stderr=subprocess.DEVNULL)
            return "NTP synchronized" if output.decode().strip() else "NTP not synchronized"
        except:
            return "NTP service non disponible"

def get_postfix_status():
    try:
        output = subprocess.check_output(["systemctl", "is-active", "postfix"], stderr=subprocess.DEVNULL)
        status = output.decode().strip()
        return "actif" if status == "active" else status
    except:
        return "non disponible"

def get_cpu_usage():
    return f"{psutil.cpu_percent()}%"

def get_memory_usage():
    memory = psutil.virtual_memory()
    return f"{memory.percent}% (Utilisé: {get_size(memory.used)} / Total: {get_size(memory.total)})"

def get_disk_usage():
    disk = psutil.disk_usage('/')
    return f"{disk.percent}% (Utilisé: {get_size(disk.used)} / Total: {get_size(disk.total)})"

def get_size(bytes):
    """
    Convert bytes to a human-readable format (KB, MB, GB).
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:3.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"

def tail_file(file_path, n=10):
    """Return the last n lines of a file."""
    try:
        if not os.path.exists(file_path):
            return [f"File not found: {file_path}"]
            
        # Use tail command for efficiency
        output = subprocess.check_output(['tail', '-n', str(n), file_path])
        return output.decode().splitlines()
    except Exception as e:
        return [f"Error reading {file_path}: {str(e)}"]

def get_recent_auth_logs(n=10):
    """Get recent authentication logs."""
    auth_log_paths = ['/var/log/auth.log', '/var/log/secure']
    
    for path in auth_log_paths:
        if os.path.exists(path):
            return tail_file(path, n)
    
    return ["Authentication logs not found"]

def get_recent_mail_logs(n=10):
    """Get recent mail logs."""
    mail_log_paths = ['/var/log/mail.log', '/var/log/maillog']
    
    for path in mail_log_paths:
        if os.path.exists(path):
            return tail_file(path, n)
    
    return ["Mail logs not found"]

def categorize_log(line):
    line_lower = line.lower()
    if re.search(r'sudo:.*command=', line_lower):
        return "Commande avec Privilèges (sudo)"

    if "session opened" in line_lower:
        if "sudo" in line_lower:
            return "Session Sudo Démarrée"
        return "Connexion Réussie"

    if "session closed" in line_lower:
        if "sudo" in line_lower:
            return "Session Sudo Terminée"
        return "Fin de Session"

    if "authentication failure" in line_lower or "failed password" in line_lower or "failed su" in line_lower:
        return "Échec d’Authentification"
    
    if "status=sent" in line_lower or "status=deliverable" in line_lower:
        return "Mail Envoyé"

    if "from=" in line_lower and "postfix/qmgr" in line_lower:
        return "Mail Reçu"

    if "status=bounced" in line_lower or "status=deferred" in line_lower or "status=expired" in line_lower:
        return "Échec d’Envoi de Mail"
        
    return 'Autre'
