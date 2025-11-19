# Guide d'utilisation de la base de données SQLite

## 🎯 Vue d'ensemble

Le système a été amélioré pour utiliser une **base de données SQLite** au lieu d'Excel pour stocker les données. Cela offre de nombreux avantages :

- ✅ **Interface web de saisie** : Plus besoin de modifier Excel manuellement
- ✅ **Validation automatique** : Moins d'erreurs de saisie
- ✅ **Historique complet** : Traçabilité avec timestamps
- ✅ **Export Excel optionnel** : Pour archivage ou compatibilité
- ✅ **Compatibilité maintenue** : Les scripts existants fonctionnent toujours

## 🚀 Démarrage rapide

### 1. Migration des données Excel vers SQLite

Si vous avez déjà un fichier `recoltes_fraises.xlsx`, migrez vos données :

```bash
python migrate_excel_to_db.py
```

Cela va :
- Créer la base de données `recoltes.db`
- Migrer toutes les données depuis Excel
- Conserver votre fichier Excel intact

### 2. Utilisation de l'interface web

Lancez l'application web :

```bash
python app.py
```

Puis ouvrez votre navigateur sur `http://localhost:5000` et cliquez sur l'onglet **"Saisie"** pour :
- Ajouter des récoltes
- Gérer les paramètres (parcelles/variétés)
- Voir l'historique

### 3. Les scripts continuent de fonctionner

Les scripts `auto_update_model_v4.py` et `forecast_next3days_v3.py` utilisent automatiquement la base de données si elle existe, sinon ils utilisent Excel (compatibilité arrière).

## 📊 Structure de la base de données

La base de données SQLite (`recoltes.db`) contient 5 tables :

### 1. `parametres`
Configuration des parcelles et variétés
- `parcelle` : Nom de la parcelle
- `variety` : Nom de la variété
- `nb_rangees` : Nombre de rangées
- `saison_debut` / `saison_fin` : (optionnel) Mois de début/fin de saison

### 2. `recoltes`
Historique de toutes les récoltes
- `date` : Date de la récolte
- `variety` : Variété
- `kg_total` : Kg récoltés
- `commentaires` : Notes optionnelles

### 3. `jour_courant`
Données du jour en cours
- `date` : Date du jour
- `variety` : Variété
- `kg_premiere_rangee` : Kg sur la première rangée

### 4. `plants_par_annee`
Nombre de plants par variété et année
- `variety` : Variété
- `annee` : Année
- `nb_plants` : Nombre de plants

### 5. `recolte_quotidienne`
Configuration de l'organisation hebdomadaire
- `jour_semaine` : Nom du jour
- `jour_semaine_num` : Numéro (0=Lundi, 6=Dimanche)
- `fraction_fraiseraie` : Fraction récoltée ce jour

## 🔄 Migration progressive

Le système fonctionne en **mode hybride** :

1. **Si `recoltes.db` existe** → Utilise la base de données
2. **Sinon** → Utilise Excel (comportement par défaut)

Pour forcer l'utilisation d'Excel, définissez la variable d'environnement :
```bash
export USE_DB=false
python auto_update_model_v4.py
```

## 📝 API REST

L'application expose une API REST pour gérer les données :

### Récoltes
- `GET /api/recoltes` - Liste des récoltes
- `POST /api/recoltes` - Ajouter une récolte
- `PUT /api/recoltes/:id` - Modifier une récolte
- `DELETE /api/recoltes/:id` - Supprimer une récolte

### Paramètres
- `GET /api/parametres` - Liste des paramètres
- `POST /api/parametres` - Ajouter un paramètre
- `PUT /api/parametres/:id` - Modifier un paramètre
- `DELETE /api/parametres/:id` - Supprimer un paramètre

### Jour courant
- `GET /api/jour-courant` - Données du jour courant
- `POST /api/jour-courant` - Enregistrer les données du jour
- `DELETE /api/jour-courant` - Effacer les données du jour

### Export
- `POST /api/export-excel` - Exporter toutes les données vers Excel

## 🔧 Utilisation en ligne de commande

### Initialiser la base de données

```python
from database import init_database
init_database()
```

### Ajouter une récolte

```python
from database import add_recolte
add_recolte(date="2025-01-15", variety="clery", kg_total=125.5, commentaires="Bonne récolte")
```

### Exporter vers Excel

```python
from database import export_to_excel
export_to_excel("recoltes_export.xlsx")
```

## ⚠️ Notes importantes

1. **Sauvegarde** : La base de données SQLite est un fichier unique (`recoltes.db`). Pensez à le sauvegarder régulièrement.

2. **Compatibilité** : Les scripts existants continuent de fonctionner avec Excel si la base de données n'existe pas.

3. **Migration** : Vous pouvez migrer vos données à tout moment avec `migrate_excel_to_db.py`.

4. **Export** : Utilisez `export_to_excel()` pour créer un fichier Excel à partir de la base de données.

## 🆘 Dépannage

### La base de données n'est pas créée
```bash
python migrate_excel_to_db.py
```

### Erreur "Module database.py non disponible"
Vérifiez que le fichier `database.py` est présent dans le répertoire.

### Les scripts utilisent toujours Excel
Vérifiez que `recoltes.db` existe et que `USE_DB=true` (par défaut).

### Besoin de revenir à Excel uniquement
Supprimez ou renommez `recoltes.db`, les scripts utiliseront automatiquement Excel.

---

**Bon usage ! 🌱🍓**

