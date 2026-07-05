import customtkinter as ctk
import hashlib, json, os
from datetime import date as _date

# ── Palette ────────────────────────────────────────────────────────
G50   = "#f0faf4"; G100 = "#d6f0e0"; G400 = "#4db882"
G500  = "#2ea065"; G600 = "#1d7a4a"; G700 = "#155c38"
G800  = "#0e3f28"; G900 = "#071f14"
ACCENT_GREEN = "#b5e48c"
PAGE_BG      = "#f7fdf9"
CARD_BG      = "#ffffff"
BORDER_COLOR = "#d0ead9"
TEXT_PRIMARY = G800
TEXT_MUTED   = "#8abfa4"
DANGER       = "#ef4444"
# ──────────────────────────────────────────────────────────────────

CONFIG_FILE = "config_securite.json"
DEFAULT_HASH = hashlib.sha256(b"1234").hexdigest()  # mot de passe par défaut : 1234


def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def _lire_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"password_hash": DEFAULT_HASH}


def _sauver_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


def verifier_mot_de_passe(pwd: str) -> bool:
    cfg = _lire_config()
    return _hash(pwd) == cfg.get("password_hash", DEFAULT_HASH)


def changer_mot_de_passe(ancien: str, nouveau: str) -> tuple[bool, str]:
    if not nouveau or len(nouveau) < 4:
        return False, "Le mot de passe doit contenir au moins 4 caractères."
    if not verifier_mot_de_passe(ancien):
        return False, "Mot de passe actuel incorrect."
    cfg = _lire_config()
    cfg["password_hash"] = _hash(nouveau)
    _sauver_config(cfg)
    return True, "Mot de passe modifié avec succès."


# ══════════════════════════════════════════════════════════════════
#  FENÊTRE DE CONNEXION
# ══════════════════════════════════════════════════════════════════
class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success   = on_success
        self.tentatives   = 0
        self.MAX_TENT     = 5

        self.title("Budget Wise — Connexion")
        self.geometry("420x540")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")
        self.configure(fg_color=PAGE_BG)

        # Centrage
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 420) // 2
        y = (self.winfo_screenheight() - 540) // 2
        self.geometry(f"420x540+{x}+{y}")

        self._build()

    def _build(self):
        # ── Bandeau haut ──────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=G900, height=170, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="🍃", font=("Arial", 44)).pack(pady=(22, 0))
        ctk.CTkLabel(top, text="BUDGET WISE",
                     font=("Arial", 18, "bold"),
                     text_color=ACCENT_GREEN).pack()
        ctk.CTkLabel(top, text="Gestion de Budget Personnelle",
                     font=("Arial", 10), text_color="#4a9468").pack(pady=(2, 0))

        # ── Carte formulaire ──────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=20,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(card, text="Entrez votre mot de passe",
                     font=("Arial", 15, "bold"),
                     text_color=TEXT_PRIMARY).pack(pady=(24, 4))
        ctk.CTkLabel(card, text="Application protégée par mot de passe",
                     font=("Arial", 10), text_color=TEXT_MUTED).pack(pady=(0, 22))

        # Champ mot de passe + œil
        mdp_row = ctk.CTkFrame(card, fg_color="transparent")
        mdp_row.pack(fill="x", padx=24)

        self.entry_mdp = ctk.CTkEntry(
            mdp_row, placeholder_text="Mot de passe",
            height=46, corner_radius=10,
            border_color=BORDER_COLOR, fg_color=G50,
            font=("Arial", 14), show="•")
        self.entry_mdp.pack(side="left", fill="x", expand=True)
        self.entry_mdp.focus()

        self._show = False
        self.btn_eye = ctk.CTkButton(
            mdp_row, text="👁", width=46, height=46,
            fg_color=G50, hover_color=G100,
            text_color=G600, corner_radius=10,
            border_width=1, border_color=BORDER_COLOR,
            command=self._toggle)
        self.btn_eye.pack(side="left", padx=(6, 0))

        # Erreur + tentatives
        self.lbl_err = ctk.CTkLabel(card, text="",
                                     font=("Arial", 11, "bold"),
                                     text_color=DANGER)
        self.lbl_err.pack(pady=(10, 0))

        self.lbl_tent = ctk.CTkLabel(card, text="",
                                      font=("Arial", 10), text_color=TEXT_MUTED)
        self.lbl_tent.pack(pady=(2, 0))

        # Bouton
        self.btn_ok = ctk.CTkButton(
            card, text="  DÉVERROUILLER  🔓",
            fg_color=G500, hover_color=G700,
            text_color="white", height=48,
            font=("Arial", 14, "bold"), corner_radius=12,
            command=self._valider)
        self.btn_ok.pack(fill="x", padx=24, pady=(18, 0))

        # Raccourci clavier
        self.entry_mdp.bind("<Return>", lambda e: self._valider())

        # Indication mot de passe par défaut (première utilisation)
        if not os.path.exists(CONFIG_FILE):
            hint = ctk.CTkFrame(card, fg_color=G50, corner_radius=8,
                                border_width=1, border_color=G100)
            hint.pack(fill="x", padx=24, pady=(14, 0))
            ctk.CTkLabel(hint,
                         text="💡  Premier lancement — mot de passe par défaut : 1234",
                         font=("Arial", 10), text_color=TEXT_MUTED).pack(pady=8)

        # Date
        ctk.CTkLabel(card,
                     text=f"📅  {_date.today().strftime('%d/%m/%Y')}",
                     font=("Arial", 10), text_color=TEXT_MUTED).pack(
            side="bottom", pady=10)

    def _toggle(self):
        self._show = not self._show
        self.entry_mdp.configure(show="" if self._show else "•")
        self.btn_eye.configure(text="🙈" if self._show else "👁")

    def _valider(self):
        pwd = self.entry_mdp.get()
        if not pwd:
            self.lbl_err.configure(text="⚠  Saisissez votre mot de passe.")
            return

        if verifier_mot_de_passe(pwd):
            self.lbl_err.configure(text="✅  Accès autorisé !", text_color=G600)
            self.btn_ok.configure(state="disabled")
            self.after(500, lambda: (self.destroy(), self.on_success()))
        else:
            self.tentatives += 1
            restants = self.MAX_TENT - self.tentatives
            self.entry_mdp.delete(0, "end")

            if restants <= 0:
                self.lbl_err.configure(text="🔒  Application verrouillée.")
                self.btn_ok.configure(state="disabled", fg_color="#9ca3af")
                self.lbl_tent.configure(text="Relancez l'application pour réessayer.")
            else:
                self.lbl_err.configure(text="❌  Mot de passe incorrect.")
                self.lbl_tent.configure(
                    text=f"Tentative {self.tentatives}/{self.MAX_TENT} "
                         f"— {restants} essai(s) restant(s)")


