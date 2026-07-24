# Résumé Complet — Projet Trading Bot
> Dernière mise à jour : Juillet 2026

---

## 1. Vue d'ensemble

Bot de **paper trading** automatique sur BTC/USDT, développé par Bonjour (username: andry, serveur: michel).  
Objectif : valider des stratégies en simulation avant de passer au trading réel.

### Stack technique
| Composant | Technologie |
|---|---|
| Backend | FastAPI + APScheduler (cycle 5 min) |
| Frontend | React (TypeScript) + TanStack React Query |
| Base de données | PostgreSQL 16 |
| Cache | Redis 7 |
| Proxy | Nginx |
| Déploiement | Docker Compose sur VPS |
| Migrations BDD | Alembic |

### Infrastructure
- **VPS** : 158.220.99.35 (Ubuntu 24, 4 vCPU, 8 GB RAM)
- **Projet serveur** : `/srv/trad/`
- **Projet local** : `~/Projects/trading_bot/`
- **Deploy script** : `~/Projects/trading_bot/deploy.sh [backend|frontend|all]`
- **GitHub** :
  - Backend : `andryfotsiny/trading_back`
  - Frontend : `andryfotsiny/trading_front`

### Containers Docker
```
trad-backend-1   → port 8000
trad-frontend-1  → port 3000
trad-nginx-1     → port 8080 (HTTP) / 8443 (HTTPS)
trad-db-1        → PostgreSQL
trad-redis-1     → Redis
```

---

## 2. Architecture Backend

### Structure des fichiers clés
```
trading_back/
├── app/
│   ├── services/
│   │   ├── bot_runner.py          ← Scheduler principal (APScheduler)
│   │   ├── execution/
│   │   │   ├── paper_executor.py  ← Ouvre/ferme les trades paper
│   │   │   └── order_manager.py   ← Historique trades
│   │   ├── risk/
│   │   │   ├── risk_manager.py    ← Gestion du risque
│   │   │   └── stop_loss.py       ← Calcul SL/TP
│   │   ├── strategies/
│   │   │   ├── signal_engine.py   ← Dispatch des stratégies
│   │   │   └── builtin/           ← Implémentations stratégies
│   │   └── exchange/
│   │       └── binance_client.py  ← API Binance (prix, candles)
│   ├── db/
│   │   └── models/
│   │       └── trade.py           ← Modèle Trade (avec strategy_type)
│   └── api/routes/
│       └── backtest/optimizer.py  ← Optimiseur de stratégies
├── alembic/versions/              ← Migrations BDD
└── main.py
```

### Flux du bot (bot_cycle — toutes les 5 min)
```
1. check_market_conditions()     → Vérif calendrier économique + Fear&Greed
2. Pour chaque stratégie active:
   a. Vérif si trade déjà ouvert (limite 1 trade / stratégie)
   b. get_ohlcv() → candles Binance
   c. run_strategy() → signal BUY/SELL ou None
   d. calculate_ma50() → filtre tendance
   e. is_trend_favorable() → BUY seulement si prix > MA50
   f. PaperExecutor.open_trade() → ouvre le trade
3. Pour chaque trade ouvert:
   a. check_trade_exit() → vérifie SL/TP
   b. Si atteint → close_trade()
```

---

## 3. Stratégies disponibles

### Types de stratégies
```
rsi_oversold       → Signal sur RSI survendu
macd_crossover     → Croisement MACD
sma_crossover      → Croisement moyennes mobiles
bollinger_bounce   → Rebond sur bandes de Bollinger
grid_trading       → Grille de niveaux de prix
dca_bot            → Dollar Cost Averaging
rsi_macd_combo     → Combinaison RSI + MACD
mtf_confluence     → Multi-timeframe confluence
bos_structure      → Break of Structure
liquidity_sweep    → Sweep de liquidité
```

### Stratégies actives (configuration actuelle — juillet 2026)
| ID | Nom | Type | TF | SL | TP |
|---|---|---|---|---|---|
| 13 | dca_4h | dca_bot | 4h | 1% | 8% |
| 14 | grid_4h | grid_trading | 4h | 2% | 6% |
| 15 | rsi_4h | rsi_oversold | 4h | 1% | 8% |
| 16 | macd_4h | macd_crossover | 4h | 1% | 3% |
| 17 | sma_4h | sma_crossover | 4h | 1.5% | 5% |
| 18 | boll_1h | bollinger_bounce | 1h | 2% | 6% |
| 19 | rsimacd_1h | rsi_macd_combo | 1h | 1% | 8% |
| 20 | mtf_4h | mtf_confluence | 4h | 1% | 8% |

