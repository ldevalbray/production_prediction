# Guide d'Installation - Première Utilisation

Ce guide explique comment installer et utiliser l'application Pépinière Valbray pour la première fois.

## 📥 Téléchargement

### Option 1 : Depuis GitHub Releases (Recommandé)

1. Allez sur la page GitHub du projet : https://github.com/ldevalbray/production_prediction/releases
2. Téléchargez le fichier correspondant à votre système :
   - **Windows** : `PepiniereValbray-Windows.zip`
   - **macOS** : `PepiniereValbray-macOS.dmg` ou `PepiniereValbray.app`

### Option 2 : Depuis un lien de partage

Si vous avez reçu un lien de partage (WeTransfer, Google Drive, etc.) :
1. Cliquez sur le lien
2. Téléchargez le fichier ZIP ou DMG correspondant à votre système

## 🪟 Installation sur Windows

### Méthode 1 : Installation simple (Recommandée)

1. **Téléchargez** `PepiniereValbray-Windows.zip`
2. **Extrayez** le fichier ZIP dans un dossier de votre choix (ex: `C:\Program Files\PepiniereValbray\` ou `C:\Users\VotreNom\PepiniereValbray\`)
3. **Ouvrez** le dossier extrait
4. **Double-cliquez** sur `PepiniereValbray.exe`
5. L'application démarre automatiquement et ouvre votre navigateur sur `http://127.0.0.1:5000`

### Méthode 2 : Créer un raccourci

1. Suivez les étapes 1-3 de la Méthode 1
2. **Clic droit** sur `PepiniereValbray.exe`
3. Sélectionnez **"Créer un raccourci"**
4. Déplacez le raccourci sur votre Bureau ou dans le menu Démarrer

### ⚠️ Avertissement Windows Defender

Si Windows Defender bloque l'application :
1. Cliquez sur **"Plus d'infos"**
2. Cliquez sur **"Exécuter quand même"**
3. L'application n'est pas signée numériquement, c'est normal pour une application interne

## 🍎 Installation sur macOS

### Méthode 1 : Depuis un DMG

1. **Téléchargez** `PepiniereValbray-macOS.dmg`
2. **Double-cliquez** sur le fichier DMG
3. **Glissez** `PepiniereValbray.app` vers le dossier Applications
4. **Ouvrez** le dossier Applications
5. **Double-cliquez** sur `PepiniereValbray.app`
6. Si macOS bloque l'application :
   - **Clic droit** sur l'application
   - Sélectionnez **"Ouvrir"**
   - Cliquez sur **"Ouvrir"** dans la fenêtre de confirmation

### Méthode 2 : Depuis un ZIP

1. **Téléchargez** le fichier ZIP contenant `PepiniereValbray.app`
2. **Extrayez** le fichier ZIP
3. **Glissez** `PepiniereValbray.app` vers le dossier Applications
4. **Double-cliquez** sur l'application dans le dossier Applications

### ⚠️ Avertissement macOS Gatekeeper

Si macOS affiche "PepiniereValbray ne peut pas être ouvert car il provient d'un développeur non identifié" :

1. Allez dans **Préférences Système** → **Sécurité et confidentialité**
2. Cliquez sur **"Ouvrir quand même"** à côté du message d'avertissement
3. Ou utilisez le **clic droit** → **Ouvrir** (voir Méthode 1)

## 🚀 Premier Lancement

### 1. Démarrer l'application

- **Windows** : Double-cliquez sur `PepiniereValbray.exe`
- **macOS** : Double-cliquez sur `PepiniereValbray.app`

### 2. Attendre le démarrage

- Un écran de chargement peut apparaître
- L'application démarre un serveur web local
- Votre navigateur s'ouvre automatiquement sur `http://127.0.0.1:5000`

### 3. Interface web

Vous verrez l'interface web de l'application avec :
- **Accueil** : Vue d'ensemble des récoltes et prévisions
- **Récoltes** : Historique et ajout de nouvelles récoltes
- **Prévisions** : Prévisions générées par l'IA
- **Paramètres** : Configuration des parcelles et variétés

## 📋 Configuration Initiale

### Étape 1 : Préparer vos données

L'application nécessite un fichier Excel avec vos données. Deux options :

#### Option A : Utiliser un fichier Excel existant

1. Placez votre fichier `recoltes_fraises.xlsx` dans le dossier de l'application
2. L'application le détectera automatiquement

#### Option B : Créer un nouveau fichier

1. L'application créera automatiquement une base de données SQLite (`recoltes.db`)
2. Utilisez l'interface web pour ajouter vos données

### Étape 2 : Configurer les paramètres

1. Allez dans **Paramètres** dans l'interface web
2. Ajoutez vos **parcelles** et **variétés**
3. Configurez le nombre de **rangées** par parcelle/variété

### Étape 3 : Ajouter vos données historiques

1. Allez dans **Récoltes**
2. Ajoutez vos récoltes passées (au moins quelques semaines pour de bonnes prédictions)
3. Ou importez depuis Excel si vous avez un fichier existant

### Étape 4 : Générer le premier modèle

1. Cliquez sur **"Mettre à jour le modèle"** dans l'interface
2. Attendez que le modèle soit entraîné (quelques minutes)
3. Le modèle sera sauvegardé automatiquement

## 📁 Structure des Fichiers

Après la première utilisation, votre dossier d'application contiendra :

```
PepiniereValbray/
├── PepiniereValbray.exe (ou .app sur macOS)
├── _internal/              # Code de l'application (ne pas modifier)
├── recoltes.db             # Base de données SQLite (vos données)
├── recoltes_fraises.xlsx   # Fichier Excel (si utilisé)
├── meteo_dataset.csv       # Données météo
├── model_fraises_v2.pkl    # Modèle IA (généré automatiquement)
├── forecasts/              # Prévisions générées
├── models/                 # Modèles et archives
└── data/                   # Données utilisateur
```

**⚠️ IMPORTANT** : Ne supprimez jamais ces fichiers, ils contiennent vos données !

## 🔄 Mise à Jour Automatique

L'application vérifie automatiquement les nouvelles versions :

1. Au démarrage, l'application vérifie s'il y a une mise à jour
2. Si une nouvelle version est disponible, une notification apparaît
3. Cliquez sur **"Mettre à jour maintenant"** pour installer
4. **Vos données sont automatiquement préservées** lors de la mise à jour

## ❓ Problèmes Courants

### L'application ne démarre pas

**Windows :**
- Vérifiez que Windows Defender n'a pas bloqué l'application
- Vérifiez les permissions d'exécution
- Essayez de lancer en tant qu'administrateur

**macOS :**
- Vérifiez que vous avez bien fait "Clic droit → Ouvrir" la première fois
- Vérifiez les permissions dans Préférences Système → Sécurité

### Le navigateur ne s'ouvre pas automatiquement

1. Ouvrez manuellement votre navigateur
2. Allez sur : `http://127.0.0.1:5000`
3. L'interface devrait s'afficher

### Erreur "Port 5000 déjà utilisé"

Une autre instance de l'application est peut-être déjà lancée :
1. Fermez toutes les instances de l'application
2. Redémarrez l'application

### L'application se ferme immédiatement

1. Vérifiez les logs dans `app.log` (dans le dossier de l'application)
2. Vérifiez que tous les fichiers sont présents dans le dossier
3. Réinstallez l'application depuis la release GitHub

### Pas de données affichées

1. Vérifiez que vous avez ajouté des données dans l'interface
2. Vérifiez que le fichier `recoltes.db` existe dans le dossier
3. Allez dans **Paramètres** pour configurer vos parcelles et variétés

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs dans `app.log`
2. Consultez la documentation : `docs/README_UTILISATEUR.md`
3. Contactez le support technique

## ✅ Checklist de Première Installation

- [ ] Application téléchargée et extraite
- [ ] Application lancée avec succès
- [ ] Interface web accessible dans le navigateur
- [ ] Parcelles et variétés configurées
- [ ] Données historiques ajoutées (au moins quelques semaines)
- [ ] Premier modèle généré avec succès
- [ ] Première prévision générée avec succès

## 🎯 Prochaines Étapes

Une fois l'installation terminée :

1. **Ajoutez régulièrement vos récoltes** pour améliorer les prédictions
2. **Générez les prévisions** chaque matin pour planifier votre journée
3. **Mettez à jour le modèle** régulièrement (toutes les semaines ou après beaucoup de nouvelles données)

---

**Note** : L'application fonctionne entièrement hors ligne après l'installation. Seule la vérification des mises à jour nécessite une connexion Internet.

