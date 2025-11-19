#!/bin/bash
# Script pour vérifier et configurer automatiquement xcode-select après installation

echo "🔍 Vérification de l'installation des outils de développement..."
echo ""

# Vérifier si xcode-select est configuré
if xcode-select -p &>/dev/null; then
    echo "✅ xcode-select est déjà configuré : $(xcode-select -p)"
    echo ""
    echo "🎉 Vous pouvez maintenant builder l'application !"
    echo "   Lancez : python3 build_executable.py"
    exit 0
fi

echo "⏳ Les outils de développement ne sont pas encore configurés."
echo ""
echo "Vérification des emplacements possibles..."

# Vérifier si CommandLineTools existe
if [ -d "/Library/Developer/CommandLineTools" ]; then
    echo "✅ CommandLineTools trouvé dans /Library/Developer/CommandLineTools"
    echo ""
    echo "Configuration de xcode-select..."
    if sudo xcode-select --switch /Library/Developer/CommandLineTools 2>/dev/null; then
        echo "✅ xcode-select configuré avec succès !"
        echo ""
        echo "🎉 Vous pouvez maintenant builder l'application !"
        echo "   Lancez : python3 build_executable.py"
        exit 0
    else
        echo "❌ Erreur lors de la configuration. Vous devrez peut-être entrer votre mot de passe."
    fi
fi

# Vérifier si Xcode complet existe
if [ -d "/Applications/Xcode.app/Contents/Developer" ]; then
    echo "✅ Xcode complet trouvé dans /Applications/Xcode.app"
    echo ""
    echo "Configuration de xcode-select..."
    if sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer 2>/dev/null; then
        echo "✅ xcode-select configuré avec succès !"
        echo ""
        echo "🎉 Vous pouvez maintenant builder l'application !"
        echo "   Lancez : python3 build_executable.py"
        exit 0
    else
        echo "❌ Erreur lors de la configuration. Vous devrez peut-être entrer votre mot de passe."
    fi
fi

echo ""
echo "⚠️  Les outils de développement ne sont pas encore installés ou configurés."
echo ""
echo "📋 Instructions :"
echo "   1. Attendez que la fenêtre d'installation se termine"
echo "   2. Une fois terminé, exécutez manuellement :"
echo ""
echo "      sudo xcode-select --switch /Library/Developer/CommandLineTools"
echo ""
echo "   3. Puis relancez ce script ou directement :"
echo ""
echo "      python3 build_executable.py"

