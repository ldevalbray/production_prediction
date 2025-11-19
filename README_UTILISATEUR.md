# Guide d'utilisation - Système de Prédiction de Récoltes

## 🎯 Introduction

Ce système vous permet de prédire les récoltes de fraises pour les 3 prochains jours en utilisant l'intelligence artificielle. Il prend en compte les données historiques, la météo, et l'organisation de vos récoltes.

## 🚀 Démarrage rapide

### Option 1 : Utiliser l'exécutable (recommandé - aucune installation requise)

Si vous avez reçu un exécutable standalone :

1. **Double-cliquez** sur l'exécutable :
   - Windows : `PepiniereValbray.exe`
   - macOS : `PepiniereValbray.app`
   - Linux : `PepiniereValbray`

2. L'application s'ouvre directement, **aucune installation n'est nécessaire** !

### Option 2 : Lancer depuis Python (pour développeurs)

Double-cliquez sur `launcher_gui.py` ou exécutez dans un terminal :
```bash
python3 launcher_gui.py
```

**Note** : Cette méthode nécessite Python et toutes les dépendances installées.

### Interface

Une fenêtre s'ouvre avec deux boutons principaux :
- **"Mettre à jour le modèle"** : Réentraîne le modèle avec les dernières données
- **"Générer prévisions"** : Crée les prévisions pour les 3 prochains jours

## 📊 Fichier Excel principal : `recoltes_fraises.xlsx`

Ce fichier contient toutes vos données. Il comporte 5 onglets :

### 1. Onglet "Recoltes" 📅

**À quoi ça sert ?** Historique de toutes vos récoltes passées.

**Colonnes à remplir :**
- **date** : Date de la récolte (ex: 2025-01-15)
- **variety** : Nom de la variété (ex: clery, manon, ciflorette, dream)
- **kg_total** : Nombre total de kg récoltés
- **commentaires** : (optionnel) Notes diverses

**Important :** Ajoutez régulièrement vos nouvelles récoltes ici pour améliorer les prédictions.

### 2. Onglet "Paramètres" ⚙️

**À quoi ça sert ?** Configuration de vos parcelles et variétés.

**Colonnes à remplir :**
- **parcelle** : Nom de la parcelle (ex: Parcelle_1, Parcelle_2)
- **variety** : Nom de la variété (doit correspondre à "Recoltes")
- **nb_rangees** : Nombre de rangées pour cette combinaison (peut rester vide, valeur par défaut : 10)

**Exemple :**
| parcelle | variety | nb_rangees |
|----------|---------|------------|
| Parcelle_1 | clery | 12 |
| Parcelle_1 | manon | 12 |
| Parcelle_2 | ciflorette | 10 |

### 3. Onglet "Jour_courant" ☀️

**À quoi ça sert ?** Données du jour en cours (optionnel, peut être vide le matin).

**Quand le remplir ?** Après avoir fait vos récoltes du jour, pour améliorer les prévisions du lendemain.

**Colonnes à remplir :**
- **date** : Date du jour (ex: 2025-01-15)
- **variety** : Nom de la variété
- **kg_premiere_rangee** : Kg récoltés sur la première rangée (pour estimation)
- **commentaires** : (optionnel)

