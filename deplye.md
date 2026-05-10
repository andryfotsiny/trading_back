#!/bin/bash

# ============================================
# DEPLOY SCRIPT - Trading Bot
# Usage:
#   ./deploy.sh           → auto-détecte les changements
#   ./deploy.sh backend   → force rebuild backend
#   ./deploy.sh frontend  → force rebuild frontend
#   ./deploy.sh all       → rebuild les 2
# ============================================

SERVER="michel@158.220.99.35"
DEPLOY_PATH="/srv/trad"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   DEPLOY - Trading Bot               ${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# ---- Détection automatique des changements ----
FORCE=$1  # backend | frontend | all | vide = auto

if [ -z "$FORCE" ]; then
    echo -e "${YELLOW}🔍 Détection des changements...${NC}"

    CHANGED_BACK=$(git diff --name-only origin/main..HEAD -- . 2>/dev/null | grep -v "^trading_front/" | wc -l)
    CHANGED_FRONT=$(git diff --name-only origin/main..HEAD -- . 2>/dev/null | grep "^trading_front/" | wc -l)

    # Si pas de diff détecté, on regarde le dernier commit
    if [ "$CHANGED_BACK" -eq 0 ] && [ "$CHANGED_FRONT" -eq 0 ]; then
        LAST_CHANGED=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
        CHANGED_BACK=$(echo "$LAST_CHANGED" | grep -v "trading_front/" | wc -l)
        CHANGED_FRONT=$(echo "$LAST_CHANGED" | grep "trading_front/" | wc -l)
    fi

    DEPLOY_BACK=false
    DEPLOY_FRONT=false

    if [ "$CHANGED_BACK" -gt 0 ]; then
        DEPLOY_BACK=true
        echo -e "  ${GREEN}✔ Backend modifié${NC} → rebuild backend"
    fi
    if [ "$CHANGED_FRONT" -gt 0 ]; then
        DEPLOY_FRONT=true
        echo -e "  ${GREEN}✔ Frontend modifié${NC} → rebuild frontend"
    fi

    # Si rien détecté
    if [ "$DEPLOY_BACK" = false ] && [ "$DEPLOY_FRONT" = false ]; then
        echo -e "  ${YELLOW}⚠ Aucun changement détecté${NC}"
        echo ""
        echo "  Que voulez-vous déployer ?"
        echo "  1) Backend"
        echo "  2) Frontend"
        echo "  3) Les deux"
        echo "  4) Annuler"
        echo ""
        read -p "  Votre choix [1-4]: " choice
        case $choice in
            1) DEPLOY_BACK=true ;;
            2) DEPLOY_FRONT=true ;;
            3) DEPLOY_BACK=true; DEPLOY_FRONT=true ;;
            *) echo -e "${RED}Annulé.${NC}"; exit 0 ;;
        esac
    fi

else
    # Mode forcé
    case $FORCE in
        backend)  DEPLOY_BACK=true;  DEPLOY_FRONT=false ;;
        frontend) DEPLOY_BACK=false; DEPLOY_FRONT=true  ;;
        all)      DEPLOY_BACK=true;  DEPLOY_FRONT=true  ;;
        *)
            echo -e "${RED}Usage: ./deploy.sh [backend|frontend|all]${NC}"
            exit 1
            ;;
    esac
fi

echo ""
echo -e "${BLUE}🚀 Déploiement en cours...${NC}"
echo ""

# ---- Connexion SSH et déploiement ----
ssh -i ~/.ssh/id_ed25519 $SERVER bash <<EOF

set -e
cd $DEPLOY_PATH

echo ""
echo "📦 Git pull backend..."
cd trading_back && git pull && cd ..

echo "📦 Git pull frontend..."
cd trading_front && git pull && cd ..

$(if [ "$DEPLOY_BACK" = true ]; then
echo '
echo ""
echo "🔨 Rebuild backend..."
docker compose up --build -d backend
echo "✅ Backend redémarré"
'
fi)

$(if [ "$DEPLOY_FRONT" = true ]; then
echo '
echo ""
echo "🔨 Rebuild frontend..."
docker compose up --build -d frontend
echo "✅ Frontend redémarré"
'
fi)

echo ""
echo "🔄 Reload nginx..."
docker compose exec nginx nginx -s reload

echo ""
echo "✅ Deploy terminé !"
docker compose ps

EOF

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   ✅ Deploy terminé avec succès !    ${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""