---

## 4. Base de données

### Tables principales
```sql
users           → Comptes utilisateurs (login/auth JWT)
strategies      → Config des stratégies (SL%, TP%, timeframe...)
trades          → Historique trades (ouvert/fermé)
orders          → Ordres associés aux trades
signals         → Signaux générés
candles         → Cache des bougies OHLCV
backtest_results → Résultats backtest
optimizer_results → Résultats optimiseur
portfolios      → Soldes portfolio
```

### Migrations Alembic appliquées
```
255f9d7ae174 → init_models (tables initiales)
c5d60c075fda → add_optimizer_results_table
282921ef1d25 → add_strategy_type_to_trades  ← DERNIÈRE
```

### Commandes BDD utiles
```bash
# Appliquer migrations
docker exec trad-backend-1 alembic upgrade head

# Reset complet (garde users + strategies)
docker exec trad-db-1 psql -U postgres -d trading_bot -c \
  "TRUNCATE TABLE orders, trades, signals, backtest_results, optimizer_results, portfolios, candles RESTART IDENTITY CASCADE;"

# Voir les trades
docker exec trad-db-1 psql -U postgres -d trading_bot -c \
  "SELECT id, strategy_name, status, pnl FROM trades ORDER BY opened_at DESC LIMIT 10;"
```

---

## 5. Historique des bugs corrigés

### Bug #1 — Bot bloqué par drawdown (mai 2026)
**Symptôme** : Bot génère des signaux mais n'ouvre aucun trade.  
**Cause** : `RiskManager.can_open_trade()` bloquait si PnL < -10% du capital.  
**Fix** : `can_open_trade()` retourne toujours `{"allowed": True}` pour paper trading.  
**Fichier** : `app/services/risk/risk_manager.py`

### Bug #2 — Accumulation infinie de trades (mai 2026)
**Symptôme** : 200+ trades identiques ouverts simultanément → -5400 USDT.  
**Cause** : Pas de limite "1 trade par stratégie".  
**Fix** : Vérification `existing > 0 → continue` avant d'ouvrir.  
**Fichier** : `app/services/bot_runner.py`

### Bug #3 — check_open_trades manquant (mai 2026)
**Symptôme** : Erreur 500 sur `/api/trading/check-exits`.  
**Cause** : Refonte de `paper_executor.py` avait supprimé la méthode `check_open_trades()`.  
**Fix** : Méthode restaurée avec création des `Order` à l'ouverture/fermeture.  
**Fichier** : `app/services/execution/paper_executor.py`

### Bug #4 — KeyError: 4 dans calculate_ma50 (juin–juillet 2026)
**Symptôme** : Aucun trade depuis le 10 juin. Logs : `Erreur strategie grid_4h: 4`.  
**Cause** : `calculate_ma50()` faisait `c[4]` mais les candles sont des **dicts** avec clé `"close"`.  
**Fix** : `c[4]` → `c["close"]` + `logger.exception()` pour avoir la stack trace.  
**Diagnostiqué par** : Claude Code Desktop via `dyleth-start`.  
**Fichier** : `app/services/bot_runner.py`

---

## 6. Résultats des tests paper trading

### Résumé global (mai–juin 2026)
| Période | Trades | TP | SL | Win Rate | PnL |
|---|---|---|---|---|---|
| Avant fix accumulation | 330 | 7 | 323 | 2.1% | -5399 USDT |
| Après fix accumulation | 21 | 1 | 20 | ~5% | -280 USDT |
| Avec filtre MA50 | 0 (bug KeyError) | — | — | — | — |

### Observations clés
- **Marché baissier** : BTC 82000 → 61000 (-25%) sur la période de test
- **Stratégies BUY only** → perdent systématiquement en downtrend
- **Seul TP** : trade #21 `grid_4h` SELL @ 64174 → +8.57 USDT
- **Problème racine** : pas de filtre de tendance → achat en pleine chute

### Résultats optimiseur (mai 2026)
Meilleure combinaison historique :
```
Stratégie : dca_bot
Timeframe : 4h
SL : 1% / TP : 8%
PnL backtest : +2543 USDT
Win rate : 28%
Profit Factor : 3.3
Sharpe : 5.75
```

---

## 7. Fonctionnalités implémentées

