import html as html_module
import re
import os
import glob
import subprocess
import platform
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta, date
from fpdf import FPDF, XPos, YPos

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import keyring
except ImportError:
    keyring = None

APP_NAME = "Planning ADMR"
APP_VERSION = "1.0.0"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MON_FILENAME = "Mon ADMR  ▹  Mon planning.html"

BASE_URL = "https://www.monadmr.org"
LOGIN_URL = BASE_URL + "/connexion"
PLANNING_URL = BASE_URL + "/mon-planning"
KEYRING_SERVICE = "admr-planning"

MOIS_SLUGS = {
    1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "aout",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre",
}

def get_week_number(date_str):
    """Try to determine week number from the first date in the HTML."""
    try:
        # Assuming format like '4' from the HTML extraction
        day_num = int(date_str)
        # Note: This is a simplification; for a specific year, you'd use datetime
        # For now, we will use the current year/month to find the week
        now = datetime.now()
        target_date = now.replace(day=day_num)
        return target_date.isocalendar()[1]
    except:
        return "inconnue"

def sanitize_pdf_text(text):
    """Map text to what the PDF built-in font (latin-1) can render."""
    text = html_module.unescape(text or "").replace("\xa0", " ")
    replacements = {
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u25b9": ">",
        "\u0153": "oe", "\u0152": "Oe", "\u00e6": "ae", "\u00c6": "Ae",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def process_planning(input_html_path):
    # 1. Read the source HTML file
    with open(input_html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    day_mapping = {
        "LUN.": "LUNDI", "MAR.": "MARDI", "MER.": "MERCREDI",
        "JEU.": "JEUDI", "VEN.": "VENDREDI", "SAM.": "SAMEDI", "DIM.": "DIMANCHE"
    }

    # 2. Extract Days and Dates
    day_pattern = re.compile(r'<span class="tx-gris txt-sm">(.*?)</span>.*?<strong>(\d+)</strong>', re.DOTALL)
    headers = day_pattern.findall(content)
    if not headers:
        raise ValueError("Impossible de trouver les dates dans le fichier HTML.")
        
    days_info = [f"{day_mapping.get(h[0].upper(), h[0].upper())} {h[1]}" for h in headers]
    
    # Get week number for the filename
    week_num = get_week_number(headers[0][1])

    # 3. Setup Directory and Paths
    doc_dir = os.path.expanduser("~/Documents/admr-planning")
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
    
    output_pdf_path = os.path.join(doc_dir, f"semaine_{week_num}.pdf")

    # 4. Parse day columns into (label, [(time, name), ...])
    columns = re.split(r'<div class="colonne-jour[^>]*">', content)[1:]
    inter_pattern = re.compile(
        r'<div class="horaires">\s*(.*?)\s*</div>.*?'
        r'<div class="intervenant">.*?</span>\s*(.*?)\s*</div>', re.DOTALL)
    days = []
    for i, col_content in enumerate(columns):
        if i >= 7:
            break
        entries = []
        for time_str, name_str in inter_pattern.findall(col_content):
            time_clean = re.sub('<[^<]+?>', '', time_str).strip()
            name_clean = re.sub('<[^<]+?>', '', name_str).strip()
            entries.append((time_clean, name_clean))
        days.append((days_info[i] if i < len(days_info) else f"JOUR {i+1}", entries))

    # 5. Render large-print PDF with fpdf2 (pure Python: bundles into .exe/.app)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(8, 8, 8)
    pdf.set_auto_page_break(True, margin=12)
    pdf.add_page()
    for label, entries in days:
        # Keep each day block on one page when possible (like CSS page-break-inside)
        block_h = 13 + (len(entries) * 19 if entries else 12) + 18
        if pdf.get_y() + block_h > 285:
            pdf.add_page()
        # Day header: bold, boxed, light grey background
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_fill_color(238, 238, 238)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(w=0, h=11, text=sanitize_pdf_text(label), border=1, fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        if entries:
            for time_str, name_str in entries:
                pdf.set_x(14)
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0, h=9, text=sanitize_pdf_text(time_str),
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_x(14)
                pdf.set_font("Helvetica", "", 16)
                pdf.set_text_color(51, 51, 51)
                pdf.cell(w=0, h=9, text=sanitize_pdf_text(name_str),
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)
                pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_x(14)
            pdf.set_font("Helvetica", "I", 14)
            pdf.set_text_color(85, 85, 85)
            pdf.cell(w=0, h=9, text="AUCUN PASSAGE",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)
        # Dashed writing line for handwritten notes
        pdf.ln(3)
        y = pdf.get_y()
        pdf.set_draw_color(153, 153, 153)
        pdf.set_dash_pattern(dash=2, gap=2)
        pdf.line(15, y, 195, y)
        pdf.set_dash_pattern()
        pdf.ln(9)

    pdf.output(output_pdf_path)
    return output_pdf_path

def open_file(path):
    """Opens the PDF automatically across Windows, Mac, or Linux."""
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', path))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(path)
    else:                                   # linux variants
        subprocess.call(('xdg-open', path))

class LoginError(Exception):
    """Raised when the ADMR login fails (bad credentials, site change...)."""
    pass


class PlanningNotAvailableError(Exception):
    """Raised when next week's planning is not published yet."""
    pass


def next_week_range(today=None):
    """Return (monday, sunday) dates of the upcoming week (Mon->Sun)."""
    today = today or date.today()
    monday_this_week = today - timedelta(days=today.weekday())
    monday = monday_this_week + timedelta(days=7)
    return monday, monday + timedelta(days=6)


def slugify_date(d):
    return f"{d.day}-{MOIS_SLUGS[d.month]}-{d.year}"


def build_week_url(monday, sunday):
    return (
        f"{BASE_URL}/mon-planning/hebdomadaire/"
        f"du-{slugify_date(monday)}-au-{slugify_date(sunday)}"
    )


def parse_login_page(page_html):
    """Extract (csrf_token, digit->secret_char mapping) from /connexion HTML."""
    soup = BeautifulSoup(page_html, "html.parser")
    token_input = soup.find("input", {"name": "connexion_csrf_token"})
    csrf_token = token_input.get("value", "") if token_input else ""
    if not csrf_token:
        raise LoginError("Page de connexion illisible (jeton manquant).")
    mapping = {}
    for btn in soup.select("button.digicode"):
        digit = btn.get("data-num")
        secret = html_module.unescape(btn.get("data-char") or "")
        if digit is not None and secret:
            mapping[digit] = secret
    if len(mapping) < 10:
        raise LoginError("Clavier de connexion illisible (chiffres manquants).")
    return csrf_token, mapping


def build_motdepasse(mapping, code_digits):
    try:
        return "".join(mapping[d] for d in code_digits)
    except KeyError as e:
        raise LoginError(f"Chiffre {e} absent du clavier de connexion.")


def new_session():
    if requests is None:
        raise LoginError("Le module 'requests' n'est pas installé.")
    if BeautifulSoup is None:
        raise LoginError("Le module 'beautifulsoup4' n'est pas installé.")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
    })
    return session


def login_admr(session, identifiant, code_digits):
    """Log in. Returns True on success, raises LoginError otherwise."""
    try:
        response = session.get(LOGIN_URL, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise LoginError(f"Impossible d'atteindre le site ADMR : {e}")
    csrf_token, mapping = parse_login_page(response.text)
    payload = {
        "identifiant": identifiant,
        "motdepasse": build_motdepasse(mapping, code_digits),
        "seSouvenirDeMoi": "1",
        "connexion_csrf_token": csrf_token,
    }
    try:
        response = session.post(LOGIN_URL, data=payload, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise LoginError(f"Erreur pendant la connexion : {e}")
    # A failed login re-displays the login form; a success shows account pages.
    page = response.text
    if 'id="form-connexion"' in page or 'name="connexion_csrf_token"' in page:
        raise LoginError("Identifiant ou mot de passe incorrect.")
    return True


def check_logged_in(session):
    """Return True if the session is authenticated (planning reachable)."""
    try:
        response = session.get(PLANNING_URL, timeout=20)
    except Exception:
        return False
    if response.status_code != 200:
        return False
    page = response.text
    if 'id="form-connexion"' in page or 'name="connexion_csrf_token"' in page:
        return False
    return True


def resolve_next_week_url(session, monday, sunday):
    """Pick the week URL for next week from /mon-planning links, else build it."""
    try:
        response = session.get(PLANNING_URL, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise PlanningNotAvailableError(f"Impossible d'ouvrir le planning : {e}")
    soup = BeautifulSoup(response.text, "html.parser")
    expected = f"du-{slugify_date(monday)}"
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/mon-planning/hebdomadaire/" in href and expected in href:
            return href if href.startswith("http") else BASE_URL + href
    return build_week_url(monday, sunday)


def download_planning_html(session, week_url):
    try:
        response = session.get(week_url, timeout=20)
    except Exception as e:
        raise PlanningNotAvailableError(f"Impossible de télécharger le planning : {e}")
    if response.status_code != 200 or "colonne-jour" not in response.text:
        raise PlanningNotAvailableError(
            "Le planning de la semaine prochaine n'est pas encore disponible.\n"
            "Il est généralement publié le samedi. Réessayez plus tard."
        )
    tmp_path = os.path.join(tempfile.gettempdir(), "mon_planning_suivant.html")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    return tmp_path


def download_next_week_pdf(identifiant, code_digits, status=None):
    """Full pipeline: login -> next-week download -> PDF. Returns pdf path."""
    def say(message):
        if status is not None:
            status(message)

    monday, sunday = next_week_range()
    say("Connexion au site ADMR…")
    session = new_session()
    login_admr(session, identifiant, code_digits)
    say("Recherche du planning de la semaine prochaine…")
    week_url = resolve_next_week_url(session, monday, sunday)
    say("Téléchargement du planning…")
    html_path = download_planning_html(session, week_url)
    say("Création du PDF en gros caractères…")
    return process_planning(html_path)


# --- Secure credential storage (macOS Keychain via keyring) ---

def save_credentials(identifiant, code_digits):
    if keyring is None:
        return False
    try:
        keyring.set_password(KEYRING_SERVICE, "identifiant", identifiant)
        keyring.set_password(KEYRING_SERVICE, "motdepasse", code_digits)
        return True
    except Exception:
        return False


def load_credentials():
    if keyring is None:
        return None, None
    try:
        identifiant = keyring.get_password(KEYRING_SERVICE, "identifiant")
        code = keyring.get_password(KEYRING_SERVICE, "motdepasse")
    except Exception:
        return None, None
    if identifiant and code:
        return identifiant, code
    return None, None


def clear_credentials():
    if keyring is None:
        return
    try:
        keyring.delete_password(KEYRING_SERVICE, "identifiant")
    except Exception:
        pass
    try:
        keyring.delete_password(KEYRING_SERVICE, "motdepasse")
    except Exception:
        pass


def find_mon_file():
    """Locate the MON planning HTML next to this script."""
    exact = os.path.join(SCRIPT_DIR, MON_FILENAME)
    if os.path.exists(exact):
        return exact
    # Fallback: tolerant match in case of space / NBSP variations
    candidates = sorted(glob.glob(os.path.join(SCRIPT_DIR, "Mon*.html")))
    if candidates:
        return candidates[0]
    return None

BIG_FONT = ("Arial", 18)
TITLE_FONT = ("Arial", 22, "bold")
BUTTON_FONT = ("Arial", 20, "bold")


def run_pipeline_with_fallback(identifiant, code_digits, status):
    """Try the automated download; fall back to the local MON file if offline."""
    try:
        return download_next_week_pdf(identifiant, code_digits, status=status)
    except (LoginError, PlanningNotAvailableError):
        raise
    except Exception as e:
        local = find_mon_file()
        if local:
            status("Problème internet : utilisation du fichier local…")
            return process_planning(local)
        raise PlanningNotAvailableError(f"Erreur inattendue : {e}")


class AdmrApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("520x560")
        self.identifiant, self.code = load_credentials()
        self.status_var = tk.StringVar(value="")
        if self.identifiant and self.code:
            self.show_progress()
            self.start_download(self.identifiant, self.code)
        else:
            self.show_login()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- Login form (first run) ---
    def show_login(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=30, pady=25)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Mon planning ADMR", font=TITLE_FONT).pack(pady=(0, 8))
        tk.Label(frame, text="Entrez vos identifiants une seule fois.\nEnsuite, un seul bouton suffit.",
                 font=("Arial", 14), justify="center").pack(pady=(0, 20))

        tk.Label(frame, text="Identifiant (9 caractères)", font=BIG_FONT, anchor="w").pack(fill="x")
        self.id_entry = tk.Entry(frame, font=BIG_FONT, width=20)
        self.id_entry.pack(fill="x", pady=(4, 14))
        if self.identifiant:
            self.id_entry.insert(0, self.identifiant)

        tk.Label(frame, text="Mot de passe (6 chiffres)", font=BIG_FONT, anchor="w").pack(fill="x")
        self.code_entry = tk.Entry(frame, font=BIG_FONT, width=20, show="•")
        self.code_entry.pack(fill="x", pady=(4, 14))

        self.remember_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Se souvenir de moi", font=("Arial", 15),
                       variable=self.remember_var).pack(anchor="w", pady=(0, 16))

        tk.Button(frame, text="Voir mon planning", font=BUTTON_FONT,
                  bg="#2e8b57", fg="white", height=2,
                  command=self.on_login_submit).pack(fill="x", pady=(0, 10))
        tk.Label(frame, textvariable=self.status_var, font=("Arial", 13),
                 wraplength=440, justify="center").pack(pady=(6, 0))
        self.id_entry.focus_set()

    def on_login_submit(self):
        identifiant = self.id_entry.get().strip()
        code = self.code_entry.get().strip()
        if len(identifiant) != 9:
            messagebox.showerror("Erreur", "L'identifiant doit comporter 9 caractères.")
            return
        if not (code.isdigit() and len(code) == 6):
            messagebox.showerror("Erreur", "Le mot de passe doit comporter 6 chiffres.")
            return
        if self.remember_var.get():
            save_credentials(identifiant, code)
        self.identifiant, self.code = identifiant, code
        self.show_progress()
        self.start_download(identifiant, code)

    # --- Progress view (every run) ---
    def show_progress(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=30, pady=40)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Mon planning ADMR", font=TITLE_FONT).pack(pady=(0, 25))
        self.progress_label = tk.Label(frame, text="Démarrage…", font=BIG_FONT,
                                       wraplength=440, justify="center")
        self.progress_label.pack(pady=(0, 30))
        tk.Button(frame, text="Changer d'identifiant", font=("Arial", 14),
                  command=self.on_change_account).pack()

    def on_change_account(self):
        clear_credentials()
        self.identifiant, self.code = None, None
        self.show_login()

    def set_status(self, message):
        def update():
            self.status_var.set(message)
            if hasattr(self, "progress_label") and self.progress_label.winfo_exists():
                self.progress_label.config(text=message)
        self.root.after(0, update)

    def start_download(self, identifiant, code):
        thread = threading.Thread(target=self._worker, args=(identifiant, code), daemon=True)
        thread.start()

    def _worker(self, identifiant, code):
        try:
            pdf_path = run_pipeline_with_fallback(identifiant, code, status=self.set_status)
        except LoginError as e:
            clear_credentials()
            self.root.after(0, lambda: (
                messagebox.showerror("Erreur de connexion", str(e)),
                self.show_login(),
            ))
            return
        except PlanningNotAvailableError as e:
            self.root.after(0, lambda: messagebox.showinfo("Planning indisponible", str(e)))
            self.root.after(0, lambda: self.set_status("Réessayez plus tard."))
            return
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erreur", f"Une erreur est survenue : {e}"))
            self.root.after(0, lambda: self.set_status("Une erreur est survenue."))
            return
        self.root.after(0, lambda: self.set_status("Planning ouvert !"))
        open_file(pdf_path)

    # --- Legacy local-file mode (kept as fallback, no dialogs) ---
    def run_local_only(self):
        try:
            file_path = find_mon_file()
            if not file_path:
                raise FileNotFoundError(
                    f"Fichier planning introuvable dans :\n{SCRIPT_DIR}\n"
                    f"(attendu : {MON_FILENAME})"
                )
            pdf_path = process_planning(file_path)
            open_file(pdf_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")


def run_auto():
    """Legacy entry point: convert the local MON file without any dialog."""
    root = tk.Tk()
    root.withdraw()
    try:
        file_path = find_mon_file()
        if not file_path:
            raise FileNotFoundError(
                f"Fichier planning introuvable dans :\n{SCRIPT_DIR}\n"
                f"(attendu : {MON_FILENAME})"
            )
        pdf_path = process_planning(file_path)
        open_file(pdf_path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")
    root.destroy()


def run_gui():
    root = tk.Tk()
    AdmrApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
