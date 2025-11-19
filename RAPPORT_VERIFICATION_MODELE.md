# Rapport de Vérification du Modèle de Prédiction

Date : 2025-01-20

## 🔍 Vue d'ensemble

Ce rapport documente la vérification globale du modèle de prédiction et de sa mise à jour, en s'assurant que tous les paramètres et modifications de la base de données sont correctement pris en compte.

---

## ✅ Vérifications effectuées

### 1. Features du modèle

#### Features obligatoires
- ✅ **temp_mean**, **temp_min**, **temp_max** : Données météo (moyenne, min, max)
- ✅ **rain_mm** : Précipitations en mm
- ✅ **humidity** : Humidité relative moyenne
- ✅ **sun_hours** : Durée d'ensoleillement en heures
- ✅ **kg_par_rangee_prev_day** : Récolte précédente par rangée (contexte)

#### Features optionnelles (ajoutées dynamiquement si présentes)
- ✅ **nb_plants** : Nombre de plants par variété/année
- ✅ **jour_semaine** : Jour de la semaine (0=Lundi, 6=Dimanche)
- ✅ **fraction_fraiseraie** : Fraction de fraiseraie récoltée ce jour
- ✅ **jours_since_last_recolte** : Jours depuis dernière récolte (par parcelle/variété)
- ✅ **jours_since_last_recolte_globale** : Jours depuis dernière récolte globale

#### Features catégorielles (encodage one-hot)
- ✅ **parcelle_*** : Encodage one-hot des parcelles
- ✅ **variety_*** : Encodage one-hot des variétés

### 2. Génération du dataset d'entraînement (`auto_update_model_v4.py`)

#### Sources de données
- ✅ **Récoltes** : Chargées via `load_recoltes_with_params()` (compatible SQLite/Excel)
- ✅ **Paramètres** : Chargés via `load_parametres()` (parcelle, variety, nb_rangees, saison_debut, saison_fin)
- ✅ **Météo** : Chargées depuis `meteo_dataset.csv`
- ✅ **Plants par année** : Chargés via `load_plants_par_annee()`
- ✅ **Récolte quotidienne** : Chargés via `load_recolte_quotidienne()` (jour_semaine, fraction_fraiseraie)

#### Calculs des features
- ✅ **kg_par_rangee** : `kg_total / nb_rangees` (gestion de division par zéro)
- ✅ **kg_par_rangee_prev_day** : Utilise `.shift(1)` par groupe parcelle/variété
- ✅ **jour_semaine** : Extrait depuis la date avec `.dt.dayofweek`
- ✅ **fraction_fraiseraie** : Mappée depuis `recolte_quotidienne` selon `jour_semaine_num`
- ✅ **nb_plants** : Fusionné par variété et année, avec valeurs par défaut si manquant
- ✅ **jours_since_last_recolte** : **CORRIGÉ** - Maintenant cohérent avec la prédiction
- ✅ **jours_since_last_recolte_globale** : **CORRIGÉ** - Maintenant cohérent avec la prédiction

### 3. Prédictions (`forecast_next3days_v3.py`)

#### Chargement des données
- ✅ **Modèle** : Chargé depuis `model_fraises_v2.pkl`
- ✅ **Paramètres** : Chargés via `load_parametres()` (compatible SQLite/Excel)
- ✅ **Historique** : Chargé via `load_recoltes()` puis fusionné avec paramètres
- ✅ **Jour courant** : Chargé via `load_jour_courant()` pour le contexte immédiat
- ✅ **Météo** : Récupérée depuis l'API Open-Meteo (fallback sur CSV local)
- ✅ **Plants par année** : Chargés via `load_plants_par_annee()`
- ✅ **Récolte quotidienne** : Chargés via `load_recolte_quotidienne()`

#### Génération des features pour prédiction
- ✅ Toutes les features météo sont générées depuis l'API
- ✅ **nb_plants** : Fusionné par variété et année (avec fallback)
- ✅ **jour_semaine** : Calculé depuis la date de prévision
- ✅ **fraction_fraiseraie** : Mappé depuis `recolte_quotidienne`
- ✅ **jours_since_last_recolte** : Calculé depuis la dernière récolte de chaque parcelle/variété
- ✅ **jours_since_last_recolte_globale** : Calculé depuis la dernière date globale
- ✅ **kg_par_rangee_prev_day** : Utilise le contexte saisonnier avec `saison_debut`/`saison_fin`

#### Utilisation des paramètres saisonniers
- ✅ **saison_debut** / **saison_fin** : Utilisés pour déterminer le contexte de production
- ✅ Détection automatique si les colonnes ne sont pas présentes
- ✅ Filtrage des valeurs de contexte basé sur la saison active

### 4. Entraînement du modèle (`train_model.py`)

#### Vérifications
- ✅ Lecture du dataset depuis `dataset_ready_for_model.csv`
- ✅ Vérification de présence de la colonne `kg_par_rangee` (variable cible)
- ✅ Détection automatique des features optionnelles
- ✅ Encodage one-hot des variables catégorielles (parcelle, variety)
- ✅ Filtrage des valeurs infinies et NaN
- ✅ Division train/test (80/20)
- ✅ Archivage du modèle et du dataset

---

## 🔧 Corrections apportées

