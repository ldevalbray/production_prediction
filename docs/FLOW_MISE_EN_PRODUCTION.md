# Flow de Mise en Production - Pépinière Valbray

Ce document décrit le processus complet de mise en production de l'application, de la modification du code à la distribution aux utilisateurs.

## 📋 Vue d'ensemble

Le système de mise en production est entièrement automatisé via GitHub Actions. Deux types de releases sont disponibles :

1. **Builds automatiques** : Créés à chaque push sur `main`/`master` (prereleases)
2. **Releases stables** : Créées manuellement avec un tag versionné (releases officielles)

## 🚀 Processus de Mise en Production

### Option 1 : Build Automatique (Recommandé pour le développement continu)

#### Étapes

1. **Développement local**
   ```bash
   # Faire vos modifications
   git add .
   git commit -m "Description des changements"
   ```

2. **Push sur GitHub**
   ```bash
   git push origin main
   ```

3. **GitHub Actions se déclenche automatiquement**
   - ✅ Build Windows exécutable
   - ✅ Build macOS application
   - ✅ Création automatique d'une release GitHub
   - ✅ Tag automatique : `vYYYYMMDD-SHA` (ex: `v20250119-abc1234`)
   - ✅ Release marquée comme "prerelease" (build automatique)

4. **Les utilisateurs sont notifiés**
   - L'application détecte automatiquement la nouvelle version
   - Notification dans l'interface web
   - Mise à jour en un clic

#### Avantages
- ✅ Automatique, aucune action manuelle
- ✅ Rapide (disponible en ~15-20 minutes)
- ✅ Idéal pour les corrections de bugs et améliorations continues

#### Inconvénients
- ⚠️ Releases marquées comme "prerelease"
- ⚠️ Nom de version basé sur la date (moins sémantique)

---

### Option 2 : Release Stable (Recommandé pour les versions majeures)

#### Étapes

1. **Mettre à jour la version dans le code**
   ```bash
   # Éditer auto_updater.py
   APP_VERSION = "1.1.0"  # Nouvelle version
   ```

2. **Commit et push**
   ```bash
   git add auto_updater.py
   git commit -m "Version 1.1.0 - Description des changements"
   git push origin main
   ```

3. **Créer un tag de version**
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. **GitHub Actions se déclenche automatiquement**
   - ✅ Build Windows exécutable
   - ✅ Build macOS application
   - ✅ Création automatique d'une release GitHub
   - ✅ Tag : `v1.1.0`
   - ✅ Release marquée comme "stable" (non-prerelease)

5. **Les utilisateurs sont notifiés**
   - L'application détecte la nouvelle version stable
   - Notification dans l'interface web
   - Mise à jour en un clic

#### Avantages
- ✅ Version sémantique claire (1.0.0, 1.1.0, 2.0.0)
- ✅ Release stable (non-prerelease)
- ✅ Idéal pour les versions majeures et les annonces

#### Inconvénients
- ⚠️ Nécessite une action manuelle (création du tag)
- ⚠️ Doit mettre à jour `APP_VERSION` dans le code

---

## 📦 Structure des Releases

### Builds Automatiques (Prereleases)

**Format du tag** : `vYYYYMMDD-SHA`
- Exemple : `v20250119-abc1234`
- Date : 19 janvier 2025
- SHA : 7 premiers caractères du commit

**Contenu de la release** :
- `PepiniereValbray-Windows.zip` - Exécutable Windows
- `PepiniereValbray-macOS.dmg` - Application macOS
- Notes de version automatiques avec le message du commit

### Releases Stables

**Format du tag** : `vX.Y.Z` (Semantic Versioning)
- Exemple : `v1.0.0`, `v1.1.0`, `v2.0.0`
- X = Major (changements incompatibles)
- Y = Minor (nouvelles fonctionnalités)
- Z = Patch (corrections de bugs)

**Contenu de la release** :
- `PepiniereValbray-Windows.zip` - Exécutable Windows
- `PepiniereValbray-macOS.dmg` - Application macOS
- Notes de version personnalisables

---

## 🔄 Workflow Complet

### Développement → Production

```
┌─────────────────┐
│  Développement  │
│     Local       │
└────────┬────────┘
         │
         │ git commit
         │
         ▼
┌─────────────────┐
│  Push sur main  │
└────────┬────────┘
         │
         │ GitHub Actions
         │
         ▼
┌─────────────────┐
│  Build Windows  │
│  Build macOS    │
└────────┬────────┘
         │
         │ Automatique
         │
         ▼
┌─────────────────┐
│  Release GitHub │
│  (Prerelease)   │
└────────┬────────┘
         │
         │ Détection auto
         │
         ▼
┌─────────────────┐
│  Notification   │
│   Utilisateurs  │
└────────┬────────┘
         │
         │ Mise à jour
         │
         ▼
┌─────────────────┐
│  Installation   │
│   Automatique   │
└─────────────────┘
```

---

## 📝 Checklist de Mise en Production

### Avant chaque release

- [ ] Tester localement les modifications
- [ ] Vérifier que les tests passent (si applicable)
- [ ] Mettre à jour `APP_VERSION` dans `auto_updater.py` (pour releases stables)
- [ ] Vérifier que `requirements.txt` est à jour
- [ ] Compiler le frontend : `cd frontend && npm run build`
- [ ] Vérifier que les migrations de base de données sont prêtes (si nécessaire)

### Pour une release stable