# ══════════════════════════════════════════════════════════════════
#  WIDGET CHANGEMENT DE MOT DE PASSE (dans Paramètres)
# ══════════════════════════════════════════════════════════════════
def creer_widget_changement_mdp(parent, card_builder, section_title_fn,
                                 G50=G50, BORDER_COLOR=BORDER_COLOR,
                                 G400=G400, G500=G500, G600=G600,
                                 G700=G700, TEXT_MUTED=TEXT_MUTED,
                                 TEXT_PRIMARY=TEXT_PRIMARY,
                                 DANGER=DANGER):
    """
    Crée la carte de changement de mot de passe à intégrer dans la page Paramètres.
    Retourne le frame créé.
    """
    mdp_card = card_builder(parent)
    mdp_card.pack(fill="x", pady=(0, 14))
    section_title_fn(mdp_card, "🔑  Changer le mot de passe", pady=(16, 8))

    def _lbl(t):
        ctk.CTkLabel(mdp_card, text=t, font=("Arial", 11, "bold"),
                     text_color=G600).pack(anchor="w", padx=22)

    _lbl("Mot de passe actuel")
    e_ancien = ctk.CTkEntry(mdp_card, height=36, show="•",
                             fg_color=G50, border_color=BORDER_COLOR,
                             placeholder_text="Mot de passe actuel")
    e_ancien.pack(fill="x", padx=22, pady=(2, 12))

    _lbl("Nouveau mot de passe")
    e_nouveau = ctk.CTkEntry(mdp_card, height=36, show="•",
                              fg_color=G50, border_color=BORDER_COLOR,
                              placeholder_text="Min. 4 caractères")
    e_nouveau.pack(fill="x", padx=22, pady=(2, 12))

    _lbl("Confirmer le nouveau")
    e_confirm = ctk.CTkEntry(mdp_card, height=36, show="•",
                              fg_color=G50, border_color=BORDER_COLOR,
                              placeholder_text="Répétez le nouveau mot de passe")
    e_confirm.pack(fill="x", padx=22, pady=(2, 12))

    lbl_status = ctk.CTkLabel(mdp_card, text="",
                               font=("Arial", 11, "bold"), text_color=DANGER)
    lbl_status.pack(pady=(0, 4))

    def _changer():
        anc = e_ancien.get()
        nv  = e_nouveau.get()
        cf  = e_confirm.get()
        lbl_status.configure(text="", text_color=DANGER)

        if not anc or not nv or not cf:
            lbl_status.configure(text="⚠  Tous les champs sont requis."); return
        if nv != cf:
            lbl_status.configure(text="⚠  Les nouveaux mots de passe ne correspondent pas."); return

        ok, msg = changer_mot_de_passe(anc, nv)
        if ok:
            lbl_status.configure(text=f"✅  {msg}", text_color=G600)
            for e in [e_ancien, e_nouveau, e_confirm]:
                e.delete(0, "end")
        else:
            lbl_status.configure(text=f"❌  {msg}")

    ctk.CTkButton(mdp_card, text="🔑  CHANGER LE MOT DE PASSE",
                  fg_color=G500, hover_color=G700,
                  text_color="white", height=42,
                  font=("Arial", 13, "bold"), corner_radius=10,
                  command=_changer).pack(fill="x", padx=22, pady=(0, 20))

    return mdp_card