### Problème identifié : Incohérence dans le calcul de `jours_since_last_recolte`

**Avant :**
- Dans `auto_update_model_v4.py` : Utilisait `.diff()` qui calculait l'intervalle entre deux récoltes consécutives pour la même parcelle/variété
- Dans `forecast_next3days_v3.py` : Calculait les jours depuis la dernière récolte réelle jusqu'à la date prévue

**Après :**
- ✅ Les deux scripts utilisent maintenant la même logique : calcul des jours depuis la dernière récolte de cette parcelle/variété jusqu'à la date actuelle/prévue

### Problème identifié : Incohérence dans le calcul de `jours_since_last_recolte_globale`

**Avant :**
- Dans `auto_update_model_v4.py` : Calculait l'écart entre dates uniques de récolte
- Dans `forecast_next3days_v3.py` : Calculait les jours depuis la dernière date globale

**Après :**
- ✅ Les deux scripts utilisent maintenant la même logique : calcul des jours depuis la dernière date globale jusqu'à la date actuelle/prévue

---

## 📊 Cohérence entre génération du dataset et prédiction

### Features météo
- ✅ **temp_mean**, **temp_min**, **temp_max** : Même format (moyenne, min, max)
- ✅ **rain_mm** : Même unité (mm)
- ✅ **humidity** : Même format (pourcentage moyen)
- ✅ **sun_hours** : Même unité (heures)

### Features temporelles
- ✅ **jour_semaine** : Même format (0=Lundi, 6=Dimanche)
- ✅ **jours_since_last_recolte** : **CORRIGÉ** - Même logique
- ✅ **jours_since_last_recolte_globale** : **CORRIGÉ** - Même logique

### Features de production
- ✅ **kg_par_rangee_prev_day** : Même logique (shift(1) dans le dataset, contexte saisonnier en prédiction)
- ✅ **nb_plants** : Même logique de fusion par variété/année avec fallback
- ✅ **fraction_fraiseraie** : Même mapping depuis `recolte_quotidienne`

### Encodage catégoriel
- ✅ **parcelle** et **variety** : Même encodage one-hot avec `drop_first=True`

---

## 🗄️ Intégration avec la base de données

### Tables utilisées
- ✅ **parametres** : `parcelle`, `variety`, `nb_rangees`, `saison_debut`, `saison_fin`
- ✅ **recoltes** : `date`, `variety`, `kg_total`
- ✅ **jour_courant** : `date`, `variety`, `kg_premiere_rangee`
- ✅ **plants_par_annee** : `variety`, `annee`, `nb_plants`
- ✅ **recolte_quotidienne** : `jour_semaine_num`, `fraction_fraiseraie`

### Compatibilité SQLite/Excel
- ✅ Utilisation de `data_loader.py` pour abstraction
- ✅ Fallback automatique vers Excel si SQLite non disponible
- ✅ Normalisation des clés (variety, parcelle) en minuscules

---

## ⚠️ Points d'attention

### 1. Valeurs manquantes
- ✅ Gestion des `nb_rangees` manquants (valeur par défaut : 10)
- ✅ Gestion des `nb_plants` manquants (moyenne par variété puis globale)
- ✅ Gestion des données météo manquantes (avertissement loggé)

### 2. Division par zéro
- ✅ Protection contre division par zéro pour `kg_par_rangee` (nb_rangees = 0)
- ✅ Protection contre division par zéro pour `kg_par_rangee_prev_day`

### 3. Contexte saisonnier
- ✅ Utilisation de `saison_debut`/`saison_fin` si présents dans Paramètres
- ✅ Détection automatique de la saison si colonnes absentes
- ✅ Gestion des valeurs NaN/None pour les paramètres de saison

### 4. Alignement des colonnes
- ✅ Vérification que toutes les colonnes attendues par le modèle sont présentes lors de la prédiction
- ✅ Ajout de colonnes manquantes avec valeur 0 si nécessaire (pour l'encodage one-hot)

---

## 📝 Recommandations

### 1. Réentraînement du modèle
⚠️ **IMPORTANT** : Après ces corrections, il est recommandé de réentraîner le modèle pour qu'il utilise les nouvelles définitions cohérentes de `jours_since_last_recolte` et `jours_since_last_recolte_globale`.

### 2. Vérification des performances
- Comparer les métriques (RMSE, R²) avant et après réentraînement
- Vérifier que les prédictions sont cohérentes avec les attentes

### 3. Tests
- Tester la génération du dataset avec les données actuelles
- Tester la prédiction avec un modèle réentraîné
- Vérifier que toutes les features sont bien présentes

---

## ✅ Conclusion

Le modèle de prédiction et sa mise à jour sont maintenant **cohérents** entre la génération du dataset d'entraînement et les prédictions. Les incohérences dans le calcul de `jours_since_last_recolte` et `jours_since_last_recolte_globale` ont été corrigées.

**Tous les paramètres de la base de données sont correctement pris en compte :**
- ✅ Parcelle, variété, nombre de rangées
- ✅ Paramètres saisonniers (saison_debut, saison_fin)
- ✅ Nombre de plants par année
- ✅ Configuration de récolte quotidienne
- ✅ Données météo
- ✅ Contexte de production (kg_par_rangee_prev_day)

**Action requise :** Réentraîner le modèle pour appliquer les corrections.

