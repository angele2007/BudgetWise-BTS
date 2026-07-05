from database import Database
import mysql.connector
from datetime import date


class BudgetModel:
    def __init__(self):
        self.db = Database()
        self.conn = self.db.connecter()
        if self.conn is None:
            print("Alerte : La connexion à la base de données a échoué.")
        # À chaque démarrage, on vérifie si le solde du mois précédent doit être reporté
        self.verifier_et_reporter_solde()

    # ─────────────────────────────────────────────────────────────────
    #  REPORT AUTOMATIQUE DU SOLDE
    #  Appelé au démarrage. Si le mois précédent n'a pas encore été
    #  reporté, on calcule son solde et on l'insère comme RECETTE
    #  au 1er jour du mois courant.
    # ─────────────────────────────────────────────────────────────────
    def verifier_et_reporter_solde(self):
        auj        = date.today()
        mois_prec  = auj.month - 1 if auj.month > 1 else 12
        annee_prec = auj.year       if auj.month > 1 else auj.year - 1
        conn = self.db.connecter()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)

            # Déjà reporté ce mois ?
            cursor.execute("""
                SELECT id_cloture FROM cloture_mensuelle
                WHERE annee_id = %s AND mois = %s
            """, (annee_prec, mois_prec))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return  # Déjà fait

            # Calculer le solde du mois précédent
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN c.type_flux = 'RECETTE' THEN t.montant ELSE 0 END) AS revenus,
                    SUM(CASE WHEN c.type_flux = 'DEPENSE' THEN t.montant ELSE 0 END) AS depenses
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
            """, (mois_prec, annee_prec))
            r = cursor.fetchone()
            revenus  = float(r['revenus'])  if r and r['revenus']  else 0.0
            depenses = float(r['depenses']) if r and r['depenses'] else 0.0
            solde    = revenus - depenses

            if solde != 0:
                # S'assurer que l'exercice courant existe
                cursor.execute("""
                    INSERT IGNORE INTO exercice_fiscal (annee, fonds_initial, description)
                    VALUES (%s, 0, %s)
                """, (auj.year, f"Exercice {auj.year}"))

                # Insérer le report comme recette au 1er du mois courant
                # Catégorie 7 = "Report" (créée ci-dessous si besoin)
                cursor.execute("""
                    INSERT IGNORE INTO categorie (id_cat, nom_cat, type_flux)
                    VALUES (7, 'Report Mois Précédent', 'RECETTE')
                """)
                date_report = date(auj.year, auj.month, 1)
                cursor.execute("""
                    INSERT INTO transaction (libelle, montant, date_op, id_cat, id_mode, annee_id)
                    VALUES (%s, %s, %s, 7, 1, %s)
                """, (
                    f"Report {mois_prec:02d}/{annee_prec}",
                    abs(solde),
                    date_report,
                    auj.year
                ))

            # Enregistrer la clôture du mois précédent
            cursor.execute("""
                INSERT INTO cloture_mensuelle (annee_id, mois, solde_cloture)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE solde_cloture = %s
            """, (annee_prec, mois_prec, solde, solde))

            conn.commit()
            cursor.close()
            conn.close()
            print(f"Report automatique : solde {mois_prec}/{annee_prec} = {solde:,.0f} FCFA")
        except Exception as e:
            print(f"Erreur verifier_et_reporter_solde : {e}")

    def cloture_mois_manuel(self, annee_source, mois_source, annee_dest, mois_dest):
        """
        Clôture manuellement un mois et reporte son solde en recette
        du mois de destination (annee_dest/mois_dest).
        Appelé depuis Paramètres quand on configure un nouveau mois de départ.
        """
        conn = self.db.connecter()
        if not conn:
            return False
        try:
            cursor = conn.cursor(dictionary=True)

            # Calculer le solde du mois source
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN c.type_flux = 'RECETTE' THEN t.montant ELSE 0 END) AS revenus,
                    SUM(CASE WHEN c.type_flux = 'DEPENSE' THEN t.montant ELSE 0 END) AS depenses
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
            """, (mois_source, annee_source))
            r = cursor.fetchone()
            revenus  = float(r['revenus'])  if r and r['revenus']  else 0.0
            depenses = float(r['depenses']) if r and r['depenses'] else 0.0
            solde    = revenus - depenses

            # Enregistrer la clôture
            cursor.execute("""
                INSERT INTO cloture_mensuelle (annee_id, mois, solde_cloture)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE solde_cloture = %s
            """, (annee_source, mois_source, solde, solde))

            # Reporter le solde en recette au 1er du mois destination si solde != 0
            if solde != 0:
                cursor.execute("""
                    INSERT IGNORE INTO exercice_fiscal (annee, fonds_initial, description)
                    VALUES (%s, 0, %s)
                """, (annee_dest, f"Exercice {annee_dest}"))

                cursor.execute("""
                    INSERT IGNORE INTO categorie (id_cat, nom_cat, type_flux)
                    VALUES (7, 'Report Mois Précédent', 'RECETTE')
                """)
                date_report = date(annee_dest, mois_dest, 1)
                # Supprimer un éventuel report déjà existant pour ce mois
                cursor.execute("""
                    DELETE FROM transaction
                    WHERE id_cat = 7
                      AND MONTH(date_op) = %s AND YEAR(date_op) = %s
                """, (mois_dest, annee_dest))
                cursor.execute("""
                    INSERT INTO transaction (libelle, montant, date_op, id_cat, id_mode, annee_id)
                    VALUES (%s, %s, %s, 7, 1, %s)
                """, (
                    f"Report {mois_source:02d}/{annee_source}",
                    abs(solde),
                    date_report,
                    annee_dest
                ))

            conn.commit()
            cursor.close()
            conn.close()
            return True, solde
        except Exception as e:
            print(f"Erreur cloture_mois_manuel : {e}")
            return False, 0

    def initialiser_exercice(self, annee, desc=""):
        conn = self.db.connecter()
        if conn:
            cursor = conn.cursor()
            sql = """INSERT INTO exercice_fiscal (annee, fonds_initial, description)
                     VALUES (%s, 0, %s)
                     ON DUPLICATE KEY UPDATE description = %s"""
            cursor.execute(sql, (annee, desc, desc))
            conn.commit()
            cursor.close()
            conn.close()

    def recuperer_config_exercice(self, annee):
        conn = self.db.connecter()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT annee, fonds_initial, description FROM exercice_fiscal WHERE annee = %s",
                (annee,))
            r = cursor.fetchone()
            cursor.close()
            conn.close()
            return r
        except Exception as e:
            print(f"Erreur recuperer_config_exercice : {e}")
            return None

    def ajouter_transaction_bdd(self, libelle, montant, date_op, id_cat, id_mode, annee_id):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                sql = """INSERT INTO transaction (libelle, montant, date_op, id_cat, id_mode, annee_id)
                         VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (libelle, montant, date_op, id_cat, id_mode, annee_id))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"Erreur SQL insertion : {e}")
                return False
        return False

    def modifier_transaction_bdd(self, id_transac, libelle, montant, date_op, id_cat):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                sql = """UPDATE transaction
                         SET libelle=%s, montant=%s, date_op=%s, id_cat=%s
                         WHERE id_transac=%s"""
                cursor.execute(sql, (libelle, montant, date_op, id_cat, id_transac))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"Erreur modifier_transaction_bdd : {e}")
                return False
        return False

    def supprimer_transaction_bdd(self, id_t):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transaction WHERE id_transac = %s", (id_t,))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"Erreur suppression : {e}")
                return False
        return False

    def recuperer_transactions_recentes(self, limite=50, mois=None, annee=None):
        conn = self.db.connecter()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            if mois and annee:
                sql = """SELECT t.id_transac, t.date_op, c.nom_cat, t.libelle,
                                c.type_flux, t.montant
                         FROM transaction t
                         JOIN categorie c ON t.id_cat = c.id_cat
                         WHERE MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
                         ORDER BY t.date_op DESC LIMIT %s"""
                cursor.execute(sql, (mois, annee, limite))
            else:
                sql = """SELECT t.id_transac, t.date_op, c.nom_cat, t.libelle,
                                c.type_flux, t.montant
                         FROM transaction t
                         JOIN categorie c ON t.id_cat = c.id_cat
                         ORDER BY t.date_op DESC LIMIT %s"""
                cursor.execute(sql, (limite,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Erreur recuperer_transactions_recentes : {e}")
            return []

    # ─────────────────────────────────────────────────────────────────
    #  ÉTAT FINANCIER  (dashboard)
    #  • revenus  = total recettes du mois courant (date réelle)
    #  • depenses = total dépenses du mois courant
    #  • solde    = total recettes exercice − total dépenses exercice
    # ─────────────────────────────────────────────────────────────────
    def recuperer_statistiques_mensuelles(self, mois=None, annee=None):
        """
        mois/annee : période active du tableau de bord.
        Par défaut = date du jour.
        """
        conn = self.db.connecter()
        if not conn:
            return {"revenus": 0, "depenses": 0, "solde": 0}
        try:
            auj   = date.today()
            mois  = mois  or auj.month
            annee = annee or auj.year
            cursor = conn.cursor(dictionary=True)

            # Recettes et dépenses du mois actif
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN c.type_flux = 'RECETTE' THEN t.montant ELSE 0 END) AS revenus,
                    SUM(CASE WHEN c.type_flux = 'DEPENSE' THEN t.montant ELSE 0 END) AS depenses
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
            """, (mois, annee))
            r = cursor.fetchone()
            revenus  = float(r['revenus'])  if r and r['revenus']  else 0.0
            depenses = float(r['depenses']) if r and r['depenses'] else 0.0

            # Solde global de l'exercice actif uniquement
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN c.type_flux = 'RECETTE' THEN t.montant ELSE 0 END) AS total_rec,
                    SUM(CASE WHEN c.type_flux = 'DEPENSE' THEN t.montant ELSE 0 END) AS total_dep
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
            """, (mois, annee))
            g = cursor.fetchone()
            total_rec = float(g['total_rec']) if g and g['total_rec'] else 0.0
            total_dep = float(g['total_dep']) if g and g['total_dep'] else 0.0
            solde     = total_rec - total_dep

            cursor.close()
            conn.close()
            return {"revenus": revenus, "depenses": depenses, "solde": solde}
        except Exception as e:
            print(f"Erreur stats: {e}")
            return {"revenus": 0, "depenses": 0, "solde": 0}

    def recuperer_depenses_par_categorie(self):
        conn = self.db.connecter()
        if not conn:
            return []
        try:
            auj = date.today()
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT c.nom_cat, SUM(t.montant) AS total
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE c.type_flux = 'DEPENSE'
                  AND MONTH(t.date_op) = %s AND YEAR(t.date_op) = %s
                GROUP BY c.nom_cat
            """
            cursor.execute(sql, (auj.month, auj.year))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Erreur recuperer_depenses_par_categorie : {e}")
            return []

    def ajouter_budget_bdd(self, id_cat, limite, annee):
        try:
            self.sauvegarder_budget(id_cat, limite, annee)
            return True
        except Exception as e:
            print(f"Erreur ajouter_budget_bdd : {e}")
            return False

    def sauvegarder_budget(self, id_cat, limite, annee):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                sql = """INSERT INTO budget (id_categorie, montant_limite, id_exercice)
                         VALUES (%s, %s, %s)
                         ON DUPLICATE KEY UPDATE montant_limite = %s"""
                cursor.execute(sql, (id_cat, limite, annee, limite))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Erreur sauvegarder_budget : {e}")

    def modifier_budget_bdd(self, id_budget, nouvelle_limite):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE budget SET montant_limite = %s WHERE id_budget = %s",
                    (nouvelle_limite, id_budget))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"Erreur modification budget : {e}")
                return False
        return False

    def supprimer_budget_bdd(self, id_budget):
        conn = self.db.connecter()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM budget WHERE id_budget = %s", (id_budget,))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"Erreur suppression budget : {e}")
                return False
        return False

    def recuperer_suivi_budgets(self, annee, mois=None):
        conn = self.db.connecter()
        if not conn:
            return []
        try:
            auj  = date.today()
            mois = mois or auj.month
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT b.id_budget, c.nom_cat, b.montant_limite,
                       (SELECT SUM(t.montant) FROM transaction t
                        WHERE t.id_cat = b.id_categorie
                          AND MONTH(t.date_op) = %s
                          AND YEAR(t.date_op)  = %s) AS total_depense
                FROM budget b
                JOIN categorie c ON b.id_categorie = c.id_cat
                WHERE b.id_exercice = %s
            """
            cursor.execute(sql, (auj.month, auj.year, annee))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Erreur recuperer_suivi_budgets : {e}")
            return []

    def recuperer_total_depenses_categorie(self, nom_categorie):
        conn = self.db.connecter()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            sql = """
                SELECT SUM(t.montant)
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE c.nom_cat = %s AND c.type_flux = 'DEPENSE'
            """
            cursor.execute(sql, (nom_categorie,))
            r = cursor.fetchone()
            cursor.close()
            conn.close()
            return r[0] if r and r[0] else 0
        except Exception as e:
            print(f"Erreur recuperer_total_depenses_categorie : {e}")
            return 0

    def recuperer_historique_mensuel(self, nb_mois=6):
        conn = self.db.connecter()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT
                    YEAR(t.date_op)  AS annee,
                    MONTH(t.date_op) AS mois,
                    SUM(CASE WHEN c.type_flux = 'RECETTE' THEN t.montant ELSE 0 END) AS revenus,
                    SUM(CASE WHEN c.type_flux = 'DEPENSE' THEN t.montant ELSE 0 END) AS depenses
                FROM transaction t
                JOIN categorie c ON t.id_cat = c.id_cat
                WHERE t.date_op >= DATE_SUB(LAST_DAY(CURRENT_DATE()), INTERVAL %s MONTH)
                GROUP BY YEAR(t.date_op), MONTH(t.date_op)
                ORDER BY annee ASC, mois ASC
            """
            cursor.execute(sql, (nb_mois,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Erreur recuperer_historique_mensuel : {e}")
            return []

        # ═══════════════════════════════════════════════════════════════════
        #  MÉTHODES À AJOUTER À LA CLASSE BudgetModel dans model.py
        #  Collez ces méthodes à l'intérieur de la classe BudgetModel,
        #  avant le dernier "def recuperer_historique_mensuel"
        # ═══════════════════════════════════════════════════════════════════

    def recuperer_transactions_par_periode(self, date_debut, date_fin):
            """
            Retourne toutes les transactions entre date_debut et date_fin (incluses).
            date_debut et date_fin sont des strings 'YYYY-MM-DD'.
            """
            conn = self.db.connecter()
            if not conn:
                return []
            try:
                cursor = conn.cursor(dictionary=True)
                sql = """
                    SELECT t.id_transac, t.date_op, c.nom_cat, t.libelle,
                           c.type_flux, t.montant
                    FROM transaction t
                    JOIN categorie c ON t.id_cat = c.id_cat
                    WHERE t.date_op BETWEEN %s AND %s
                    ORDER BY t.date_op DESC
                """
                cursor.execute(sql, (date_debut, date_fin))
                result = cursor.fetchall()
                cursor.close()
                conn.close()
                return result
            except Exception as e:
                print(f"Erreur recuperer_transactions_par_periode : {e}")
                return []

    def vider_toutes_transactions(self):
            """
            Supprime TOUTES les transactions et les clôtures mensuelles.
            Action irréversible — protégée par double confirmation dans la vue.
            """
            conn = self.db.connecter()
            if not conn:
                return False
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cloture_mensuelle")
                cursor.execute("DELETE FROM transaction")
                conn.commit()
                cursor.close()
                conn.close()
                print("Historique vidé.")
                return True
            except Exception as e:
                print(f"Erreur vider_toutes_transactions : {e}")
                return False