**Note :** Si vous ne remplissez pas cet onglet, le système utilisera uniquement les données historiques (c'est normal le matin avant les récoltes).

### 4. Onglet "Plants_par_annee" 🌱

**À quoi ça sert ?** Nombre de plants par variété et par année.

**Colonnes à remplir :**
- **variety** : Nom de la variété
- **Année** : Année (ex: 2025)
- **Nb_plants** : Nombre total de plants

**Exemple :**
| variety | Année | Nb_plants |
|---------|-------|-----------|
| clery | 2025 | 20580 |
| manon | 2025 | 21120 |

### 5. Onglet "Recolte_quotidienne" 📆

**À quoi ça sert ?** Configuration de votre organisation hebdomadaire des récoltes.

**Colonnes :**
- **jour_semaine** : Nom du jour (Lundi, Mardi, etc.)
- **jour_semaine_num** : Numéro du jour (0=Lundi, 6=Dimanche) - **Ne pas modifier**
- **fraction_fraiseraie** : Fraction de la fraiseraie récoltée ce jour (ex: 0.333 = 1/3, 0.5 = 1/2)
- **description** : Description (informative)

**Vous pouvez modifier :**
- La colonne **fraction_fraiseraie** si votre organisation change

**Exemple par défaut :**
- Lundi/Mardi/Mercredi : 0.333 (1/3 de la fraiseraie)
- Jeudi/Vendredi/Samedi : 0.5 (1/2 de la fraiseraie)
- Dimanche : 0 (pas de récolte)

## 🔄 Utilisation quotidienne

### Le matin (avant les récoltes)

1. **Générer les prévisions** :
   - Cliquez sur "Générer prévisions"
   - Attendez quelques secondes
   - Les prévisions sont sauvegardées dans le dossier `forecasts/`
   - Un fichier Excel s'ouvre automatiquement avec les prévisions

2. **Consulter les prévisions** :
   - Le fichier Excel contient les prédictions pour les 3 prochains jours
   - Pour chaque parcelle/variété, vous verrez :
     - La prédiction en kg total
     - Un intervalle de confiance (min/max)
     - Les conditions météo prévues (températures, pluie, humidité, ensoleillement)

### Le soir (après les récoltes)

1. **Mettre à jour les données** :
   - Ajoutez vos récoltes du jour dans l'onglet "Recoltes"
   - (Optionnel) Remplissez "Jour_courant" avec les données du jour

2. **Mettre à jour le modèle** (1-2 fois par semaine) :
   - Cliquez sur "Mettre à jour le modèle"
   - Cela réentraîne le modèle avec toutes les nouvelles données
   - Le processus prend quelques minutes

## 📁 Fichiers générés

### Prévisions
- **Emplacement** : Dossier `forecasts/`
- **Nom** : `forecast_next3days_YYYY-MM-DD.xlsx`
- **Contenu** : Prévisions détaillées pour les 3 prochains jours

### Description des colonnes du fichier de prévisions

Le fichier Excel de prévisions contient les colonnes suivantes :

#### Informations de base
- **date** : Date de la prévision (format : YYYY-MM-DD)
- **horizon** : Jours à l'avance (J+1, J+2, J+3)
- **parcelle** : Nom de la parcelle concernée
- **variety** : Nom de la variété de fraises

#### Données météorologiques prévues
- **temp_mean** : Température moyenne prévue (°C)
- **temp_min** : Température minimale prévue (°C)
- **temp_max** : Température maximale prévue (°C)
- **rain_mm** : Précipitations prévues (mm)
- **humidity** : Humidité relative prévue (%)
- **sun_hours** : Heures d'ensoleillement prévues

#### Prédictions de récolte (par rangée)
- **predicted_kg_par_rangee** : Prédiction de kg récoltés par rangée
- **predicted_std_par_rangee** : Écart-type de la prédiction (incertitude) par rangée

#### Paramètres
- **nb_rangees** : Nombre de rangées pour cette parcelle/variété

#### Prédictions de récolte (total)
- **predicted_kg_total** : Prédiction totale de kg récoltés (pour toutes les rangées)
- **predicted_std_kg_total** : Écart-type de la prédiction totale (incertitude)
- **confidence_min_kg_total** : Minimum de l'intervalle de confiance (kg)
- **confidence_max_kg_total** : Maximum de l'intervalle de confiance (kg)

**Note** : L'intervalle de confiance (min/max) vous donne une fourchette probable. La vraie récolte devrait se situer entre ces deux valeurs dans la plupart des cas.

### Modèles archivés
- **Emplacement** : Dossier `models_archive/`
- **Contenu** : Sauvegarde automatique des modèles et datasets à chaque mise à jour

## ❓ Questions fréquentes

### Le fichier "Jour_courant" est vide, est-ce normal ?
**Oui !** C'est normal le matin avant les récoltes. Le système utilisera les données historiques pour faire les prévisions.

### À quelle fréquence dois-je mettre à jour le modèle ?
**Recommandation** : 1 à 2 fois par semaine, ou après avoir ajouté beaucoup de nouvelles données de récoltes.

### Les prévisions sont-elles fiables ?
Le modèle s'améliore avec le temps. Plus vous ajoutez de données historiques, plus les prédictions seront précises. Les prévisions incluent un intervalle de confiance pour vous donner une fourchette.

### Puis-je modifier l'organisation hebdomadaire des récoltes ?
**Oui !** Modifiez simplement la colonne `fraction_fraiseraie` dans l'onglet "Recolte_quotidienne". Les changements seront pris en compte lors de la prochaine génération de prévisions.

### Que faire si j'ajoute une nouvelle variété ?
1. Ajoutez-la dans l'onglet "Paramètres" avec sa parcelle et nb_rangees
2. Ajoutez ses récoltes dans l'onglet "Recoltes"
3. Ajoutez ses données de plants dans "Plants_par_annee"
4. Mettez à jour le modèle

### Le système nécessite-t-il Internet ?
**Oui**, pour les prévisions météo. Les prévisions utilisent une API météo en ligne pour obtenir les conditions des 3 prochains jours.

## 🆘 En cas de problème

### L'interface ne s'ouvre pas

**Si vous utilisez l'exécutable :**
- Vérifiez que tous les fichiers nécessaires sont présents (voir section "Fichiers nécessaires" ci-dessous)
- Sur macOS : Autorisez l'application dans Paramètres Système > Sécurité
- Sur Windows : L'antivirus peut bloquer l'exécutable (ajoutez une exception)

**Si vous utilisez Python directement :**
- Vérifiez que Python 3 est installé
- Vérifiez que les bibliothèques sont installées : `pip install -r requirements.txt`

### Erreur lors de la génération de prévisions
- Vérifiez que le fichier `model_fraises_v2.pkl` existe
- Vérifiez votre connexion Internet (pour les données météo)
- Vérifiez que l'onglet "Paramètres" contient au moins une ligne

### Erreur lors de la mise à jour du modèle
- Vérifiez que l'onglet "Recoltes" contient des données
- Vérifiez que le fichier `meteo_dataset.csv` existe
- Vérifiez que les dates dans "Recoltes" sont au format correct

### Les prévisions semblent incorrectes
- Vérifiez que vous avez assez de données historiques (au moins quelques semaines)
- Mettez à jour le modèle avec les dernières données
- Vérifiez que les paramètres (nb_rangees, fraction_fraiseraie) sont corrects

## 📁 Fichiers nécessaires

L'application nécessite les fichiers suivants dans le même dossier que l'exécutable :

- ✅ **recoltes_fraises.xlsx** : Fichier principal avec toutes vos données (obligatoire)
- ✅ **meteo_dataset.csv** : Données météo historiques (obligatoire)
- ⚠️ **model_fraises_v2.pkl** : Modèle d'IA (sera créé automatiquement au premier lancement si absent)

Les dossiers suivants seront créés automatiquement :
- `forecasts/` : Contient les prévisions générées
- `models_archive/` : Contient les sauvegardes des modèles

## 📞 Support

Pour toute question technique ou problème, consultez le `README_TECHNIQUE.md` ou le `GUIDE_BUILD.md` (pour créer votre propre exécutable).

## 🔨 Créer votre propre exécutable

Si vous souhaitez créer un exécutable standalone pour distribuer l'application, consultez le fichier `GUIDE_BUILD.md` qui contient toutes les instructions détaillées.

## 💡 Conseils pour de meilleures prédictions

1. **Données régulières** : Ajoutez vos récoltes régulièrement dans "Recoltes"
2. **Données complètes** : Remplissez "Jour_courant" après chaque journée de récolte
3. **Paramètres à jour** : Mettez à jour "Plants_par_annee" chaque année
4. **Modèle à jour** : Réentraînez le modèle régulièrement (1-2 fois/semaine)
5. **Organisation réelle** : Ajustez "Recolte_quotidienne" si votre organisation change

---

**Bonne utilisation ! 🌱🍓**

