from model import BudgetModel

# Initialisation
model = BudgetModel()

# 1. On crée l'exercice fiscal
model.initialiser_exercice(2024, 5000.00, "Budget Annuel 2024")

# 2. On affiche les catégories disponibles pour vérifier que l'import SQL a marché
categories = model.recuperer_categories()
print("\nCatégories disponibles :")
for c in categories:
    print(f"ID: {c['id_cat']} | {c['nom_cat']} ({c['type_flux']})")

# 3. Ajoutons une première transaction de test (ex: Loyer payé en Janvier)
# On suppose que l'ID de la catégorie 'Loyer' est 3 et le mode 'Banque' est 2
# model.ajouter_transaction("Loyer Janvier", 800.00, "2024-01-05", 3, 2, 2024)