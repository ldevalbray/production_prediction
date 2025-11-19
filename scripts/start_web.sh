#!/bin/bash

# Script de démarrage pour l'interface web
# Démarre le backend Flask et le frontend React

echo "🌾 Démarrage de l'interface web Pépinière Valbray..."

# Vérifier si les dépendances Python sont installées
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Installation des dépendances Python..."
    pip install -r requirements.txt
fi

# Vérifier si node_modules existe
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Installation des dépendances Node.js..."
    cd frontend
    npm install
    cd ..
fi

# Démarrer le backend Flask en arrière-plan
echo "🚀 Démarrage du backend Flask..."
python app.py &
BACKEND_PID=$!

# Attendre un peu pour que le backend démarre
sleep 2

# Démarrer le frontend React
echo "🚀 Démarrage du frontend React..."
cd frontend
npm start

# Nettoyer les processus à la sortie
trap "kill $BACKEND_PID 2>/dev/null" EXIT

