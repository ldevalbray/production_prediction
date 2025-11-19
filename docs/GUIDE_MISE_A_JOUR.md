# Guide de Mise à Jour Automatique

Ce guide explique comment fonctionne le système de mise à jour automatique de l'application Pépinière Valbray.

## 🔒 Protection des Données Utilisateur

**IMPORTANT** : Le système de mise à jour **PRÉSERVE TOUTES LES DONNÉES UTILISATEUR** :

### ✅ Fichiers et dossiers protégés (NE SONT PAS SUPPRIMÉS) :

- **`recoltes.db`** : Base de données SQLite avec toutes vos données
- **`recoltes_fraises.xlsx`** : Fichier Excel (si utilisé)
- **`meteo_dataset.csv`** : Données météorologiques
- **`forecasts/`** : Toutes vos prévisions générées
- **`models/`** : Modèles ML entraînés localement
- **`models_archive/`** : Archives des modèles
- **`data/`** : Dossier de données utilisateur
- **`last_runs.json`** : Logs d'exécution
- **`app.log`** : Logs de l'application

### 🔄 Ce qui est mis à jour :

- Code de l'application (dossier `_internal/`)
- Exécutable principal
- Dépendances Python
- Structure de la base de données (migrations automatiques si nécessaire)

## 📋 Fonctionnement

### 1. Vérification automatique

Au démarrage de l'application, le système vérifie automatiquement s'il y a une nouvelle version disponible sur GitHub Releases.

### 2. Notification

Si une nouvelle version est disponible, une notification apparaît dans l'interface web avec :
- Version actuelle vs version disponible
- Notes de version
- Bouton pour mettre à jour

### 3. Mise à jour

Lorsque l'utilisateur clique sur "Mettre à jour maintenant" :

1. **Sauvegarde automatique** : Toutes les données utilisateur sont sauvegardées dans `backup_before_update/`
2. **Téléchargement** : La nouvelle version est téléchargée depuis GitHub
3. **Installation** : 
   - Remplacement du code de l'application
   - Restauration des données utilisateur depuis la sauvegarde
   - Exécution des migrations de base de données si nécessaire
4. **Redémarrage** : L'utilisateur doit redémarrer l'application

## 🔧 Migrations de Base de Données

Le système gère automatiquement les migrations de schéma de base de données :

- La table `schema_version` stocke la version actuelle du schéma
- Lors d'une mise à jour, les migrations nécessaires sont exécutées automatiquement
- Les données existantes sont préservées

### Ajouter une nouvelle migration

1. Modifier `auto_updater.py` dans la fonction `run_database_migrations()`
2. Incrémenter `target_schema_version` dans l'appel à `install_update()`
3. Ajouter le code de migration pour la nouvelle version

Exemple :
```python
# Migration vers version 2
if version == 2:
    cursor.execute("ALTER TABLE recoltes ADD COLUMN nouvelle_colonne TEXT")
```

## 📝 Mise à jour de la version

Pour chaque nouvelle release :

1. **Mettre à jour `APP_VERSION`** dans `auto_updater.py` :
   ```python
   APP_VERSION = "1.1.0"  # Nouvelle version
   ```

2. **Créer un tag Git** :
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

3. **GitHub Actions** va automatiquement :
   - Construire les exécutables
   - Créer une release GitHub
   - Les utilisateurs pourront mettre à jour depuis cette release

## 🛡️ Sécurité

- Les données sont toujours sauvegardées avant la mise à jour
- En cas d'erreur, restauration automatique depuis la sauvegarde
- Les fichiers protégés ne sont jamais supprimés

## ⚠️ Notes importantes

1. **Redémarrage requis** : Après une mise à jour, l'application doit être redémarrée
2. **Connexion Internet** : Nécessaire pour vérifier et télécharger les mises à jour
3. **Permissions** : L'application doit avoir les permissions d'écriture dans son dossier

## 🔍 Dépannage

### La mise à jour ne fonctionne pas

1. Vérifier la connexion Internet
2. Vérifier que GitHub Releases est accessible
3. Vérifier les logs dans `app.log`

### Restauration manuelle

Si quelque chose ne va pas, vous pouvez restaurer manuellement depuis la sauvegarde :

```bash
# Le dossier backup_before_update/ contient toutes vos données
# Copiez les fichiers nécessaires depuis ce dossier
```

### Désactiver les mises à jour automatiques

Pour désactiver temporairement les vérifications de mise à jour, commentez cette ligne dans `app.py` :

```python
# threading.Thread(target=check_updates_async, daemon=True).start()
```