### Backend
- [x] APScheduler bot cycle (5 min)
- [x] Stratégies multiples en parallèle
- [x] Paper trading (PaperExecutor)
- [x] Stop Loss / Take Profit automatique
- [x] Trailing Stop Loss
- [x] Partial Take Profit
- [x] Risk Manager (désactivé pour paper testing)
- [x] Limite 1 trade ouvert par stratégie
- [x] Filtre MA50 (anti-downtrend) ← NOUVEAU
- [x] Optimiseur de stratégies (backtest multi-combinaisons)
- [x] Calendrier économique (Finnhub)
- [x] Fear & Greed Index
- [x] Notifications Telegram (optionnel)
- [x] Migration `strategy_type` dans `trades`
- [x] Module IA (Claude/OpenAI/Ollama) — non connecté au bot

### Frontend
- [x] Dashboard (PnL, win rate, prix BTC, RSI)
- [x] Trades ouverts en temps réel
- [x] Historique des trades avec type stratégie
- [x] Gestion des stratégies (create/delete/activate) avec SL% et TP%
- [x] Backtest
- [x] Optimiseur
- [x] Calendrier économique
- [x] React Query (auto-refresh)
- [x] Design zinc/cyan responsive
- [x] Page 404 + session expirée

---

## 8. État actuel (juillet 2026)

### Ce qui fonctionne
- Bot tourne 24/7 ✅
- 8 stratégies actives ✅
- Filtre MA50 déployé ✅
- Fix KeyError appliqué par Claude Code ✅ (à confirmer déployé)

### Ce qui reste à faire
- [ ] Confirmer déploiement fix KeyError (Claude Code a commit, vérifier push+deploy)
- [ ] Tester 48h avec le filtre MA50 corrigé
- [ ] Analyser résultats par stratégie → supprimer les mauvaises
- [ ] Implémenter auto-optimiseur hebdomadaire
- [ ] Connecter module IA aux décisions de trading
- [ ] Envisager passage au trading réel si win rate > 30% sur 48h

---

## 9. Commandes utiles

### Déploiement
```bash
# Deploy backend seul
cd ~/Projects/trading_bot && ./deploy.sh backend

# Deploy tout
./deploy.sh all

# Migration BDD après deploy
ssh michel@158.220.99.35 "cd /srv/trad && docker exec trad-backend-1 alembic upgrade head"
```

### Monitoring
```bash
# Logs en temps réel (sur serveur)
cd /srv/trad && docker compose logs -f backend

# Filtrer signaux et trades
docker compose logs backend --since=1h 2>&1 | grep -E "Signal|MA50|Trade ouvert|Filtre|Erreur"

# Vérifier trades ouverts
curl -s http://158.220.99.35:8080/api/trading/open-trades \
  -H "Authorization: Bearer TOKEN" | python3 -c "import sys,json; print('Trades:', len(json.load(sys.stdin)))"
```

### Gestion stratégies (API)
```bash
TOKEN="VOTRE_TOKEN_JWT"
BASE="http://158.220.99.35:8080"

# Lister stratégies
curl -s $BASE/api/strategies/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Activer stratégie
curl -s -X POST $BASE/api/strategies/ID/activate -H "Authorization: Bearer $TOKEN"

# Créer stratégie
curl -s -X POST $BASE/api/strategies/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"nom","strategy_type":"dca_bot","symbol":"BTC/USDT","timeframe":"4h","risk_per_trade":0.02,"stop_loss_pct":0.01,"take_profit_pct":0.08}'
```

---

## 10. Leçons apprises

1. **Sans limite de trades** → accumulation catastrophique (-5400 USDT sur 330 trades)
2. **Drawdown threshold en paper trading** → bloque le bot, désactiver pour les tests
3. **Stratégies BUY only en downtrend** → perte garantie, filtre MA50 essentiel
4. **Backtests sur données passées ≠ performance future** → overfitting possible
5. **10 trades de backtest insuffisants** pour valider une stratégie (mtf_confluence)
6. **Logs sans stack trace** → bugs silencieux pendant 1 mois (bug KeyError: 4)
7. **`logger.exception()` plutôt que `logger.error(str(e))`** → toujours avoir la trace complète
8. **Candles Binance = dicts** (`{"close": ...}`) pas des listes (`c[4]` = bug)
9. **Un seul vrai trade gagnant** était un SELL → les stratégies doivent trader les 2 sens
10. **Claude Code Desktop** très utile pour diagnostic serveur via SSH + dyleth tunnel
