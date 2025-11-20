#!/usr/bin/env python3
"""
Script pour créer un template Excel vide avec la structure correcte.
Ce template peut être utilisé pour importer des données dans l'application.
"""
import pandas as pd
from pathlib import Path
import sys

def create_excel_template(output_path: str = "data/recoltes_fraises_template.xlsx"):
    """Crée un fichier Excel template avec la structure correcte."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📝 Création du template Excel : {output_path}")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 1. Onglet "Paramètres"
        params_df = pd.DataFrame(columns=[
            'parcelle', 'variety', 'nb_rangees', 'saison_debut', 'saison_fin'
        ])
        params_df.to_excel(writer, sheet_name='Paramètres', index=False)
        print("   ✅ Onglet 'Paramètres' créé")
        
        # 2. Onglet "Recoltes"
        recoltes_df = pd.DataFrame(columns=[
            'date', 'variety', 'kg_total', 'commentaires'
        ])
        recoltes_df.to_excel(writer, sheet_name='Recoltes', index=False)
        print("   ✅ Onglet 'Recoltes' créé")
        
        # 3. Onglet "Jour_courant"
        jour_courant_df = pd.DataFrame(columns=[
            'date', 'variety', 'kg_premiere_rangee', 'commentaires'
        ])
        jour_courant_df.to_excel(writer, sheet_name='Jour_courant', index=False)
        print("   ✅ Onglet 'Jour_courant' créé")
        
        # 4. Onglet "Plants_par_annee"
        plants_df = pd.DataFrame(columns=[
            'variety', 'Année', 'Nb_plants'
        ])
        plants_df.to_excel(writer, sheet_name='Plants_par_annee', index=False)
        print("   ✅ Onglet 'Plants_par_annee' créé")
        
        # 5. Onglet "Recolte_quotidienne"
        recolte_quot_df = pd.DataFrame(columns=[
            'jour_semaine', 'jour_semaine_num', 'fraction_fraiseraie', 'description'
        ])
        # Ajouter des valeurs par défaut
        defaults = [
            {"jour_semaine": "Lundi", "jour_semaine_num": 0, "fraction_fraiseraie": 1/3, "description": "1/3 de la fraiseraie"},
            {"jour_semaine": "Mardi", "jour_semaine_num": 1, "fraction_fraiseraie": 1/3, "description": "1/3 de la fraiseraie"},
            {"jour_semaine": "Mercredi", "jour_semaine_num": 2, "fraction_fraiseraie": 1/3, "description": "1/3 de la fraiseraie"},
            {"jour_semaine": "Jeudi", "jour_semaine_num": 3, "fraction_fraiseraie": 1/2, "description": "1/2 de la fraiseraie"},
            {"jour_semaine": "Vendredi", "jour_semaine_num": 4, "fraction_fraiseraie": 1/2, "description": "1/2 de la fraiseraie"},
            {"jour_semaine": "Samedi", "jour_semaine_num": 5, "fraction_fraiseraie": 1/2, "description": "1/2 de la fraiseraie"},
            {"jour_semaine": "Dimanche", "jour_semaine_num": 6, "fraction_fraiseraie": 0, "description": "Pas de récolte"}
        ]
        recolte_quot_df = pd.DataFrame(defaults)
        recolte_quot_df.to_excel(writer, sheet_name='Recolte_quotidienne', index=False)
        print("   ✅ Onglet 'Recolte_quotidienne' créé (avec valeurs par défaut)")
    
    print(f"\n✅ Template Excel créé avec succès : {output_path}")
    return str(output_path)

if __name__ == "__main__":
    # Créer le template dans data/
    template_path = create_excel_template()
    sys.exit(0)

