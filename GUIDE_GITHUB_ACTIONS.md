# Guide GitHub Actions - Build Automatique

Ce guide explique comment utiliser GitHub Actions pour construire automatiquement les exécutables Windows et macOS sans avoir besoin de machines physiques.

## 🚀 Avantages

- ✅ **Gratuit** : GitHub Actions offre 2000 minutes/mois gratuites
- ✅ **Automatique** : Builds déclenchés automatiquement
- ✅ **Multi-plateforme** : Windows et macOS en parallèle
- ✅ **Pas de machine physique** : Tout se fait dans le cloud

## 📋 Prérequis

1. Un compte GitHub
2. Votre projet doit être sur GitHub (repository public ou privé)
3. Les fichiers de workflow sont déjà créés dans `.github/workflows/`

## 🔧 Configuration

### 1. Pousser votre code sur GitHub

```bash
# Si ce n'est pas déjà fait, initialisez git et poussez votre code
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
git push -u origin main
```

### 2. Vérifier les workflows

Les workflows sont automatiquement activés une fois poussés sur GitHub. Vérifiez dans l'onglet **Actions** de votre repository.

## 🎯 Utilisation

### Option A : Build automatique sur push de tag (Releases)

Pour créer une release avec les exécutables :

```bash
# Créer un tag de version
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0
```

GitHub Actions va :
1. Construire les exécutables Windows et macOS
2. Créer automatiquement une release GitHub
3. Attacher les fichiers ZIP/DMG à la release

**Résultat** : Une release GitHub avec les fichiers téléchargeables

### Option B : Build manuel (Workflow Dispatch)

1. Allez sur votre repository GitHub
2. Cliquez sur l'onglet **Actions**
3. Sélectionnez le workflow **Build Executables**
4. Cliquez sur **Run workflow**
5. Choisissez la branche et cliquez sur **Run workflow**

**Résultat** : Les artefacts sont disponibles dans l'onglet Actions (conservés 30 jours)

### Option C : Build automatique sur push (Développement)

Le workflow `build-on-push.yml` se déclenche automatiquement quand vous poussez sur `main`, `master` ou `develop`.

**Résultat** : Les artefacts sont disponibles dans l'onglet Actions (conservés 7 jours)

## 📥 Télécharger les Exécutables

### Depuis une Release

1. Allez sur votre repository GitHub
2. Cliquez sur **Releases** (à droite)
3. Téléchargez le fichier correspondant à votre système :
   - `PepiniereValbray-Windows.zip` pour Windows
   - `PepiniereValbray-macOS.dmg` pour macOS

### Depuis les Artifacts

1. Allez sur l'onglet **Actions**
2. Cliquez sur le workflow qui vous intéresse
3. Cliquez sur le job (Windows ou macOS)
4. Dans la section **Artifacts**, téléchargez le fichier

## 🔍 Vérifier les Builds

### Voir les logs

1. Allez sur **Actions**
2. Cliquez sur un workflow
3. Cliquez sur un job pour voir les logs détaillés

### Résoudre les erreurs

Si un build échoue :
1. Consultez les logs pour identifier l'erreur
2. Vérifiez que tous les fichiers nécessaires sont présents
3. Vérifiez que `requirements.txt` est à jour
4. Vérifiez que le frontend compile correctement

## 📝 Personnalisation

### Modifier les déclencheurs

Éditez `.github/workflows/build.yml` pour changer :
- Les branches qui déclenchent le build
- Les tags qui créent des releases
- Les versions de Python/Node.js

### Ajouter des étapes

Vous pouvez ajouter des étapes supplémentaires :
- Tests automatiques
- Signature de code
- Upload vers d'autres services
- Notifications

## 💡 Astuces

### Créer une release avec description

```bash
# Créer un tag annoté
git tag -a v1.0.0 -m "Version 1.0.0 - Première release stable"
git push origin v1.0.0
```

### Versioning automatique

Vous pouvez utiliser des variables d'environnement pour gérer les versions :

```yaml
- name: Set version
  run: echo "VERSION=1.0.0" >> $GITHUB_ENV
```

### Notifications

Ajoutez des notifications Slack, Discord, ou email dans le workflow.

## ⚠️ Limitations

- **Temps d'exécution** : Les builds peuvent prendre 10-20 minutes
- **Quota gratuit** : 2000 minutes/mois (suffisant pour ~100 builds/mois)
- **Taille des artefacts** : Maximum 10 GB par artefact
- **Rétention** : 30 jours pour les releases, 7 jours pour les builds de développement

## 🐛 Dépannage

### Le workflow ne se déclenche pas

1. Vérifiez que les fichiers sont dans `.github/workflows/`
2. Vérifiez la syntaxe YAML (utilisez un validateur en ligne)
3. Vérifiez que vous avez poussé sur la bonne branche

### Les artefacts ne sont pas créés

1. Vérifiez les logs pour voir si le build a réussi
2. Vérifiez que les chemins dans `upload-artifact` sont corrects
3. Vérifiez que les fichiers existent après le build

### Le frontend ne compile pas

1. Vérifiez que `package.json` est présent
2. Vérifiez que toutes les dépendances sont installées
3. Consultez les logs npm pour plus de détails

## 📚 Ressources

- [Documentation GitHub Actions](https://docs.github.com/en/actions)
- [Marketplace GitHub Actions](https://github.com/marketplace?type=actions)
- [Exemples de workflows](https://github.com/actions/starter-workflows)

---

**Bon build automatique ! 🚀**

