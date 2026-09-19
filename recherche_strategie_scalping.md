# Recherche : meilleure stratégie de scalping BTC/USDT

## Contexte (15/09/2026) — à donner à toute IA consultée

Notre bot paper trading tourne sur Binance, BTC/USDT (aussi EUR/USDT et PAXG/USDT en swing). Le module scalping tourne sur un cycle **1 minute**, mais trade en timeframe **5m** (le 1m testé s'est révélé perdant partout). Frais réels : **0,1 % par côté, 0,2 % aller-retour**.

### Ce qu'on a déjà testé (backtest sur ~21 jours de 5m paginé, frais inclus, validation out-of-sample sur 2 moitiés indépendantes)

| Stratégie | Logique | Résultat |
|---|---|---|
| `scalp_momentum` | Breakout (cassure du plus haut/bas des N dernières bougies) + confirmation taker buy ratio | **Aucun edge réel.** 16 configurations testées (breakout_period 10/20/30, ratio 0.5-0.9, SL 0,3 %→1,0 %), PF toujours < 1 une fois les frais comptés. Désactivée. |
| `scalp_reversion` | Mean-reversion : Bollinger Bands + RSI, achète/vend le retour vers la moyenne | **Edge modeste mais réel.** SL/TP élargi à 0,8 %/1,6 % → PF 2,73 sur backtest, cohérent sur out-of-sample. Mais seulement ~7 trades sur 21 jours (signal rare). En pause le temps de cette recherche. |

### Le vrai piège découvert ce soir : le ratio frais/SL

Avec un SL de 0,3 % et 0,2 % de frais aller-retour, le R:R réel après frais tombe à 0,8:1 même si le R:R nominal affiché est 2:1. **Toute stratégie de scalping doit avoir un SL nettement plus large que le coût de transaction**, sinon elle perd structurellement même avec un bon taux de réussite brut.

### Constat marché

BTC a été en range pendant plusieurs semaines (ADX ~16, faible directionnalité) — les stratégies de breakout/suivi de tendance y échouent quasi systématiquement. Une stratégie de range/mean-reversion a mieux résisté. À garder en tête : le régime de marché peut changer, une stratégie qui marche en range peut échouer en tendance forte et vice versa.

### Ce qu'on cherche

Une **2e famille de stratégie**, différente du breakout pur et idéalement complémentaire au mean-reversion déjà en place — pas juste une variation de paramètres sur les mêmes idées (on a déjà prouvé que ça finit par du surapprentissage). Idées à explorer : order flow / carnet d'ordres, VWAP, volatilité (squeeze), structure de marché (liquidity sweep, order blocks), ou une combinaison multi-signal plus robuste.

---

## Liste de recherche web

- `crypto scalping strategy BTC/USDT 5 minute backtest`
- `mean reversion vs momentum scalping crypto which works better`
- `order flow scalping strategy bitcoin futures/spot`
- `VWAP scalping strategy crypto backtest results`
- `volatility squeeze breakout strategy crypto (Bollinger + Keltner)`
- `market maker vs taker scalping strategy binance fees impact`
- `walk-forward analysis crypto scalping strategy validation`
- `why do most scalping strategies fail backtest overfitting`
- `liquidity sweep / stop hunt scalping strategy crypto`
- `range trading strategy low ADX market crypto`
- `binance taker buy sell ratio order flow signal effectiveness`
- `scalping strategy transaction cost fee breakeven win rate calculation`

## Prompts prêts à copier pour une autre IA

### Prompt 1 — Recherche de stratégie avec contraintes réelles

```
Je gère un bot de scalping paper trading sur BTC/USDT (Binance spot), timeframe 5 minutes,
cycle de décision toutes les 1 minute. Frais réels : 0,1% par côté (0,2% aller-retour).

J'ai déjà testé et rejeté :
- Une stratégie de breakout pur (cassure de plus haut/bas sur N bougies) : aucun edge une
  fois les frais comptés, testé sur ~20 configurations différentes.
- Une stratégie mean-reversion Bollinger+RSI (SL 0,8%, TP 1,6%) : edge positif mais signal
  rare (~7 trades sur 21 jours), échantillon trop petit pour être confiant.

Contrainte critique : avec un SL de X% et 0,2% de frais aller-retour, le R:R réel après frais
est bien pire que le R:R nominal. Toute stratégie proposée doit avoir un SL suffisamment large
par rapport aux frais pour ne pas être mangée par les coûts de transaction.

Propose-moi 2-3 stratégies de scalping crypto DIFFÉRENTES du breakout et du mean-reversion
Bollinger/RSI classique (order flow, VWAP, structure de marché, volatilité, etc.), avec pour
chacune : la logique d'entrée précise, le raisonnement sur pourquoi elle pourrait avoir un edge
réel après frais, et les pièges connus de ce type de stratégie en backtest.
```

### Prompt 2 — Validation critique d'une idée trouvée

```
Voici une idée de stratégie de scalping que j'ai trouvée : [DÉCRIRE LA STRATÉGIE].

Avant que je la teste, challenge-la sérieusement :
1. Est-ce que cette logique a un edge économique plausible (pourquoi le marché laisserait
   cette inefficacité exister), ou est-ce juste un pattern qui a l'air bien sur un graphique ?
2. Sur quel type de régime de marché (tendance/range/volatil) est-elle censée fonctionner,
   et où est-ce qu'elle est censée échouer ?
3. Quels sont les pièges classiques de backtesting pour ce type de stratégie (surapprentissage,
   biais de sélection, données insuffisantes) ?
4. Avec des frais de 0,2% aller-retour, quel SL minimum faut-il pour que la stratégie ne soit
   pas structurellement perdante ?
```

### Prompt 3 — Version fusionnée (génération + auto-critique en un seul message)

Plus rapide, mais l'auto-critique est en général un peu moins sévère qu'en la demandant à froid dans un chat séparé (Prompt 2) — l'IA a tendance à défendre ce qu'elle vient de proposer.

```
Je gère un bot de scalping paper trading sur BTC/USDT (Binance spot), timeframe 5 minutes,
cycle de décision toutes les 1 minute. Frais réels : 0,1% par côté (0,2% aller-retour).

J'ai déjà testé et rejeté :
- Une stratégie de breakout pur (cassure de plus haut/bas sur N bougies) : aucun edge une
  fois les frais comptés, testé sur ~20 configurations différentes.
- Une stratégie mean-reversion Bollinger+RSI (SL 0,8%, TP 1,6%) : edge positif mais signal
  rare (~7 trades sur 21 jours), échantillon trop petit pour être confiant.

Contrainte critique : avec un SL de X% et 0,2% de frais aller-retour, le R:R réel après frais
est bien pire que le R:R nominal. Toute stratégie proposée doit avoir un SL suffisamment large
par rapport aux frais pour ne pas être mangée par les coûts de transaction.

Propose-moi 2-3 stratégies de scalping crypto DIFFÉRENTES du breakout et du mean-reversion
Bollinger/RSI classique (order flow, VWAP, structure de marché, volatilité, etc.), avec pour
chacune : la logique d'entrée précise, le raisonnement sur pourquoi elle pourrait avoir un edge
réel après frais, et les pièges connus de ce type de stratégie en backtest.

Ensuite, pour CHAQUE stratégie proposée, mets-toi immédiatement dans la peau d'un critique
sceptique et réponds honnêtement, sans complaisance pour ta propre proposition :
1. Est-ce que cette logique a un edge économique plausible (pourquoi le marché laisserait
   cette inefficacité exister), ou est-ce juste un pattern qui a l'air bien sur un graphique ?
2. Sur quel régime de marché (tendance/range/volatil) fonctionne-t-elle, et où échoue-t-elle ?
3. Quels sont les pièges classiques de backtesting pour ce type de stratégie (surapprentissage,
   biais de sélection, données insuffisantes) ?
4. Avec 0,2% de frais aller-retour, quel SL minimum faut-il pour qu'elle ne soit pas
   structurellement perdante ?

Termine par un classement des 2-3 stratégies de la plus à la moins prometteuse, en justifiant.
```

## Grille d'évaluation avant de me la soumettre

Pour qu'une stratégie proposée soit exploitable rapidement de mon côté, vérifiez qu'elle a :
- [ ] Une logique d'entrée **précise et codable** (pas juste "acheter quand ça monte fort")
- [ ] Un **raisonnement économique** (pourquoi cette inefficacité existerait)
- [ ] Idéalement des **résultats de backtest déjà montrés** par la source (avec ou sans frais — je revérifierai avec frais inclus de toute façon)
- [ ] Une indication du **régime de marché** où elle est censée fonctionner

Toute stratégie retenue passera par le même protocole que ce soir avant activation : backtest sur historique long paginé, frais inclus, validation out-of-sample sur au moins 2 fenêtres indépendantes, paper trading avant tout jugement définitif.
