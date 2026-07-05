import tkinter as tk
import customtkinter as ctk
from tkcalendar import DateEntry
from model import BudgetModel
import math
from datetime import date as _date, datetime
from tkinter import messagebox
import subprocess, sys, os, tempfile
from auth import LoginWindow, creer_widget_changement_mdp

# ── Palette verte économique ───────────────────────────────────────
G50   = "#f0faf4"
G100  = "#d6f0e0"
G200  = "#aadfc2"
G400  = "#4db882"
G500  = "#2ea065"
G600  = "#1d7a4a"
G700  = "#155c38"
G800  = "#0e3f28"
G900  = "#071f14"

SIDEBAR_BG   = G900
ACCENT_GREEN = "#b5e48c"
PAGE_BG      = "#f7fdf9"
CARD_BG      = "#ffffff"
BORDER_COLOR = "#d0ead9"
TEXT_PRIMARY = G800
TEXT_MUTED   = "#8abfa4"
DANGER       = "#ef4444"
WARNING      = "#f59e0b"
BLUE         = "#3b82f6"
NOMS_MOIS    = ["Janvier","Février","Mars","Avril","Mai","Juin",
                "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
NOMS_COURTS  = ["Jan","Fév","Mar","Avr","Mai","Jun",
                "Jul","Aoû","Sep","Oct","Nov","Déc"]
# ──────────────────────────────────────────────────────────────────


class BudgetApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.model = BudgetModel()
        self.title("Budget Wise - Gestion de Budget")
        self.geometry("1280x900")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=PAGE_BG)

        auj = _date.today()
        self.pages              = {}
        self.menu_buttons       = {}
        self._id_budget_en_cours  = None
        self._id_transac_en_cours = None
        self.mois_actif  = auj.month
        self.annee_actif = auj.year

        # ── SIDEBAR ──────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0,
                                    fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 4))
        ctk.CTkLabel(logo_frame, text="BW 🍃", font=("Arial", 22, "bold"),
                     text_color=ACCENT_GREEN).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="BUDGET WISE", font=("Arial", 9),
                     text_color="#4a9468").pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1a3828").pack(
            fill="x", padx=16, pady=(8, 16))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True, padx=24, pady=24)

        icons = {"dashboard":"🗂","transactions":"↔","budgets":"💼",
                 "objectifs":"📊","parametres":"⚙"}
        items = [("Tableau de Bord","dashboard"),("Transactions","transactions"),
                 ("Budgets","budgets"),("Statistiques","objectifs"),("Paramètres","parametres")]
        for text, pid in items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icons[pid]}  {text}",
                fg_color="transparent", text_color="#8abfa4",
                hover_color="#1a3828", anchor="w", height=40,
                corner_radius=10, font=("Arial", 13),
                command=lambda p=pid: self.afficher_page(p))
            btn.pack(fill="x", padx=10, pady=2)
            self.menu_buttons[pid] = btn

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1a3828").pack(
            fill="x", padx=16, pady=(16, 8), side="bottom")
        badge = ctk.CTkFrame(self.sidebar, fg_color="#0e3020",
                              corner_radius=10, border_width=1, border_color="#1d7a4a")
        badge.pack(fill="x", padx=14, pady=(0, 16), side="bottom")
        ctk.CTkLabel(badge, text="PÉRIODE ACTIVE", font=("Arial", 9),
                     text_color="#4a9468").pack(pady=(8, 0))
        self.lbl_badge_mois = ctk.CTkLabel(badge, text="", font=("Arial", 12, "bold"),
                                           text_color=ACCENT_GREEN)
        self.lbl_badge_mois.pack(pady=(2, 8))

        self.creer_page_dashboard()
        self.creer_page_transactions()
        self.creer_page_budgets()
        self.creer_page_objectifs()
        self.creer_page_parametres()
        self.afficher_page("dashboard")

    # ──────────────────────────────────────────────
    #  NAVIGATION
    # ──────────────────────────────────────────────
    def afficher_page(self, pid):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[pid].pack(fill="both", expand=True)
        for p_id, btn in self.menu_buttons.items():
            btn.configure(fg_color=G700 if p_id==pid else "transparent",
                          text_color=ACCENT_GREEN if p_id==pid else "#8abfa4",
                          font=("Arial",13,"bold") if p_id==pid else ("Arial",13))
        if pid == "parametres": self.charger_config_parametres()
        if pid == "objectifs":  self.actualiser_page_statistiques()
        if pid == "budgets":    self.actualiser_liste_budgets(); self.actualiser_fond_caisse()
        if pid == "dashboard":
            self.actualiser_statistiques()
            self.actualiser_barres_budget()
            self.remplir_tableau_dashboard()
            self.label_titre_dashboard.configure(
                text=f"Tableau de Bord — {NOMS_MOIS[self.mois_actif-1]} {self.annee_actif}")
        self._maj_badge_mois()

    def _maj_badge_mois(self):
        self.lbl_badge_mois.configure(
            text=f"{NOMS_MOIS[self.mois_actif-1]} {self.annee_actif}")

    # ──────────────────────────────────────────────
    #  HELPERS UI
    # ──────────────────────────────────────────────
    def _card(self, parent, **kw):
        d = dict(fg_color=CARD_BG, corner_radius=14,
                 border_width=1, border_color=BORDER_COLOR)
        d.update(kw)
        return ctk.CTkFrame(parent, **d)

    def _section_title(self, parent, text, pady=(0,12)):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=pady)
        ctk.CTkLabel(f, text=text, font=("Arial",14,"bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkFrame(f, height=2, fg_color=G400, corner_radius=2,
                     width=32).pack(side="left", padx=(10,0), pady=(4,0))

    def _table_headers(self, frame, headers, uniform="col"):
        """Insère une ligne d'en-têtes en row=0 et un séparateur en row=1."""
        n = len(headers)
        for i in range(n):
            frame.grid_columnconfigure(i, weight=1, uniform=uniform)
        for ci, h in enumerate(headers):
            ctk.CTkLabel(frame, text=h, font=("Arial",9,"bold"),
                         text_color=TEXT_MUTED, fg_color=G50,
                         anchor="w").grid(row=0, column=ci, sticky="nsew",
                                          ipadx=10, ipady=7)
        ctk.CTkFrame(frame, height=1, fg_color=BORDER_COLOR).grid(
            row=1, column=0, columnspan=n, sticky="ew")
        return 2  # première ligne de données

    # ──────────────────────────────────────────────
    #  BARRE FILTRE DATE (réutilisable)
    # ──────────────────────────────────────────────
    def _barre_filtre(self, parent, on_filtrer, on_imprimer, on_reset=None):
        """
        Crée une barre de filtre par date avec validation, bouton Filtrer,
        bouton Réinitialiser et bouton Imprimer.
        Retourne (entry_debut, entry_fin, label_erreur).
        """
        bar = self._card(parent, fg_color=G50, corner_radius=10)
        bar.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(inner, text="🔍  Filtrer par période :",
                     font=("Arial",12,"bold"), text_color=G700).pack(side="left", padx=(0,12))

        ctk.CTkLabel(inner, text="Du", font=("Arial",11),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=(0,4))
        e_debut = DateEntry(inner, width=11, background=G800,
                            foreground="white", date_pattern="yyyy-mm-dd",
                            borderwidth=1)
        e_debut.pack(side="left", padx=(0,10))

        ctk.CTkLabel(inner, text="Au", font=("Arial",11),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=(0,4))
        e_fin = DateEntry(inner, width=11, background=G800,
                          foreground="white", date_pattern="yyyy-mm-dd",
                          borderwidth=1)
        e_fin.pack(side="left", padx=(0,16))

        # Label erreur
        lbl_err = ctk.CTkLabel(inner, text="", font=("Arial",10,"bold"),
                                text_color=DANGER, fg_color="transparent")
        lbl_err.pack(side="left", padx=(0,10))

        # Boutons à droite
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(btn_frame, text="🖨  Imprimer", width=110, height=32,
                      fg_color=G600, hover_color=G800, corner_radius=8,
                      font=("Arial",11,"bold"),
                      command=on_imprimer).pack(side="right", padx=(6,0))

        if on_reset:
            ctk.CTkButton(btn_frame, text="↺  Réinitialiser", width=120, height=32,
                          fg_color="#6b7280", hover_color="#4b5563",
                          corner_radius=8, font=("Arial",11),
                          command=on_reset).pack(side="right", padx=(6,0))

        ctk.CTkButton(btn_frame, text="▶  Filtrer", width=100, height=32,
                      fg_color=G500, hover_color=G700, corner_radius=8,
                      font=("Arial",11,"bold"),
                      command=on_filtrer).pack(side="right", padx=(0,6))

        return e_debut, e_fin, lbl_err

    def _valider_dates(self, e_debut, e_fin, lbl_err):
        """
        Valide que la date de début ≤ date de fin.
        Retourne (date_debut_str, date_fin_str) ou (None, None) si erreur.
        """
        lbl_err.configure(text="")
        try:
            d_debut = e_debut.get_date()
            d_fin   = e_fin.get_date()
        except Exception:
            lbl_err.configure(text="⚠  Dates invalides")
            return None, None
        if d_debut > d_fin:
            lbl_err.configure(text="⚠  La date de début doit être ≤ à la date de fin")
            return None, None
        if d_fin > _date.today():
            lbl_err.configure(text="⚠  La date de fin ne peut pas être dans le futur")
            return None, None
        return d_debut.strftime("%Y-%m-%d"), d_fin.strftime("%Y-%m-%d")

    # ──────────────────────────────────────────────
    #  IMPRESSION (génère un rapport texte / HTML)
    # ──────────────────────────────────────────────
    def _imprimer_rapport(self, titre, colonnes, lignes, periode=""):
        """Génère un fichier HTML et l'ouvre dans le navigateur pour impression."""
        try:
            rows_html = ""
            for i, ligne in enumerate(lignes):
                bg = "#f0faf4" if i % 2 == 0 else "#ffffff"
                cells = "".join(f"<td>{v}</td>" for v in ligne)
                rows_html += f'<tr style="background:{bg}">{cells}</tr>'

            headers_html = "".join(f"<th>{c}</th>" for c in colonnes)
            periode_html = f"<p style='color:#8abfa4;font-size:13px'>{periode}</p>" if periode else ""

            html = f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8">
<title>{titre}</title>
<style>
  body{{font-family:Arial,sans-serif;margin:30px;color:#0e3f28;background:#f7fdf9}}
  h1{{color:#071f14;border-bottom:3px solid #4db882;padding-bottom:8px}}
  table{{width:100%;border-collapse:collapse;margin-top:16px;font-size:13px}}
  th{{background:#1d7a4a;color:white;padding:10px 12px;text-align:left}}
  td{{padding:8px 12px;border-bottom:1px solid #d0ead9}}
  .footer{{margin-top:20px;font-size:11px;color:#8abfa4;text-align:right}}
  @media print{{body{{margin:10px}}}}
</style></head><body>
<h1>🍃 Budget Wise — {titre}</h1>
{periode_html}
<table><thead><tr>{headers_html}</tr></thead>
<tbody>{rows_html}</tbody></table>
<div class="footer">Imprimé le {_date.today().strftime('%d/%m/%Y')} — Budget Wise</div>
<script>window.onload=function(){{window.print()}}</script>
</body></html>"""

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html",
                                              mode="w", encoding="utf-8")
            tmp.write(html)
            tmp.close()
            if sys.platform == "win32":
                os.startfile(tmp.name)
            elif sys.platform == "darwin":
                subprocess.run(["open", tmp.name])
            else:
                subprocess.run(["xdg-open", tmp.name])
        except Exception as e:
            messagebox.showerror("Erreur impression", str(e))

    # ══════════════════════════════════════════════
    #  PAGE DASHBOARD
    # ══════════════════════════════════════════════
    def creer_page_dashboard(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["dashboard"] = page
        auj = _date.today()

        # En-tête
        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,12))
        self.label_titre_dashboard = ctk.CTkLabel(
            hdr, text=f"Tableau de Bord — {NOMS_MOIS[auj.month-1]} {auj.year}",
            font=("Arial",22,"bold"), text_color=TEXT_PRIMARY)
        self.label_titre_dashboard.pack(side="left")
        ctk.CTkLabel(hdr, text="Vue d'ensemble de votre activité",
                     font=("Arial",12), text_color=TEXT_MUTED).pack(
            side="left", padx=(12,0), pady=(6,0))

        # ── Barre filtre dashboard ────────────────────────────────
        self.dash_e_debut, self.dash_e_fin, self.dash_lbl_err = \
            self._barre_filtre(page,
                on_filtrer=self._filtrer_dashboard,
                on_imprimer=self._imprimer_dashboard,
                on_reset=self._reset_dashboard)

        # ── KPI cards ─────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0,12))
        self.stats_frame.grid_columnconfigure((0,1,2), weight=1)

        self.label_revenus  = self._kpi_card(f"Total Recettes — {NOMS_MOIS[auj.month-1]} {auj.year}",
                                              "0 FCFA", 0, G400, "↑")
        self.label_depenses = self._kpi_card(f"Total Dépenses — {NOMS_MOIS[auj.month-1]} {auj.year}",
                                              "0 FCFA", 1, DANGER, "↓")
        self.label_solde    = self._kpi_card("Solde de l'Exercice",
                                              "0 FCFA", 2, BLUE, "⚖")

        # ── Progrès budgets ───────────────────────────────────────
        prog_card = self._card(page)
        prog_card.pack(fill="x", pady=(0,12))
        self._section_title(prog_card, "Progrès du Budget", pady=(14,8))
        self.frame_barres_scroll = ctk.CTkScrollableFrame(
            prog_card, fg_color="transparent", height=170)
        self.frame_barres_scroll.pack(fill="both", expand=True, padx=16, pady=(0,12))

        # ── Transactions récentes ─────────────────────────────────
        tx_card = self._card(page)
        tx_card.pack(fill="both", expand=True)
        self._section_title(tx_card, "Transactions Récentes", pady=(14,8))

        self.container_table_dashboard = ctk.CTkScrollableFrame(
            tx_card, fg_color="transparent", height=180)
        self.container_table_dashboard.pack(fill="both", expand=True,
                                            padx=16, pady=(0,14))

        self.actualiser_statistiques()
        self.actualiser_barres_budget()
        self.remplir_tableau_dashboard()

    def _kpi_card(self, titre, valeur, col, accent, icon):
        card = self._card(self.stats_frame, height=96)
        card.grid(row=0, column=col, padx=6, sticky="ew")
        card.grid_propagate(False)
        ctk.CTkFrame(card, height=3, fg_color=accent,
                     corner_radius=0).pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=8)
        ctk.CTkLabel(inner, text=titre, font=("Arial",10),
                     text_color=TEXT_MUTED).pack(anchor="w")
        lbl = ctk.CTkLabel(inner, text=valeur, font=("Arial",18,"bold"),
                           text_color=TEXT_PRIMARY)
        lbl.pack(anchor="w", pady=(2,0))
        ctk.CTkLabel(card, text=icon, font=("Arial",22),
                     text_color=accent, fg_color="transparent").place(
            relx=0.93, rely=0.62, anchor="center")
        return lbl

    # Couleurs catégories
    COULEUR_PAR_CAT = {
        "Alimentation":"#f59e0b","Transport":"#3b82f6",
        "Loyer":"#8b5cf6","Loisirs":"#1abc9c",
        "Report Mois Précédent":"#8abfa4",
    }
    COULEURS_DEFAUT = [DANGER, G400, WARNING, "#e91e63","#16a085"]

    def _couleur_cat(self, nom, i=0):
        return self.COULEUR_PAR_CAT.get(nom,
               self.COULEURS_DEFAUT[i % len(self.COULEURS_DEFAUT)])

    def actualiser_barres_budget(self):
        for w in self.frame_barres_scroll.winfo_children(): w.destroy()
        budgets = self.model.recuperer_suivi_budgets(self.annee_actif, self.mois_actif)
        if not budgets:
            ctk.CTkLabel(self.frame_barres_scroll,
                         text="Aucun budget défini. Allez dans 'Budgets' pour en créer.",
                         text_color=TEXT_MUTED, font=("Arial",11)).pack(pady=20)
            return
        for item in budgets:
            limite  = float(item['montant_limite'])
            depense = float(item['total_depense']) if item['total_depense'] else 0.0
            ratio   = depense/limite if limite>0 else 0
            pct     = int(ratio*100)
            bc      = self.COULEUR_PAR_CAT.get(item['nom_cat'], TEXT_MUTED)
            dep     = ratio>1.0; att = 0.8<=ratio<=1.0
            color   = DANGER if dep else (WARNING if att else G400)

            fr = ctk.CTkFrame(self.frame_barres_scroll, fg_color="transparent")
            fr.pack(fill="x", pady=5)
            top = ctk.CTkFrame(fr, fg_color="transparent"); top.pack(fill="x")
            dot = tk.Canvas(top, width=8, height=8, bg=PAGE_BG, highlightthickness=0)
            dot.pack(side="left", padx=(0,6), pady=5)
            dot.create_oval(0,0,8,8, fill=bc, outline="")
            ctk.CTkLabel(top, text=item['nom_cat'], font=("Arial",12,"bold"),
                         text_color=TEXT_PRIMARY).pack(side="left")
            rg = ctk.CTkFrame(top, fg_color="transparent"); rg.pack(side="right")
            ctk.CTkLabel(rg, text=f"{int(depense):,} / {int(limite):,} FCFA",
                         font=("Arial",10), text_color=TEXT_MUTED).pack(side="left", padx=(0,8))
            pc = DANGER if dep else (WARNING if att else G600)
            pb2= "#fef2f2" if dep else ("#fffbeb" if att else G50)
            ctk.CTkLabel(rg, text=f"{pct}%", font=("Arial",10,"bold"),
                         text_color=pc, fg_color=pb2,
                         corner_radius=5, width=38).pack(side="left")
            pb = ctk.CTkProgressBar(fr, progress_color=color,
                                    fg_color=G100, height=6, corner_radius=99)
            pb.pack(fill="x", pady=(4,0)); pb.set(min(ratio,1.0))
            if dep:
                ctk.CTkLabel(fr, text=f"⛔  Budget dépassé — excédent : {int(depense-limite):,} FCFA",
                             font=("Arial",9,"bold"), text_color=DANGER).pack(anchor="w", pady=(3,0))
            elif att:
                ctk.CTkLabel(fr, text="⚠  Budget presque atteint",
                             font=("Arial",9), text_color=WARNING).pack(anchor="w", pady=(3,0))

    def actualiser_statistiques(self):
        try:
            stats = self.model.recuperer_statistiques_mensuelles(self.mois_actif, self.annee_actif)
            nm = NOMS_MOIS[self.mois_actif-1]
            self.label_revenus.master.winfo_children()[0].configure(
                text=f"Total Recettes — {nm} {self.annee_actif}")
            self.label_depenses.master.winfo_children()[0].configure(
                text=f"Total Dépenses — {nm} {self.annee_actif}")
            self.label_revenus.configure(
                text=f"{stats.get('revenus',0):,.0f} FCFA", text_color=G600)
            self.label_depenses.configure(
                text=f"{stats.get('depenses',0):,.0f} FCFA", text_color=DANGER)
            s = stats.get('solde',0)
            self.label_solde.configure(
                text=f"{s:,.0f} FCFA", text_color=G600 if s>=0 else DANGER)
        except Exception as e:
            print(f"Erreur stats: {e}")

    def remplir_tableau_dashboard(self, transactions=None):
        for w in self.container_table_dashboard.winfo_children(): w.destroy()
        dr = self._table_headers(self.container_table_dashboard,
                                 ["DATE","CATÉGORIE","DESCRIPTION","TYPE","MONTANT"])
        if transactions is None:
            transactions = self.model.recuperer_transactions_recentes(
                limite=10, mois=self.mois_actif, annee=self.annee_actif)
        for idx, row in enumerate(transactions):
            ri = idx + dr
            rec   = row.get('type_flux') == "RECETTE"
            color = G600 if rec else DANGER
            rbg   = G50 if idx%2==0 else CARD_BG
            kw    = dict(fg_color=rbg, anchor="w")
            ctk.CTkLabel(self.container_table_dashboard,
                         text=str(row.get('date_op','N/A')),
                         font=("Arial",11), text_color=TEXT_MUTED, **kw).grid(
                row=ri, column=0, sticky="nsew", ipadx=8, ipady=5)
            ctk.CTkLabel(self.container_table_dashboard,
                         text=row.get('nom_cat','N/A'),
                         font=("Arial",11,"bold"), text_color=TEXT_PRIMARY, **kw).grid(
                row=ri, column=1, sticky="nsew", ipadx=8, ipady=5)
            ctk.CTkLabel(self.container_table_dashboard,
                         text=row.get('libelle','N/A'),
                         font=("Arial",11), text_color=TEXT_PRIMARY, **kw).grid(
                row=ri, column=2, sticky="nsew", ipadx=8, ipady=5)
            ctk.CTkLabel(self.container_table_dashboard,
                         text=row.get('type_flux','N/A'),
                         font=("Arial",10,"bold"), text_color=color,
                         fg_color=G50 if rec else "#fef2f2",
                         corner_radius=6, width=70, anchor="w").grid(
                row=ri, column=3, sticky="nsew", ipadx=8, ipady=5)
            ctk.CTkLabel(self.container_table_dashboard,
                         text=f"{row.get('montant',0):,.0f} FCFA",
                         font=("Arial",12,"bold"), text_color=color, **kw).grid(
                row=ri, column=4, sticky="nsew", ipadx=8, ipady=5)

    # ── Filtre dashboard ──────────────────────────
    def _filtrer_dashboard(self):
        d_deb, d_fin = self._valider_dates(
            self.dash_e_debut, self.dash_e_fin, self.dash_lbl_err)
        if not d_deb: return
        txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
        self.remplir_tableau_dashboard(transactions=txs)
        # Stats filtrées
        revenus  = sum(float(r['montant']) for r in txs if r.get('type_flux')=='RECETTE')
        depenses = sum(float(r['montant']) for r in txs if r.get('type_flux')=='DEPENSE')
        solde    = revenus - depenses
        self.label_revenus.configure(text=f"{revenus:,.0f} FCFA", text_color=G600)
        self.label_depenses.configure(text=f"{depenses:,.0f} FCFA", text_color=DANGER)
        self.label_solde.configure(text=f"{solde:,.0f} FCFA",
                                   text_color=G600 if solde>=0 else DANGER)
        self.dash_lbl_err.configure(
            text=f"✅  {len(txs)} transaction(s) trouvée(s)",
            text_color=G600)

    def _reset_dashboard(self):
        self.dash_lbl_err.configure(text="")
        self.actualiser_statistiques()
        self.remplir_tableau_dashboard()

    def _imprimer_dashboard(self):
        d_deb, d_fin = self._valider_dates(
            self.dash_e_debut, self.dash_e_fin, self.dash_lbl_err)
        if not d_deb:
            # si pas de filtre actif, on imprime tout le mois
            txs = self.model.recuperer_transactions_recentes(
                limite=200, mois=self.mois_actif, annee=self.annee_actif)
            periode = f"Période : {NOMS_MOIS[self.mois_actif-1]} {self.annee_actif}"
        else:
            txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
            periode = f"Période : du {d_deb} au {d_fin}"
        lignes = [(str(r.get('date_op','')), r.get('nom_cat',''),
                   r.get('libelle',''), r.get('type_flux',''),
                   f"{r.get('montant',0):,.0f} FCFA") for r in txs]
        self._imprimer_rapport("Tableau de Bord",
                               ["Date","Catégorie","Description","Type","Montant"],
                               lignes, periode)

    # Méthode compat
    def creer_carte_stat(self, titre, valeur, col):
        return self._kpi_card(titre, valeur, col, G400, "")

    # ══════════════════════════════════════════════
    #  PAGE TRANSACTIONS
    # ══════════════════════════════════════════════
    def creer_page_transactions(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["transactions"] = page

        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(hdr, text="Gestion des Transactions",
                     font=("Arial",22,"bold"), text_color=TEXT_PRIMARY).pack(side="left")

        # ── Barre filtre ──────────────────────────────────────────
        self.tx_e_debut, self.tx_e_fin, self.tx_lbl_err = \
            self._barre_filtre(page,
                on_filtrer=self._filtrer_transactions,
                on_imprimer=self._imprimer_transactions,
                on_reset=self._reset_transactions)

        split = ctk.CTkFrame(page, fg_color="transparent")
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=1)
        split.grid_columnconfigure(1, weight=2)

        # ── Formulaire ────────────────────────────────────────────
        form_card = self._card(split)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        self._section_title(form_card, "Nouvelle opération", pady=(18,14))

        def _lbl(p, t):
            ctk.CTkLabel(p, text=t, font=("Arial",11,"bold"),
                         text_color=G600).pack(anchor="w", padx=22)

        _lbl(form_card, "Date")
        self.entry_date = DateEntry(form_card, width=12, background=G800,
                                    date_pattern='yyyy-mm-dd',
                                    foreground='white', borderwidth=2)
        self.entry_date.pack(fill="x", padx=22, pady=(2,12))

        _lbl(form_card, "Description")
        self.entry_libelle = ctk.CTkEntry(form_card, placeholder_text="Ex: Achat Parfum",
                                          height=36, border_color=BORDER_COLOR, fg_color=G50)
        self.entry_libelle.pack(fill="x", padx=22, pady=(2,12))

        _lbl(form_card, "Montant (FCFA)")
        self.entry_montant = ctk.CTkEntry(form_card, placeholder_text="Ex: 5000",
                                          height=36, border_color=BORDER_COLOR, fg_color=G50)
        self.entry_montant.pack(fill="x", padx=22, pady=(2,12))

        _lbl(form_card, "Type")
        self.combo_type = ctk.CTkComboBox(form_card, values=["DEPENSE","RECETTE"],
                                          height=36, border_color=BORDER_COLOR, fg_color=G50,
                                          button_color=G400, button_hover_color=G600)
        self.combo_type.pack(fill="x", padx=22, pady=(2,12))

        _lbl(form_card, "Catégorie")
        self.combo_cat = ctk.CTkComboBox(
            form_card,
            values=["Salaire","Vente","Loyer","Alimentation","Transport","Loisirs"],
            height=36, border_color=BORDER_COLOR, fg_color=G50,
            button_color=G400, button_hover_color=G600)
        self.combo_cat.pack(fill="x", padx=22, pady=(2,20))

        self.btn_enregistrer_transac = ctk.CTkButton(
            form_card, text="✚  ENREGISTRER", fg_color=G500, hover_color=G700,
            text_color="white", height=42, font=("Arial",13,"bold"),
            corner_radius=10, command=self.enregistrer_transaction)
        self.btn_enregistrer_transac.pack(fill="x", padx=22, pady=(0,10))

        # Bouton vider historique
        ctk.CTkButton(
            form_card, text="🗑  Vider l'historique complet",
            fg_color="#dc2626", hover_color="#991b1b",
            text_color="white", height=36, font=("Arial",11),
            corner_radius=10, command=self._vider_historique
        ).pack(fill="x", padx=22, pady=(0,20))

        # ── Historique ────────────────────────────────────────────
        hist_card = self._card(split)
        hist_card.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        self._section_title(hist_card, "Historique complet", pady=(18,8))

        self.container_table_transac = ctk.CTkScrollableFrame(
            hist_card, fg_color="transparent")
        self.container_table_transac.pack(fill="both", expand=True,
                                          padx=14, pady=(0,14))
        self.remplir_tableau_transactions_complet()

    def enregistrer_transaction(self):
        libelle = self.entry_libelle.get().strip()
        montant = self.entry_montant.get().strip()
        cat_nom = self.combo_cat.get()
        date_obj = self.entry_date.get_date()
        date_val = date_obj.strftime('%Y-%m-%d')
        annee_id = date_obj.year
        cats = {"Salaire":1,"Vente":2,"Loyer":3,"Alimentation":4,"Transport":5,"Loisirs":6}
        id_cat = cats.get(cat_nom, 4)
        if not libelle or not montant:
            messagebox.showwarning("Champs manquants", "Veuillez remplir la description et le montant.")
            return
        try:
            montant_f = float(montant)
            if montant_f <= 0:
                messagebox.showwarning("Montant invalide", "Le montant doit être supérieur à 0.")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit être un nombre valide.")
            return
        try:
            if self._id_transac_en_cours:
                self.model.modifier_transaction_bdd(
                    self._id_transac_en_cours, libelle, montant_f, date_val, id_cat)
                self._id_transac_en_cours = None
                self.btn_enregistrer_transac.configure(
                    text="✚  ENREGISTRER", fg_color=G500, hover_color=G700)
            else:
                self.model.ajouter_transaction_bdd(
                    libelle, montant_f, date_val, id_cat, 1, annee_id)
            self.entry_libelle.delete(0,'end')
            self.entry_montant.delete(0,'end')
            self.remplir_tableau_transactions_complet()
            self.actualiser_statistiques()
            self.actualiser_barres_budget()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def remplir_tableau_transactions_complet(self, transactions=None):
        for w in self.container_table_transac.winfo_children(): w.destroy()
        dr = self._table_headers(self.container_table_transac,
                                 ["DATE","CATÉGORIE","DESCRIPTION","TYPE","MONTANT","ACTIONS"],
                                 uniform="tcol")
        if transactions is None:
            transactions = self.model.recuperer_transactions_recentes(limite=200)
        for idx, row in enumerate(transactions):
            ri  = idx + dr
            rec = row.get('type_flux') == "RECETTE"
            col = G600 if rec else DANGER
            rbg = G50 if idx%2==0 else CARD_BG
            kw  = dict(fg_color=rbg, anchor="w")
            ctk.CTkLabel(self.container_table_transac,
                         text=str(row.get('date_op','N/A')),
                         font=("Arial",11), text_color=TEXT_MUTED, **kw).grid(
                row=ri, column=0, sticky="nsew", ipadx=10, ipady=5)
            ctk.CTkLabel(self.container_table_transac,
                         text=row.get('nom_cat','N/A'),
                         font=("Arial",11,"bold"), text_color=TEXT_PRIMARY, **kw).grid(
                row=ri, column=1, sticky="nsew", ipadx=10, ipady=5)
            ctk.CTkLabel(self.container_table_transac,
                         text=row.get('libelle','N/A'),
                         font=("Arial",11), text_color=TEXT_PRIMARY, **kw).grid(
                row=ri, column=2, sticky="nsew", ipadx=10, ipady=5)
            ctk.CTkLabel(self.container_table_transac,
                         text=row.get('type_flux','N/A'),
                         font=("Arial",10,"bold"), text_color=col,
                         fg_color=G50 if rec else "#fef2f2",
                         corner_radius=6, width=68, anchor="w").grid(
                row=ri, column=3, sticky="nsew", ipadx=10, ipady=5)
            ctk.CTkLabel(self.container_table_transac,
                         text=f"{row.get('montant',0):,.0f} FCFA",
                         font=("Arial",12,"bold"), text_color=col, **kw).grid(
                row=ri, column=4, sticky="nsew", ipadx=10, ipady=5)
            af = ctk.CTkFrame(self.container_table_transac, fg_color=rbg)
            af.grid(row=ri, column=5, ipadx=6, ipady=3, sticky="nsew")
            ctk.CTkButton(af, text="✏", width=28, height=26,
                          fg_color=WARNING, hover_color="#d97706", corner_radius=6,
                          command=lambda r=row: self.preparer_modification(r)).pack(
                side="left", padx=2)
            ctk.CTkButton(af, text="🗑", width=28, height=26,
                          fg_color=DANGER, hover_color="#dc2626", corner_radius=6,
                          command=lambda id_t=row['id_transac']: self.confirmer_suppression(id_t)).pack(
                side="left", padx=2)

    def confirmer_suppression(self, id_t):
        if messagebox.askyesno("Suppression","Supprimer cette transaction ?"):
            if self.model.supprimer_transaction_bdd(id_t):
                self.remplir_tableau_transactions_complet()
                self.actualiser_statistiques()
                self.actualiser_barres_budget()

    def preparer_modification(self, row):
        self.entry_libelle.delete(0,'end'); self.entry_libelle.insert(0, row['libelle'])
        self.entry_montant.delete(0,'end'); self.entry_montant.insert(0, str(row['montant']))
        self.combo_cat.set(row['nom_cat']); self.combo_type.set(row['type_flux'])
        self._id_transac_en_cours = row['id_transac']
        self.btn_enregistrer_transac.configure(
            text="✏  MODIFIER", fg_color=WARNING, hover_color="#d97706")

    def _vider_historique(self):
        if messagebox.askyesno("⚠  Confirmation",
                               "Voulez-vous vraiment SUPPRIMER TOUTES les transactions ?\n\n"
                               "Cette action est irréversible.", icon="warning"):
            if messagebox.askyesno("Dernière confirmation",
                                   "Êtes-vous absolument certain ?\nToutes les données seront perdues."):
                try:
                    self.model.vider_toutes_transactions()
                    self.remplir_tableau_transactions_complet()
                    self.actualiser_statistiques()
                    self.actualiser_barres_budget()
                    messagebox.showinfo("Succès", "L'historique a été vidé avec succès.")
                except Exception as e:
                    messagebox.showerror("Erreur", str(e))

    def _filtrer_transactions(self):
        d_deb, d_fin = self._valider_dates(
            self.tx_e_debut, self.tx_e_fin, self.tx_lbl_err)
        if not d_deb: return
        txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
        self.remplir_tableau_transactions_complet(transactions=txs)
        self.tx_lbl_err.configure(
            text=f"✅  {len(txs)} transaction(s)", text_color=G600)

    def _reset_transactions(self):
        self.tx_lbl_err.configure(text="")
        self.remplir_tableau_transactions_complet()

    def _imprimer_transactions(self):
        d_deb, d_fin = self._valider_dates(
            self.tx_e_debut, self.tx_e_fin, self.tx_lbl_err)
        if not d_deb:
            txs = self.model.recuperer_transactions_recentes(limite=500)
            periode = "Toutes les transactions"
        else:
            txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
            periode = f"Période : du {d_deb} au {d_fin}"
        lignes = [(str(r.get('date_op','')), r.get('nom_cat',''),
                   r.get('libelle',''), r.get('type_flux',''),
                   f"{r.get('montant',0):,.0f} FCFA") for r in txs]
        self._imprimer_rapport("Transactions",
                               ["Date","Catégorie","Description","Type","Montant"],
                               lignes, periode)

    # ══════════════════════════════════════════════
    #  PAGE BUDGETS
    # ══════════════════════════════════════════════
    def creer_page_budgets(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["budgets"] = page
        ctk.CTkLabel(page, text="Gestion des Budgets",
                     font=("Arial",22,"bold"), text_color=TEXT_PRIMARY).pack(
            anchor="nw", pady=(0,10))

        # ── Barre filtre budgets ───────────────────────────────────
        self.bud_e_debut, self.bud_e_fin, self.bud_lbl_err = \
            self._barre_filtre(page,
                on_filtrer=self._filtrer_budgets,
                on_imprimer=self._imprimer_budgets,
                on_reset=self._reset_budgets)

        # ── Fond de caisse ─────────────────────────────────────────
        caisse_card = self._card(page)
        caisse_card.pack(fill="x", pady=(0,12))
        ctk.CTkLabel(caisse_card, text="💰  Fond de Caisse",
                     font=("Arial",14,"bold"), text_color=TEXT_PRIMARY).pack(
            anchor="w", padx=20, pady=(14,8))
        ci = ctk.CTkFrame(caisse_card, fg_color="transparent")
        ci.pack(fill="x", padx=16, pady=(0,10))
        ci.grid_columnconfigure((0,1,2,3), weight=1)
        self.lbl_caisse_rec  = self._carte_caisse(ci,"Recettes du mois","0 FCFA",0,G600)
        self.lbl_caisse_dep  = self._carte_caisse(ci,"Dépenses du mois","0 FCFA",1,DANGER)
        self.lbl_caisse_exc  = self._carte_caisse(ci,"Hors budget","0 FCFA",2,WARNING)
        self.lbl_caisse_sold = self._carte_caisse(ci,"Solde disponible","0 FCFA",3,BLUE)
        self.frame_detail_exces = ctk.CTkFrame(caisse_card, fg_color="transparent")
        self.frame_detail_exces.pack(fill="x", padx=20, pady=(0,10))

        # ── Split formulaire + liste ───────────────────────────────
        split = ctk.CTkFrame(page, fg_color="transparent")
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=1)
        split.grid_columnconfigure(1, weight=2)

        form_card = self._card(split)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        self._section_title(form_card, "Définir un Budget", pady=(18,14))

        def _lbl(p, t):
            ctk.CTkLabel(p, text=t, font=("Arial",11,"bold"),
                         text_color=G600).pack(anchor="w", padx=22)

        _lbl(form_card, "Catégorie")
        self.combo_cat_budget = ctk.CTkComboBox(
            form_card, values=["Alimentation","Transport","Loyer","Loisirs"],
            height=36, border_color=BORDER_COLOR, fg_color=G50,
            button_color=G400, button_hover_color=G600)
        self.combo_cat_budget.pack(fill="x", padx=22, pady=(2,14))

        _lbl(form_card, "Limite mensuelle (FCFA)")
        self.entry_limite = ctk.CTkEntry(form_card, placeholder_text="Ex: 50000",
                                         height=36, border_color=BORDER_COLOR, fg_color=G50)
        self.entry_limite.pack(fill="x", padx=22, pady=(2,24))

        self.btn_def_budget = ctk.CTkButton(
            form_card, text="✚  DÉFINIR LE BUDGET",
            fg_color=G500, hover_color=G700, text_color="white",
            height=42, font=("Arial",13,"bold"), corner_radius=10,
            command=self.enregistrer_budget)
        self.btn_def_budget.pack(fill="x", padx=22, pady=(0,22))

        list_card = self._card(split)
        list_card.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        self._section_title(list_card, "Suivi des consommations", pady=(18,8))
        self.container_budgets_list = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent")
        self.container_budgets_list.pack(fill="both", expand=True,
                                         padx=12, pady=(0,14))

        self.actualiser_liste_budgets()
        self.actualiser_fond_caisse()

    def _carte_caisse(self, parent, titre, valeur, col, couleur):
        f = ctk.CTkFrame(parent, fg_color=G50, corner_radius=10,
                         border_width=1, border_color=BORDER_COLOR)
        f.grid(row=1, column=col, padx=6, sticky="ew")
        ctk.CTkLabel(f, text=titre, font=("Arial",10),
                     text_color=TEXT_MUTED).pack(pady=(10,0))
        lbl = ctk.CTkLabel(f, text=valeur, font=("Arial",13,"bold"), text_color=couleur)
        lbl.pack(pady=(2,10))
        return lbl

    def actualiser_fond_caisse(self):
        try:
            stats   = self.model.recuperer_statistiques_mensuelles(self.mois_actif, self.annee_actif)
            budgets = self.model.recuperer_suivi_budgets(self.annee_actif, self.mois_actif)
            revenus  = stats.get('revenus',0); depenses = stats.get('depenses',0)
            deps = [{"nom":b['nom_cat'],
                     "exces":(float(b['total_depense']) if b['total_depense'] else 0)-float(b['montant_limite'])}
                    for b in budgets
                    if b['total_depense'] and (float(b['total_depense'])-float(b['montant_limite']))>0]
            hb = sum(d["exces"] for d in deps)
            solde = revenus - depenses
            self.lbl_caisse_rec.configure(text=f"{revenus:,.0f} FCFA")
            self.lbl_caisse_dep.configure(text=f"{depenses:,.0f} FCFA")
            self.lbl_caisse_exc.configure(text=f"{hb:,.0f} FCFA",
                                          text_color=DANGER if hb>0 else WARNING)
            self.lbl_caisse_sold.configure(text=f"{solde:,.0f} FCFA",
                                           text_color=G600 if solde>=0 else DANGER)
            for w in self.frame_detail_exces.winfo_children(): w.destroy()
            if deps:
                ctk.CTkLabel(self.frame_detail_exces, text="Détail des dépassements :",
                             font=("Arial",10,"bold"), text_color=DANGER).pack(
                    anchor="w", padx=5, pady=(4,2))
                for d in deps:
                    ctk.CTkLabel(self.frame_detail_exces,
                                 text=f"  •  {d['nom']} :  +{int(d['exces']):,} FCFA hors budget",
                                 font=("Arial",10),
                                 text_color=self.COULEUR_PAR_CAT.get(d["nom"],TEXT_MUTED)).pack(
                        anchor="w", padx=5, pady=1)
        except Exception as e:
            print(f"Erreur fond caisse: {e}")

    def enregistrer_budget(self):
        cat_nom = self.combo_cat_budget.get()
        limite  = self.entry_limite.get().strip()
        mapping = {"Alimentation":4,"Transport":5,"Loyer":3,"Loisirs":6}
        id_cat  = mapping.get(cat_nom)
        annee   = _date.today().year
        if not limite or not id_cat:
            messagebox.showwarning("Champs manquants","Veuillez sélectionner une catégorie et saisir une limite.")
            return
        try:
            lim_f = float(limite)
            if lim_f <= 0:
                messagebox.showwarning("Valeur invalide","La limite doit être supérieure à 0.")
                return
        except ValueError:
            messagebox.showerror("Erreur","La limite doit être un nombre valide.")
            return
        try:
            if self._id_budget_en_cours:
                self.model.modifier_budget_bdd(self._id_budget_en_cours, lim_f)
                self._id_budget_en_cours = None
                self.btn_def_budget.configure(
                    text="✚  DÉFINIR LE BUDGET", fg_color=G500, hover_color=G700)
            else:
                self.model.ajouter_budget_bdd(id_cat, lim_f, annee)
            self.entry_limite.delete(0,'end')
            self.actualiser_liste_budgets()
            self.actualiser_barres_budget()
            self.actualiser_fond_caisse()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def actualiser_liste_budgets(self):
        for w in self.container_budgets_list.winfo_children(): w.destroy()
        budgets = self.model.recuperer_suivi_budgets(self.annee_actif, self.mois_actif)
        if not budgets:
            ctk.CTkLabel(self.container_budgets_list, text="Aucun budget défini.",
                         text_color=TEXT_MUTED).pack(pady=20)
            return
        for item in budgets:
            limite  = float(item['montant_limite'])
            depense = float(item['total_depense']) if item['total_depense'] else 0.0
            ratio   = depense/limite if limite>0 else 0
            pct     = int(ratio*100)
            bc      = self.COULEUR_PAR_CAT.get(item['nom_cat'], TEXT_MUTED)
            dep     = ratio>1.0; color = DANGER if dep else G400
            exces   = depense-limite if dep else 0
            fr = ctk.CTkFrame(self.container_budgets_list,
                              fg_color="#fef2f2" if dep else G50,
                              corner_radius=10, border_width=1,
                              border_color="#fecaca" if dep else BORDER_COLOR)
            fr.pack(fill="x", pady=5, padx=4)
            top = ctk.CTkFrame(fr, fg_color="transparent"); top.pack(fill="x", padx=14, pady=(10,0))
            dot = tk.Canvas(top, width=10, height=10,
                            bg="#fef2f2" if dep else G50, highlightthickness=0)
            dot.pack(side="left", padx=(0,6), pady=4)
            dot.create_oval(0,0,10,10, fill=bc, outline="")
            ctk.CTkLabel(top, text=f"{item['nom_cat']}  ({pct}%)",
                         font=("Arial",12,"bold"), text_color=TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=f"{int(depense):,} / {int(limite):,} FCFA",
                         font=("Arial",11), text_color=TEXT_MUTED).pack(side="right")
            pb = ctk.CTkProgressBar(fr, progress_color=color,
                                    fg_color=G100, height=6, corner_radius=99)
            pb.pack(fill="x", padx=14, pady=(6,0)); pb.set(min(ratio,1.0))
            if dep:
                mf = ctk.CTkFrame(fr, fg_color="#fecaca", corner_radius=8)
                mf.pack(fill="x", padx=14, pady=(8,0))
                ctk.CTkLabel(mf, text=f"⚠  Budget dépassé de {int(exces):,} FCFA",
                             font=("Arial",11,"bold"), text_color=DANGER).pack(
                    side="left", padx=10, pady=6)
                ctk.CTkLabel(mf, text="→ Excédent imputé sur le fond de caisse",
                             font=("Arial",10), text_color="#991b1b").pack(
                    side="right", padx=10, pady=6)
            act = ctk.CTkFrame(fr, fg_color="transparent")
            act.pack(anchor="e", padx=14, pady=(8,10))
            ctk.CTkButton(act, text="✏ Modifier", width=90, height=28,
                          fg_color=WARNING, hover_color="#d97706", text_color="white",
                          corner_radius=8, font=("Arial",11),
                          command=lambda b=item: self.preparer_modification_budget(b)).pack(
                side="left", padx=(0,6))
            ctk.CTkButton(act, text="🗑 Supprimer", width=100, height=28,
                          fg_color=DANGER, hover_color="#dc2626", text_color="white",
                          corner_radius=8, font=("Arial",11),
                          command=lambda id_b=item['id_budget']: self.confirmer_suppression_budget(id_b)).pack(
                side="left")

    def preparer_modification_budget(self, item):
        self.combo_cat_budget.set(item['nom_cat'])
        self.entry_limite.delete(0,'end')
        self.entry_limite.insert(0, str(int(float(item['montant_limite']))))
        self._id_budget_en_cours = item['id_budget']
        self.btn_def_budget.configure(text="✏  MODIFIER LE BUDGET",
                                      fg_color=WARNING, hover_color="#d97706")

    def confirmer_suppression_budget(self, id_budget):
        if messagebox.askyesno("Suppression","Supprimer ce budget ?"):
            if self.model.supprimer_budget_bdd(id_budget):
                self._id_budget_en_cours = None
                self.btn_def_budget.configure(text="✚  DÉFINIR LE BUDGET",
                                              fg_color=G500, hover_color=G700)
                self.actualiser_liste_budgets()
                self.actualiser_barres_budget()
                self.actualiser_fond_caisse()

    def _filtrer_budgets(self):
        d_deb, d_fin = self._valider_dates(
            self.bud_e_debut, self.bud_e_fin, self.bud_lbl_err)
        if not d_deb: return
        # Recalcule le fond de caisse sur la période
        txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
        revenus  = sum(float(r['montant']) for r in txs if r.get('type_flux')=='RECETTE')
        depenses = sum(float(r['montant']) for r in txs if r.get('type_flux')=='DEPENSE')
        solde    = revenus - depenses
        self.lbl_caisse_rec.configure(text=f"{revenus:,.0f} FCFA")
        self.lbl_caisse_dep.configure(text=f"{depenses:,.0f} FCFA")
        self.lbl_caisse_sold.configure(text=f"{solde:,.0f} FCFA",
                                       text_color=G600 if solde>=0 else DANGER)
        self.bud_lbl_err.configure(
            text=f"✅  Période : {d_deb} → {d_fin}", text_color=G600)

    def _reset_budgets(self):
        self.bud_lbl_err.configure(text="")
        self.actualiser_fond_caisse()

    def _imprimer_budgets(self):
        d_deb, d_fin = self._valider_dates(
            self.bud_e_debut, self.bud_e_fin, self.bud_lbl_err)
        budgets = self.model.recuperer_suivi_budgets(self.annee_actif, self.mois_actif)
        lignes = [(b['nom_cat'], f"{float(b['montant_limite']):,.0f} FCFA",
                   f"{float(b['total_depense']) if b['total_depense'] else 0:,.0f} FCFA",
                   f"{int((float(b['total_depense']) if b['total_depense'] else 0)/float(b['montant_limite'])*100) if float(b['montant_limite'])>0 else 0}%")
                  for b in budgets]
        periode = f"Période : {d_deb} → {d_fin}" if d_deb else \
                  f"{NOMS_MOIS[self.mois_actif-1]} {self.annee_actif}"
        self._imprimer_rapport("Rapport Budgets",
                               ["Catégorie","Limite","Dépensé","Consommé"],
                               lignes, periode)

    # ══════════════════════════════════════════════
    #  PAGE STATISTIQUES
    # ══════════════════════════════════════════════
    def creer_page_objectifs(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["objectifs"] = page
        ctk.CTkLabel(page, text="Statistiques Mensuelles",
                     font=("Arial",22,"bold"), text_color=TEXT_PRIMARY).pack(
            anchor="nw", pady=(0,10))

        # ── Barre filtre stats ─────────────────────────────────────
        self.stat_e_debut, self.stat_e_fin, self.stat_lbl_err = \
            self._barre_filtre(page,
                on_filtrer=self._filtrer_stats,
                on_imprimer=self._imprimer_stats,
                on_reset=self._reset_stats)

        # KPI
        self.stats_histo_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.stats_histo_frame.pack(fill="x", pady=(0,12))
        self.stats_histo_frame.grid_columnconfigure((0,1,2), weight=1)
        self.lbl_histo_rev  = self._carte_histo("Revenus ce mois",  "0 FCFA", 0, G600)
        self.lbl_histo_dep  = self._carte_histo("Dépenses ce mois", "0 FCFA", 1, DANGER)
        self.lbl_histo_sold = self._carte_histo("Solde ce mois",    "0 FCFA", 2, BLUE)

        # Graphique
        graph_card = self._card(page)
        graph_card.pack(fill="both", expand=True, pady=(0,12))
        self._section_title(graph_card, "Évolution sur 6 mois", pady=(14,8))
        self.canvas_histo = tk.Canvas(graph_card, bg=CARD_BG,
                                      highlightthickness=0, height=240)
        self.canvas_histo.pack(fill="x", padx=20, pady=(0,14))

        # Récap
        recap_card = self._card(page)
        recap_card.pack(fill="both", expand=True)
        self._section_title(recap_card, "Récapitulatif par mois", pady=(14,8))
        self.container_histo_table = ctk.CTkScrollableFrame(
            recap_card, fg_color="transparent", height=150)
        self.container_histo_table.pack(fill="both", expand=True, padx=14, pady=(0,14))
        for ci in range(5):
            self.container_histo_table.grid_columnconfigure(
                ci, weight=1, uniform="scol")

        self.actualiser_page_statistiques()

    def _carte_histo(self, titre, valeur, col, couleur):
        card = self._card(self.stats_histo_frame, height=90)
        card.grid(row=0, column=col, padx=6, sticky="ew")
        card.grid_propagate(False)
        ctk.CTkFrame(card, height=3, fg_color=couleur, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text=titre, font=("Arial",11),
                     text_color=TEXT_MUTED).pack(pady=(10,0))
        lbl = ctk.CTkLabel(card, text=valeur, font=("Arial",15,"bold"), text_color=couleur)
        lbl.pack()
        return lbl

    def actualiser_page_statistiques(self, donnees=None):
        if donnees is None:
            donnees = self.model.recuperer_historique_mensuel(6)
        auj = _date.today()
        mc = next((d for d in donnees if d['annee']==auj.year and d['mois']==auj.month), None)
        if mc:
            rev = float(mc['revenus'] or 0); dep = float(mc['depenses'] or 0)
            sold = rev-dep
            self.lbl_histo_rev.configure(text=f"{rev:,.0f} FCFA")
            self.lbl_histo_dep.configure(text=f"{dep:,.0f} FCFA")
            self.lbl_histo_sold.configure(text=f"{sold:,.0f} FCFA",
                                          text_color=G600 if sold>=0 else DANGER)
        else:
            for l,v in [(self.lbl_histo_rev,"0 FCFA"),(self.lbl_histo_dep,"0 FCFA"),
                        (self.lbl_histo_sold,"0 FCFA")]:
                l.configure(text=v)

        # Graphique
        self.canvas_histo.delete("all")
        if not donnees:
            self.canvas_histo.create_text(300,120,text="Aucune donnée",
                                          fill=TEXT_MUTED,font=("Arial",12)); return
        self.canvas_histo.update_idletasks()
        W = max(self.canvas_histo.winfo_width(), 700); H = 230
        self.canvas_histo.configure(height=H)
        nb = len(donnees)
        mg,md,mh,mb2 = 60,20,20,40
        lz = W-mg-md; lg = lz/nb; bw = min(lg*0.35,28)
        mv = max(max(float(d['revenus'] or 0) for d in donnees),
                 max(float(d['depenses'] or 0) for d in donnees),1)
        hz = H-mh-mb2
        for i in range(nb):
            x0 = mg+i*lg
            self.canvas_histo.create_rectangle(x0,mh,x0+lg,H-mb2,
                fill=G50 if i%2==0 else CARD_BG, outline="")
        for i in range(5):
            yv = mv*i/4; yp = H-mb2-int(yv/mv*hz)
            self.canvas_histo.create_line(mg,yp,W-md,yp,fill=BORDER_COLOR,dash=(3,4))
            self.canvas_histo.create_text(mg-6,yp,anchor="e",font=("Arial",8),fill=TEXT_MUTED,
                text=f"{int(yv/1000)}k" if yv>=1000 else str(int(yv)))
        for i,d in enumerate(donnees):
            rev=float(d['revenus'] or 0); dep=float(d['depenses'] or 0)
            cx=mg+i*lg+lg/2
            hr=int(rev/mv*hz); x0r=cx-bw-2
            self.canvas_histo.create_rectangle(x0r,H-mb2-hr,x0r+bw,H-mb2,fill=G400,outline="")
            hd=int(dep/mv*hz); x0d=cx+2
            self.canvas_histo.create_rectangle(x0d,H-mb2-hd,x0d+bw,H-mb2,fill=DANGER,outline="")
            self.canvas_histo.create_text(cx,H-mb2+14,
                text=f"{NOMS_COURTS[d['mois']-1]}\n{str(d['annee'])[2:]}",
                font=("Arial",8),fill=TEXT_MUTED)
        self.canvas_histo.create_rectangle(mg,6,mg+10,16,fill=G400,outline="")
        self.canvas_histo.create_text(mg+13,11,text="Revenus",anchor="w",
                                      font=("Arial",9),fill=TEXT_PRIMARY)
        self.canvas_histo.create_rectangle(mg+68,6,mg+78,16,fill=DANGER,outline="")
        self.canvas_histo.create_text(mg+81,11,text="Dépenses",anchor="w",
                                      font=("Arial",9),fill=TEXT_PRIMARY)

        # Tableau récap
        for w in self.container_histo_table.winfo_children(): w.destroy()
        dr = self._table_headers(self.container_histo_table,
                                 ["MOIS","REVENUS","DÉPENSES","SOLDE","ÉVOLUTION"],
                                 uniform="scol")
        sp = None
        for ri, d in enumerate(donnees):
            rev=float(d['revenus'] or 0); dep=float(d['depenses'] or 0)
            solde=rev-dep; cs=G600 if solde>=0 else DANGER
            rbg=G50 if ri%2==0 else CARD_BG
            grid_row=ri+dr
            if sp is not None:
                diff=solde-sp; evol=f"{'▲' if diff>=0 else '▼'}  {abs(diff):,.0f}"
                ce=G600 if diff>=0 else DANGER
            else: evol,ce="—",TEXT_MUTED
            for ci,(txt,tc) in enumerate([
                (f"{NOMS_COURTS[d['mois']-1]} {d['annee']}",TEXT_PRIMARY),
                (f"{rev:,.0f} FCFA",G600),(f"{dep:,.0f} FCFA",DANGER),
                (f"{solde:,.0f} FCFA",cs),(evol,ce)]):
                ctk.CTkLabel(self.container_histo_table,text=txt,
                             font=("Arial",11),text_color=tc,
                             fg_color=rbg,anchor="w").grid(
                    row=grid_row,column=ci,sticky="nsew",ipadx=10,ipady=5)
            sp=solde

    def _filtrer_stats(self):
        d_deb, d_fin = self._valider_dates(
            self.stat_e_debut, self.stat_e_fin, self.stat_lbl_err)
        if not d_deb: return
        txs = self.model.recuperer_transactions_par_periode(d_deb, d_fin)
        # Recalcule un historique synthétique sur la période
        from collections import defaultdict
        mois_data = defaultdict(lambda: {"revenus":0,"depenses":0})
        for r in txs:
            try:
                dt = datetime.strptime(str(r['date_op']), "%Y-%m-%d")
                k = (dt.year, dt.month)
                if r.get('type_flux') == 'RECETTE':
                    mois_data[k]["revenus"] += float(r['montant'])
                else:
                    mois_data[k]["depenses"] += float(r['montant'])
            except: pass
        donnees = [{"annee":k[0],"mois":k[1],
                    "revenus":v["revenus"],"depenses":v["depenses"]}
                   for k,v in sorted(mois_data.items())]
        self.actualiser_page_statistiques(donnees=donnees)
        self.stat_lbl_err.configure(
            text=f"✅  Période filtrée : {d_deb} → {d_fin}", text_color=G600)

    def _reset_stats(self):
        self.stat_lbl_err.configure(text="")
        self.actualiser_page_statistiques()

    def _imprimer_stats(self):
        d_deb, d_fin = self._valider_dates(
            self.stat_e_debut, self.stat_e_fin, self.stat_lbl_err)
        donnees = self.model.recuperer_historique_mensuel(12)
        periode = f"Période : {d_deb} → {d_fin}" if d_deb else "6 derniers mois"
        lignes = [(f"{NOMS_COURTS[d['mois']-1]} {d['annee']}",
                   f"{float(d['revenus'] or 0):,.0f} FCFA",
                   f"{float(d['depenses'] or 0):,.0f} FCFA",
                   f"{float(d['revenus'] or 0)-float(d['depenses'] or 0):,.0f} FCFA")
                  for d in donnees]
        self._imprimer_rapport("Statistiques Mensuelles",
                               ["Mois","Revenus","Dépenses","Solde"],
                               lignes, periode)

    # ══════════════════════════════════════════════
    #  PAGE PARAMÈTRES
    # ══════════════════════════════════════════════
    def creer_page_parametres(self):
        page = ctk.CTkFrame(self.container, fg_color="transparent")
        self.pages["parametres"] = page
        ctk.CTkLabel(page, text="Paramètres", font=("Arial",22,"bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="nw", pady=(0,18))

        config_card = self._card(page)
        config_card.pack(fill="x", pady=(0,14))
        self._section_title(config_card, "Configuration de l'Exercice", pady=(18,6))
        ctk.CTkLabel(config_card,
                     text="Définissez le mois et l'année de départ de votre suivi budgétaire.\n"
                          "Le report du mois précédent est effectué automatiquement.",
                     font=("Arial",12), text_color=TEXT_MUTED, justify="center").pack(pady=(0,14))

        row_cfg = ctk.CTkFrame(config_card, fg_color="transparent")
        row_cfg.pack(pady=(0,10))
        ctk.CTkLabel(row_cfg, text="Mois de départ :", font=("Arial",12),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=(20,6))
        self.combo_mois_depart = ctk.CTkComboBox(
            row_cfg, width=140, height=36,
            border_color=BORDER_COLOR, fg_color=G50,
            button_color=G400, button_hover_color=G600,
            values=NOMS_MOIS)
        self.combo_mois_depart.pack(side="left", padx=(0,20))
        ctk.CTkLabel(row_cfg, text="Année :", font=("Arial",12),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=(0,6))
        self.entry_annee_depart = ctk.CTkEntry(
            row_cfg, width=90, height=36, placeholder_text="Ex: 2026",
            border_color=BORDER_COLOR, fg_color=G50)
        self.entry_annee_depart.pack(side="left", padx=(0,20))

        self.label_config_status = ctk.CTkLabel(config_card, text="",
                                                 font=("Arial",12), text_color=G600)
        self.label_config_status.pack()
        ctk.CTkButton(config_card, text="💾  ENREGISTRER LA CONFIGURATION",
                      fg_color=G500, hover_color=G700, text_color="white",
                      height=42, font=("Arial",13,"bold"), corner_radius=10,
                      command=self.enregistrer_config_depart).pack(
            fill="x", padx=22, pady=(8,22))

        date_card = self._card(page)
        date_card.pack(fill="x", pady=(0,14))
        auj = _date.today()
        ctk.CTkLabel(date_card,
                     text=f"📅  Date du système : {auj.day} {NOMS_MOIS[auj.month-1]} {auj.year}",
                     font=("Arial",14,"bold"), text_color=TEXT_PRIMARY).pack(pady=(20,6))
        ctk.CTkLabel(date_card,
                     text="Le report mensuel est calculé et inséré automatiquement\n"
                          "à chaque démarrage de l'application en début de mois.",
                     font=("Arial",11), text_color=TEXT_MUTED, justify="center").pack(pady=(0,20))

        # ── Changement de mot de passe ────────────────────────────
        creer_widget_changement_mdp(page, self._card, self._section_title)

        # ── Verrouiller ───────────────────────────────────────────
        lock_card = self._card(page)
        lock_card.pack(fill="x", pady=(0, 14))
        lock_inner = ctk.CTkFrame(lock_card, fg_color="transparent")
        lock_inner.pack(fill="x", padx=22, pady=16)
        ctk.CTkLabel(lock_inner, text="🔒  Verrouiller l'application",
                     font=("Arial",13,"bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(lock_inner,
                     text="Ferme l'app et revient à l'écran de connexion",
                     font=("Arial",10), text_color=TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkButton(lock_inner, text="🔒  Verrouiller",
                      fg_color="#dc2626", hover_color="#991b1b",
                      text_color="white", height=36, width=140,
                      font=("Arial",12,"bold"), corner_radius=8,
                      command=self._deconnecter).pack(side="right")

    def charger_config_parametres(self):
        config = self.model.recuperer_config_exercice(_date.today().year)
        if config:
            self.entry_annee_depart.delete(0,'end')
            self.entry_annee_depart.insert(0, str(config['annee']))
            desc = config.get('description','')
            for nm in NOMS_MOIS:
                if nm in desc:
                    self.combo_mois_depart.set(nm); break

    def enregistrer_config_depart(self):
        mois_nom  = self.combo_mois_depart.get()
        annee_str = self.entry_annee_depart.get().strip()
        if not annee_str:
            self.label_config_status.configure(
                text="⚠️  Veuillez saisir une année.", text_color=DANGER); return
        try:
            annee_dest = int(annee_str)
            if annee_dest < 2000 or annee_dest > 2100:
                self.label_config_status.configure(
                    text="⚠️  Année invalide (entre 2000 et 2100).", text_color=DANGER); return
            mois_dest = NOMS_MOIS.index(mois_nom)+1
            auj = _date.today()
            resultat = self.model.cloture_mois_manuel(auj.year, auj.month, annee_dest, mois_dest)
            succes, solde = resultat if isinstance(resultat,tuple) else (resultat,0)
            self.model.initialiser_exercice(annee_dest, f"Exercice {annee_dest} - {mois_nom}")
            if succes:
                sg = "+" if solde>=0 else ""
                self.label_config_status.configure(
                    text=f"✅  {NOMS_MOIS[auj.month-1]} {auj.year} clôturé  —  "
                         f"Report {sg}{int(solde):,} FCFA → {mois_nom} {annee_dest}",
                    text_color=G600)
            else:
                self.label_config_status.configure(
                    text=f"✅  Exercice {annee_dest} configuré — départ : {mois_nom} {annee_dest}",
                    text_color=G600)
            self.mois_actif=mois_dest; self.annee_actif=annee_dest
            self._maj_badge_mois()
            self.label_titre_dashboard.configure(
                text=f"Tableau de Bord — {mois_nom} {annee_dest}")
            self.actualiser_statistiques()
            self.actualiser_barres_budget()
            self.remplir_tableau_dashboard()
        except Exception as e:
            self.label_config_status.configure(text=f"❌  Erreur : {e}", text_color=DANGER)

    def _deconnecter(self):
        if messagebox.askyesno("Verrouiller", "Verrouiller l'application ?"):
            self.destroy()
            _lancer_login()

    def actualiser_graphique_categories(self): pass


def _lancer_login():
    def on_success():
        app = BudgetApp()
        app.mainloop()
    login = LoginWindow(on_success=on_success)
    login.mainloop()


if __name__ == "__main__":
    _lancer_login()