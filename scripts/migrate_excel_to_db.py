"""
Script de migration des données Excel vers SQLite
Migre toutes les données de recoltes_fraises.xlsx vers la base de données SQLite
"""
import pandas as pd
from pathlib import Path
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    init_database, add_parametre, add_recolte, set_jour_courant,
    set_plants_par_annee, set_recolte_quotidienne
)

# Utiliser config.py si disponible, sinon fallback
try:
    from config import EXCEL_PATH
except ImportError:
    # Fallback: chercher dans data/ puis à la racine
    BASE_DIR = Path(__file__).parent.parent.resolve()
    data_path = BASE_DIR / "data" / "recoltes_fraises.xlsx"
    root_path = BASE_DIR / "recoltes_fraises.xlsx"
    EXCEL_PATH = str(data_path if data_path.exists() else root_path)

def migrate_excel_to_db():
    """Migre toutes les données depuis Excel vers SQLite."""
    
    if not Path(EXCEL_PATH).exists():
        print(f"❌ Fichier Excel introuvable : {EXCEL_PATH}")
        return False
    
    print("🔄 Migration des données Excel vers SQLite...")
    
    # Initialiser la base de données
    init_database()
    
    # 1. Migration des Paramètres
    print("\n📋 Migration de l'onglet 'Paramètres'...")
    try:
        params = pd.read_excel(EXCEL_PATH, sheet_name="Paramètres")
        if not params.empty:
            count = 0
            for _, row in params.iterrows():
                parcelle = str(row.get("parcelle", "")).strip().lower()
                variety = str(row.get("variety", "")).strip().lower()
                nb_rangees = row.get("nb_rangees", 10)
                if pd.isna(nb_rangees):
                    nb_rangees = 10
                saison_debut = row.get("saison_debut")
                saison_fin = row.get("saison_fin")
                
                if parcelle and variety:
                    try:
                        add_parametre(
                            parcelle=parcelle,
                            variety=variety,
                            nb_rangees=int(nb_rangees),
                            saison_debut=int(saison_debut) if pd.notna(saison_debut) else None,
                            saison_fin=int(saison_fin) if pd.notna(saison_fin) else None
                        )
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Erreur pour {parcelle}/{variety}: {e}")
            print(f"   ✅ {count} paramètres migrés")
        else:
            print("   ⚠️ Onglet 'Paramètres' vide")
    except Exception as e:
        print(f"   ❌ Erreur lors de la migration des paramètres : {e}")
    
    # 2. Migration des Récoltes
    print("\n📅 Migration de l'onglet 'Recoltes'...")
    try:
        recoltes = pd.read_excel(EXCEL_PATH, sheet_name="Recoltes", parse_dates=["date"])
        if not recoltes.empty:
            count = 0
            for _, row in recoltes.iterrows():
                date = row.get("date")
                variety = str(row.get("variety", "")).strip().lower()
                kg_total = row.get("kg_total")
                commentaires = row.get("commentaires")
                
                if pd.notna(date) and variety and pd.notna(kg_total):
                    try:
                        date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
                        add_recolte(
                            date=date_str,
                            variety=variety,
                            kg_total=float(kg_total),
                            commentaires=str(commentaires) if pd.notna(commentaires) else None
                        )
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Erreur pour {date}/{variety}: {e}")
            print(f"   ✅ {count} récoltes migrées")
        else:
            print("   ⚠️ Onglet 'Recoltes' vide")
    except Exception as e:
        print(f"   ❌ Erreur lors de la migration des récoltes : {e}")
    
    # 3. Migration du Jour_courant
    print("\n☀️ Migration de l'onglet 'Jour_courant'...")
    try:
        jour_courant = pd.read_excel(EXCEL_PATH, sheet_name="Jour_courant", parse_dates=["date"])
        if not jour_courant.empty:
            count = 0
            for _, row in jour_courant.iterrows():
                date = row.get("date")
                variety = str(row.get("variety", "")).strip().lower()
                kg_premiere_rangee = row.get("kg_premiere_rangee")
                commentaires = row.get("commentaires")
                
                if pd.notna(date) and variety:
                    try:
                        date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
                        set_jour_courant(
                            date=date_str,
                            variety=variety,
                            kg_premiere_rangee=float(kg_premiere_rangee) if pd.notna(kg_premiere_rangee) else None,
                            commentaires=str(commentaires) if pd.notna(commentaires) else None
                        )
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Erreur pour {date}/{variety}: {e}")
            print(f"   ✅ {count} enregistrements du jour courant migrés")
        else:
            print("   ℹ️ Onglet 'Jour_courant' vide (normal)")
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la migration du jour courant : {e}")
    
    # 4. Migration de Plants_par_annee
    print("\n🌱 Migration de l'onglet 'Plants_par_annee'...")
    try:
        plants = pd.read_excel(EXCEL_PATH, sheet_name="Plants_par_annee")
        if not plants.empty:
            count = 0
            for _, row in plants.iterrows():
                variety = str(row.get("variety", "")).strip().lower()
                annee = row.get("Année")
                nb_plants = row.get("Nb_plants")
                
                if variety and pd.notna(annee) and pd.notna(nb_plants):
                    try:
                        set_plants_par_annee(
                            variety=variety,
                            annee=int(annee),
                            nb_plants=int(nb_plants)
                        )
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Erreur pour {variety}/{annee}: {e}")
            print(f"   ✅ {count} enregistrements de plants migrés")
        else:
            print("   ⚠️ Onglet 'Plants_par_annee' vide")
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la migration des plants : {e}")
    
    # 5. Migration de Recolte_quotidienne
    print("\n📆 Migration de l'onglet 'Recolte_quotidienne'...")
    try:
        recolte_quot = pd.read_excel(EXCEL_PATH, sheet_name="Recolte_quotidienne")
        if not recolte_quot.empty:
            count = 0
            for _, row in recolte_quot.iterrows():
                jour_semaine = str(row.get("jour_semaine", "")).strip()
                jour_semaine_num = row.get("jour_semaine_num")
                fraction_fraiseraie = row.get("fraction_fraiseraie")
                description = row.get("description")
                
                if pd.notna(jour_semaine_num) and pd.notna(fraction_fraiseraie):
                    try:
                        set_recolte_quotidienne(
                            jour_semaine=jour_semaine,
                            jour_semaine_num=int(jour_semaine_num),
                            fraction_fraiseraie=float(fraction_fraiseraie),
                            description=str(description) if pd.notna(description) else None
                        )
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Erreur pour {jour_semaine}: {e}")
            print(f"   ✅ {count} configurations de récolte quotidienne migrées")
        else:
            print("   ⚠️ Onglet 'Recolte_quotidienne' vide, utilisation des valeurs par défaut")
            # Valeurs par défaut
            defaults = [
                ("Lundi", 0, 1/3, "1/3 de la fraiseraie"),
                ("Mardi", 1, 1/3, "1/3 de la fraiseraie"),
                ("Mercredi", 2, 1/3, "1/3 de la fraiseraie"),
                ("Jeudi", 3, 1/2, "1/2 de la fraiseraie"),
                ("Vendredi", 4, 1/2, "1/2 de la fraiseraie"),
                ("Samedi", 5, 1/2, "1/2 de la fraiseraie"),
                ("Dimanche", 6, 0, "Pas de récolte")
            ]
            for jour, num, fraction, desc in defaults:
                set_recolte_quotidienne(jour, num, fraction, desc)
            print("   ✅ Valeurs par défaut créées")
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la migration de la récolte quotidienne : {e}")
        # Créer les valeurs par défaut en cas d'erreur
        defaults = [
            ("Lundi", 0, 1/3, "1/3 de la fraiseraie"),
            ("Mardi", 1, 1/3, "1/3 de la fraiseraie"),
            ("Mercredi", 2, 1/3, "1/3 de la fraiseraie"),
            ("Jeudi", 3, 1/2, "1/2 de la fraiseraie"),
            ("Vendredi", 4, 1/2, "1/2 de la fraiseraie"),
            ("Samedi", 5, 1/2, "1/2 de la fraiseraie"),
            ("Dimanche", 6, 0, "Pas de récolte")
        ]
        for jour, num, fraction, desc in defaults:
            set_recolte_quotidienne(jour, num, fraction, desc)
        print("   ✅ Valeurs par défaut créées")
    
    print("\n✅ Migration terminée avec succès !")
    print(f"📦 Base de données créée : recoltes.db")
    return True

if __name__ == "__main__":
    success = migrate_excel_to_db()
    sys.exit(0 if success else 1)

