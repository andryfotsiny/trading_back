# Diagnostic & Plan de correction — Bot de paper trading

> Date : 2026-07-23
> Périmètre : 25 trades fermés, 1 seul gagnant (win rate ~4%)
> Méthode : vérification dans les données réelles (SQL), le code et l'ATR mesuré. Aucune supposition.

---

## 0. Preuve centrale

Sur les 25 trades fermés, **`exit_price` == `stop_loss` pour les 25 lignes, sans exception**.

- **0 trade sur 25** n'a jamais atteint son `take_profit`.
- 100% des sorties se font sur le stop (trailé).
- Le seul « gagnant » (#21, grid **SELL**, +0.86%) est aussi sorti sur son stop, mais dans le bon sens car c'était un short en marché baissier.

Conclusion : le problème n'est pas le choix de direction des stratégies, c'est que le mécanisme de sortie rend le TP mathématiquement inatteignable.

---

## 1. Verdict par hypothèse

| # | Hypothèse | Verdict | Preuve chiffrée |
|---|---|---|---|
| H2 | Trailing stop trop agressif | CONFIRMÉE — cause n°1 | 25/25 sorties = stop trailé ; fermetures à -0.26 / -0.35 / -0.78% |
| H8 | BUY-only en downtrend | CONFIRMÉE — amplificateur | 23 BUY / 2 SELL ; l'unique gain = le seul SELL |
| H3 | Repainting (bougie non clôturée) | CONFIRMÉE | Toutes les stratégies lisent `closes[-1]` (bougie en cours) |
| H1 | SL trop serré vs ATR | PARTIELLE | dca/rsi/macd/mtf SL 1% = 1.18x ATR(4h) — serré mais pas la cause principale |
| H6 | Frais absents | CONFIRMÉE (mineur) | `fee_total = 0` et `orders.fee = 0` partout → résultats optimistes |
| H7 | Partial TP corrompt le PnL | LATENTE | Bug réel mais jamais déclenché (aucun partial n'a eu lieu) |
| H4 | Priorité SL avant TP | INFIRMÉE | SL et TP de part et d'autre du prix → ne peuvent trigger ensemble sur un tick |
| H5 | Comparaisons inversées | INFIRMÉE | rsi<30 crossup, macd cross-up, sma golden cross, boll bande basse : tous corrects |

---

## 2. Mécanisme exact de la cause n°1

Dans `app/services/bot_runner.py`, chaque cycle appelle :
```python
calculate_trailing_stop(trade.side, trade.entry_price, price, trade.stop_loss)
```
Le 5e argument `trailing_pct` n'est pas passé → il vaut le défaut **0.02 (2%)** pour toutes les stratégies, quel que soit leur SL configuré.

Logique dans `app/services/risk/trailing_stop.py:11-14` (BUY) :
```
new_sl = price * 0.98        # 2% sous le prix courant
update si new_sl > SL_actuel ET price > entry
```

Enchaînement pour un dca (SL initial = entry x 0.99) :
1. Le trailing commence dès que `price*0.98 > entry*0.99` → dès **+1.02%** au-dessus de l'entrée.
2. Le SL se colle alors à **2% sous le plus-haut atteint**.
3. Le trade est stoppé dès un recul de 2% depuis le pic local.
4. Pour toucher le TP (+6 à +8%), il faudrait grimper de 6-8% sans jamais retracer de 2% → impossible en marché réel.

Vérification sur trades réels :
- #16 et #17 : sortie identique 66541.461 = `67899 * 0.98`. Prix +1.68%, SL remonté à 66541, puis retour → -0.35%.
- #1 et #2 : sortie identique 72839.078 = `74326 * 0.98`, même timestamp de clôture. Pic +1.6% commun puis chute → -0.45% / -0.26%.

→ Le trailing transforme systématiquement un petit gain latent en petite perte réalisée et plafonne tout trade avant le TP. C'est ce qui produit le win rate de 4%.

---

## 3. ATR réel mesuré (via le container, BTC/USDT)

| Timeframe | ATR(14) | En % du prix |
|---|---|---|
| 4h | 551.5 | 0.85% |
| 1h | 278.3 | 0.43% |

Ratio SL configuré / ATR et TP / ATR :

| Stratégie | TF | SL | SL/ATR | TP | TP/ATR | Lecture |
|---|---|---|---|---|---|---|
| dca_4h | 4h | 1% | 1.18x | 8% | 9.4x | TP inatteignable |
| grid_4h | 4h | 2% | 2.35x | 6% | 7.1x | déséquilibré |
| rsi_4h | 4h | 1% | 1.18x | 8% | 9.4x | TP inatteignable |
| macd_4h | 4h | 1% | 1.18x | 3% | 3.5x | le moins pire |
| sma_4h | 4h | 1.5% | 1.76x | 5% | 5.9x | déséquilibré |
| boll_1h | 1h | 2% | 4.65x | 6% | 14x | TP irréaliste |
| rsimacd_1h | 1h | 1% | 2.33x | 8% | 18.6x | TP irréaliste |
| mtf_4h | 4h | 1% | 1.18x | 8% | 9.4x | TP inatteignable |

Problème structurel : asymétrie reward/risk. Le TP est à 7-19x ATR alors que le trailing coupe tout gain au moindre recul de 2%. La cible de gain est hors d'atteinte pendant que le stop est atteignable.

---

## 4. Performance par stratégie

| Stratégie | Trades | Gains | Pertes | PnL total | Décision |
|---|---|---|---|---|---|
| dca_4h | 13 | 0 | 13 | -225.64 | BUY-only : désactiver ou ajouter filtre tendance |
| grid_4h | 10 | 1 | 9 | -101.48 | Garder (capable de SELL) mais revoir trailing |
| rsimacd_1h | 1 | 0 | 1 | -20.00 | Trop peu de données |
| boll_1h | 1 | 0 | 1 | -14.85 | Trop peu de données |
| rsi_4h / macd_4h / sma_4h / mtf_4h | ~0 | — | — | — | Signaux rares, à observer |

---

## 5. Conclusion honnête

Le win rate de 4% n'est pas dû à des stratégies simplement mauvaises ni uniquement au marché baissier. C'est un défaut d'implémentation dominant : le trailing stop à 2% (activé dès +1%) combiné à un TP placé à 7-19x ATR rend tout gain impossible à matérialiser (0/25 trades ont touché leur TP). Le marché baissier + le long-only (H8) et le repainting (H3) aggravent, mais la racine est le mécanisme de sortie.

---

## 6. Plan de correction (ordonné par priorité)

### Fix #1 — Débloquer le reward/risk (PRIORITÉ ABSOLUE) — FAIT (commit 6ace553)
Fichiers : `app/services/bot_runner.py`, `app/services/risk/trailing_stop.py`
- Seuil d'activation ajouté : le trailing ne s'enclenche qu'après un gain >= 1R au lieu de dès +1%.
- Plancher break-even : `max(price*(1-trailing_pct), entry_price)` — le SL ne peut plus passer du mauvais côté de l'entrée.
- `trailing_pct` et `trailing_activation_pct` lus depuis `strategy.parameters` au lieu du défaut caché de 2%.
- Vérifié sur trades réels : #1 passe de -0.45% à 0.00% breakeven ; #17 ne sort plus prématurément à -0.35%.

### Fix #2 — Supprimer le repainting — FAIT (commit 9a58781)
Fichier : `app/services/bot_runner.py`
- Les stratégies reçoivent `candles[:-1]`, la bougie en cours de formation est exclue à la source (une seule modification au lieu de patcher les 10 stratégies).
- Le prix d'entrée provient désormais du ticker live, plus du close d'une bougie non terminée.
- Écart mesuré entre bougie formante et dernière clôturée : 1.4% (bruit supprimé).

### Fix #3 — SL/TP basés sur l'ATR — FAIT (commit 9a58781)
Fichiers : `app/services/strategies/indicators/atr.py` (nouveau), `app/services/bot_runner.py`
- Indicateur ATR créé (absent du projet).
- `resolve_risk_levels()` : SL = 2x ATR, TP = 3x ATR → R:R = 1.50, bornés entre 0.5%-5% (SL) et 0.75%-10% (TP).
- Repli sur la config de la stratégie si l'ATR est indisponible ; désactivable via `use_atr_risk: false`.
- Mesuré : 4h SL 1.71% / TP 2.57% ; 1h SL 1.05% / TP 1.58% (contre TP à 9.4x ATR avant, inatteignable).

### Fix #4 — Comptabiliser les frais — FAIT (commit 5bc1ede)
Fichier : `app/services/execution/paper_executor.py`
- `FEE_RATE = 0.001` prélevé à l'ouverture et à la fermeture, enregistré sur `trades.fee_total` et `orders.fee`, déduit du PnL net.
- Les 25 trades précédents avaient `fee_total = 0`, donc des résultats optimistes.

### Fix #5 — PnL des partial TP écrasé — FAIT (commit 5bc1ede)
Fichier : `app/services/execution/paper_executor.py`
- `close_trade()` faisait `trade.pnl = pnl`, écrasant le PnL déjà banké. Désormais cumulé (`banked + gross - fee_total`).
- Garde-fou ajouté sur la division par zéro du `pnl_pct`.

### Fix #6 — Shorts : AUCUN CHANGEMENT DE CODE NÉCESSAIRE
- `is_trend_favorable()` autorise déjà les SELL quand `price <= MA50`, et bloque les BUY en downtrend.
- Vérifié en production le 2026-07-24 : le filtre bloque activement les BUY (`Filtre MA50 ... signal BUY ignore pour dca_4h / grid_4h / rsimacd_1h`).
- La vraie limite est structurelle : `dca_bot` est BUY-only par conception et reste le pire contributeur (13 trades, 0 gain, -225.64). Décision d'exploitation, pas de code : envisager de le désactiver.

### Fix #7 — Partial TP sans état — FAIT (commit 866268e)
Fichier : `app/services/bot_runner.py`
- **Correction du diagnostic initial** : H7 avait été classée « latente, jamais déclenchée ». C'était vrai pour les 25 trades fermés mais FAUX en réalité — le trade ouvert #31 le prouve.
- `calculate_partial_tp()` est stateless : tant que le prix dépasse le palier 50% du TP, elle renvoie `should_close=True` à **chaque cycle de 5 min**. La position était donc divisée par deux et du PnL fictif crédité en boucle.
- Constaté : trade #31 avec `quantity = 5.7e-12` et `pnl` fictif de 2.27 après ~4h (~41 divisions).
- Conflit avec le Fix #1 : avec un TP ATR à 2.57%, le palier 50% sort la moitié de la position à +1.3%, réintroduisant le « couper les gagnants trop tôt » que le Fix #1 venait d'éliminer.
- Désactivé par défaut, réactivable via `enable_partial_tp` une fois réimplémenté avec suivi du palier exécuté (nécessiterait une migration Alembic).
- Trade #31 neutralisé en base (`status='closed'`, `pnl=0`), sans suppression pour conserver la trace.

---

### Fix #8 — Réouverture en boucle sur un signal déjà tradé — FAIT (commit 9c09483)
Fichier : `app/services/bot_runner.py`
- **Régression introduite par le Fix #2.** Avant, les stratégies lisaient la bougie en cours : le signal variait avec le prix et était transitoire. Depuis le passage aux bougies clôturées, le signal est constant pendant toute la durée de la bougie (jusqu'à 48 cycles en 4h).
- Le garde-fou « 1 trade ouvert par stratégie » ne couvre que la période où le trade est ouvert. Dès qu'il se fermait sur SL, le cycle suivant retrouvait le même signal encore valide et rouvrait aussitôt : ouverture / SL / réouverture en boucle dans la même bougie.
- Version séquentielle du Bug #2 historique (« accumulation infinie de trades »).
- Dédup sur le timestamp de la bougie formante : une entrée au maximum par stratégie et par bougie. Aucune migration, fenêtre déduite de `trades.opened_at`.

---

## 8. Points restants (non traités)

| Sujet | Nature | Gravité |
|---|---|---|
| Finnhub 403 à chaque cycle | Token invalide → exception avalée par `check_market_conditions()` → `can_trade=True` par défaut. Le filtre calendrier économique est inopérant. | Moyenne |
| `can_open_trade()` retourne toujours `allowed: True` | Aucune protection drawdown, `max_open_trades` calculé mais jamais appliqué. Volontaire en paper, dangereux avant le réel. | Élevée avant passage au réel |
| `deploy.sh` annonce un succès en cas d'échec | Constaté le 2026-07-24 : `no such service: backend` suivi de « Deploy terminé avec succès ». Pas de `set -e` ni de test des codes retour. | Moyenne |
| `dca_bot` BUY-only | Pire contributeur : 13 trades, 0 gain, -225.64. Décision d'exploitation. | Moyenne |
| `trailing_stop_loss()` dans `stop_loss.py` | Code mort, jamais appelé. | Faible |
| Partial TP | Désactivé. Réimplémentation propre = migration Alembic pour mémoriser le palier exécuté. | Faible |
| `side` non normalisé | Trade #31 avait `side='buy'` en minuscules, ne matchant aucun `== "BUY"` du code. | Faible |
| `exit_price` = prix du SL théorique | `check_trade_exit()` renvoie le prix du stop, pas le prix réel. Avec un échantillonnage 5 min, un gap réel serait ignoré → résultats optimistes. | Faible en paper |

---

## 9. Vérification post-correction
- Rejouer un cycle et confirmer dans les logs qu'au moins un trade atteint son TP (`exit_reason = take_profit`).
- Requête de contrôle : `SELECT exit_reason, COUNT(*) FROM trades WHERE status='closed' GROUP BY exit_reason;` → doit montrer des `take_profit`, plus seulement des `stop_loss`.
- Surveiller le win rate sur 48h après déploiement (objectif intermédiaire > 30%).
- Vérifier que `fee_total` est renseigné sur les nouveaux trades.