- [ ] Créer un tag versionné : `git tag vX.Y.Z`
- [ ] Pousser le tag : `git push origin vX.Y.Z`
- [ ] Vérifier que la release est créée sur GitHub
- [ ] Tester le téléchargement et l'installation
- [ ] Vérifier que la mise à jour fonctionne depuis une version précédente

### Après la release

- [ ] Vérifier les logs GitHub Actions
- [ ] Tester l'exécutable Windows (si possible)
- [ ] Tester l'application macOS (si possible)
- [ ] Vérifier que les utilisateurs reçoivent la notification
- [ ] Documenter les changements dans les notes de release

---

## 🛠️ Commandes Utiles

### Créer une release stable

```bash
# 1. Mettre à jour la version
# Éditer auto_updater.py : APP_VERSION = "1.1.0"

# 2. Commit
git add auto_updater.py
git commit -m "Version 1.1.0"
git push origin main

# 3. Créer et pousser le tag
git tag v1.1.0
git push origin v1.1.0
```

### Vérifier les releases

```bash
# Lister les tags
git tag -l

# Voir les détails d'un tag
git show v1.1.0
```

### Annuler une release (si erreur)

```bash
# Supprimer le tag local
git tag -d v1.1.0

# Supprimer le tag sur GitHub
git push origin :refs/tags/v1.1.0

# Supprimer la release depuis l'interface GitHub (Releases → Delete)
```

---

## 🔍 Vérification Post-Release

### Vérifier que la release est disponible

1. Aller sur GitHub → Releases
2. Vérifier que la release apparaît
3. Vérifier que les fichiers sont téléchargeables
4. Tester le téléchargement d'un fichier

### Vérifier que la mise à jour fonctionne

1. Lancer une version précédente de l'application
2. Vérifier que la notification de mise à jour apparaît
3. Cliquer sur "Mettre à jour maintenant"
4. Vérifier que la mise à jour s'installe correctement
5. Vérifier que les données utilisateur sont préservées

### Vérifier les logs

```bash
# Logs GitHub Actions
# GitHub → Actions → Voir le workflow exécuté

# Logs de l'application
# Vérifier app.log pour les erreurs de mise à jour
```

---

## ⚠️ Points d'Attention

### Protection des Données

✅ **TOUJOURS préservées** :
- Base de données (`recoltes.db`)
- Prévisions (`forecasts/`)
- Modèles ML (`models/`)
- Fichiers de configuration

❌ **Jamais supprimées** lors d'une mise à jour

### Migrations de Base de Données

Si vous modifiez le schéma de la base de données :

1. Mettre à jour `auto_updater.py` dans `run_database_migrations()`
2. Incrémenter `target_schema_version` dans l'appel à `install_update()`
3. Tester la migration sur une copie de la base de données

### Version dans le Code

⚠️ **IMPORTANT** : Pour les releases stables, mettre à jour `APP_VERSION` dans `auto_updater.py` AVANT de créer le tag.

### Frontend

⚠️ **N'oubliez pas** : Compiler le frontend avant de créer une release :
```bash
cd frontend
npm run build
cd ..
```

---

## 📊 Monitoring

### Métriques à surveiller

- Taux de succès des builds GitHub Actions
- Temps de build (normalement 15-20 minutes)
- Erreurs de mise à jour dans les logs utilisateurs
- Taux d'adoption des nouvelles versions

### Logs à consulter

- GitHub Actions : `GitHub → Actions`
- Application : `app.log` dans le dossier de l'application
- Base de données : Vérifier l'intégrité après mise à jour

---

## 🚨 Dépannage

### Le build échoue

1. Vérifier les logs GitHub Actions
2. Vérifier que toutes les dépendances sont dans `requirements.txt`
3. Vérifier que le frontend compile correctement
4. Vérifier les erreurs de syntaxe Python

### La release n'est pas créée

1. Vérifier que le workflow s'est bien exécuté
2. Vérifier les permissions GitHub (GITHUB_TOKEN)
3. Vérifier que le job `create-release` s'est bien terminé

### Les utilisateurs ne voient pas la mise à jour

1. Vérifier que la release est bien publique
2. Vérifier que les assets sont bien attachés
3. Vérifier la connexion Internet de l'utilisateur
4. Vérifier les logs de l'application (`app.log`)

### Erreur lors de l'installation de la mise à jour

1. Vérifier les permissions d'écriture dans le dossier de l'application
2. Vérifier l'espace disque disponible
3. Vérifier les logs dans `app.log`
4. Restaurer depuis `backup_before_update/` si nécessaire

---

## 📚 Ressources

- [Guide de Build](./GUIDE_BUILD.md) - Détails sur la construction des exécutables
- [Guide de Mise à Jour](./GUIDE_MISE_A_JOUR.md) - Détails sur le système de mise à jour
- [Guide GitHub Actions](./GUIDE_GITHUB_ACTIONS.md) - Configuration des workflows
- [Guide Packaging](./GUIDE_PACKAGING.md) - Distribution et packaging

---

## 🎯 Bonnes Pratiques

1. **Tester avant de pousser** : Toujours tester localement avant de créer une release
2. **Messages de commit clairs** : Les messages de commit apparaissent dans les notes de release
3. **Versions sémantiques** : Utiliser Semantic Versioning pour les releases stables
4. **Documenter les changements** : Ajouter des notes de version détaillées
5. **Surveiller les builds** : Vérifier que les builds réussissent après chaque push
6. **Backup avant mise à jour** : Le système fait automatiquement un backup, mais vérifiez qu'il fonctionne

---

**Dernière mise à jour** : 2025-01-19

