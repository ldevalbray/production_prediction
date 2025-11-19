import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import subprocess, sys, os, json, threading, itertools, time
from datetime import datetime
from tkinter import messagebox
from pathlib import Path

# Import de l'utilitaire PyInstaller
try:
    from pyinstaller_utils import is_pyinstaller, get_script_path
except ImportError:
    # Si le module n'est pas disponible, définir des fonctions de repli
    def is_pyinstaller():
        return False
    def get_script_path(script_name):
        return script_name

# --- CONFIG ---
LAST_RUN_FILE = "last_runs.json"
EXCEL_PATH = "recoltes_fraises.xlsx"
FORECASTS_DIR = "forecasts"

script_running = False
spinner_running = False
spinner_job = None
spinner_cycle = itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"])

# --- UTILITAIRES ---
def safe_load_json(p):
    if not Path(p).exists():
        return {}
    try:
        return json.load(open(p))
    except Exception:
        return {}

def save_last_run(mode, status="✅ Succès"):
    d = safe_load_json(LAST_RUN_FILE)
    d[mode] = {"time": datetime.now().strftime("%d %b %H:%M"), "status": status}
    json.dump(d, open(LAST_RUN_FILE, "w"), indent=2)
    refresh_labels()

def refresh_labels():
    d = safe_load_json(LAST_RUN_FILE)
    f = d.get("forecast", {})
    u = d.get("update", {})
    lbl_forecast.config(text=f"Prévision : {f.get('time','–')} {f.get('status','')}")
    lbl_update.config(text=f"Modèle : {u.get('time','–')} {u.get('status','')}")

def append_history(txt, tag="default"):
    history_box.config(state="normal")
    history_box.insert("1.0", txt + "\n", tag)
    history_box.config(state="disabled")

def open_file(path):
    """Ouvre un fichier/dossier sans bloquer l'interface, compatible macOS/Windows."""
    p = Path(path).resolve()
    if not p.exists():
        messagebox.showerror("Erreur", f"{p} introuvable")
        return
    try:
        if sys.platform.startswith("darwin"):
            os.system(f"open '{p}' &")  # Finder non bloquant
        elif os.name == "nt":
            os.startfile(str(p))
        else:
            os.system(f"xdg-open '{p}' &")
        time.sleep(0.2)
        append_history(f"Ouverture de {p.name}", "success")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d’ouvrir {path}: {e}")
        append_history(f"Erreur ouverture {p.name}: {e}", "danger")

# --- SPINNER ---
def start_spinner():
    global spinner_running, spinner_job
    spinner_running = True
    def spin():
        global spinner_job
        if not spinner_running: return
        status_label.config(text=f"{next(spinner_cycle)} En cours...", bootstyle="info")
        spinner_job = root.after(100, spin)
    spin()

def stop_spinner(txt="", style="success"):
    global spinner_running, spinner_job
    spinner_running = False
    if spinner_job:
        try:
            root.after_cancel(spinner_job)
        except: pass
    status_label.config(text=txt, bootstyle=style)

# --- EXECUTION SCRIPT ---
def run_script(mode):
    global script_running
    if script_running:
        messagebox.showinfo("En cours", "Une opération est déjà en cours.")
        return
    script_running = True
    btn_forecast.config(state="disabled")
    btn_update.config(state="disabled")
    start_spinner()

    def worker():
        ok = True
        err = ""
        try:
            script_path = get_script_path("run_daily_cycle.py")
            subprocess.run(
                [sys.executable, script_path, "--mode", mode],
                check=True, text=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            ok = False
            err = e.stderr or ""
        def finish():
            global script_running
            script_running = False
            if ok:
                save_last_run(mode, "✅ Succès")
                append_history(f"{datetime.now():%d %b %H:%M} — {mode} terminé avec succès", "success")
                stop_spinner("✅ Terminé", "success")
            else:
                save_last_run(mode, "❌ Erreur")
                append_history(f"{datetime.now():%d %b %H:%M} — {mode} échoué : {err[:100]}", "danger")
                stop_spinner("❌ Erreur", "danger")
                messagebox.showerror("Erreur", err[:1000])
            btn_forecast.config(state="normal")
            btn_update.config(state="normal")
            refresh_labels()
        root.after(0, finish)
    threading.Thread(target=worker, daemon=True).start()

# --- INTERFACE ---
root = ttk.Window(themename="superhero")
root.title("Pépinière Valbray – Tableau de bord")
root.geometry("850x600")

main = ttk.Frame(root)
main.pack(fill=BOTH, expand=True)

# --- BARRE SUPÉRIEURE ---
top = ttk.Frame(main, bootstyle="dark")
top.pack(fill=X)
ttk.Label(top, text="PÉPINIÈRE VALBRAY", font=("Helvetica", 20, "bold"), bootstyle="inverse-dark").pack(side=LEFT, padx=20, pady=10)
ttk.Label(top, text="Tableau de bord – Automatisations récolte", font=("Helvetica", 11), bootstyle="secondary").pack(side=LEFT, pady=15)

# --- BARRE LATÉRALE ---
side = ttk.Frame(main, width=260, bootstyle="dark")
side.pack(side=LEFT, fill=Y)
side.pack_propagate(False)

lbl_forecast = ttk.Label(side, text="Prévision : –", font=("Helvetica", 10))
lbl_forecast.pack(pady=(30, 5))
lbl_update = ttk.Label(side, text="Modèle : –", font=("Helvetica", 10))
lbl_update.pack(pady=(0, 20))

# --- BOUTONS PLEINE LARGEUR ---
btn_forecast = ttk.Button(side, text="Générer les prévisions", bootstyle="success", padding=10, command=lambda: run_script("forecast"))
btn_forecast.pack(pady=6, fill=X, expand=True)

btn_update = ttk.Button(side, text="Mettre à jour le modèle", bootstyle="secondary", padding=10, command=lambda: run_script("update"))
btn_update.pack(pady=6, fill=X, expand=True)

ttk.Button(side, text="Ouvrir les données de récolte", bootstyle="info", padding=10, command=lambda: open_file(EXCEL_PATH)).pack(pady=6, fill=X, expand=True)
ttk.Button(side, text="Ouvrir les prévisions", bootstyle="info", padding=10, command=lambda: open_file(FORECASTS_DIR)).pack(pady=6, fill=X, expand=True)

status_label = ttk.Label(side, text="", font=("Helvetica", 10))
status_label.pack(pady=20)

# --- CONTENU PRINCIPAL ---
content = ttk.Frame(main)
content.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

ttk.Label(content, text="Historique des opérations", font=("Helvetica", 13, "bold")).pack(pady=(10, 0))
history_box = ttk.Text(content, height=22, width=80, wrap="word", font=("Courier", 9))
history_box.pack(padx=10, pady=5)
history_box.config(state="disabled")
history_box.tag_config("success", foreground="#66ff99")
history_box.tag_config("danger", foreground="#ff6666")

refresh_labels()
root.mainloop()
