# Diagnostic et refonte d'un bot de trading algorithmique crypto (BTC/USDT) — État de l'art 2025-2026

## TL;DR
- Un win rate de 5% sur 350+ trades n'est **pas** explicable par le seul bear market (une stratégie long-only en marché baissier tournerait autour de 35-45%) : c'est la signature quasi certaine d'un **bug d'implémentation** — stop loss trop serré par rapport à l'ATR intraday de BTC (~3-4% de range quotidien), take profit inatteignable, fill au high/low au lieu du close, ou repainting d'indicateurs. Le premier chantier est le débogage, pas la recherche de nouvelles stratégies.
- La recherche académique (Liu & Tsyvinski, *Review of Financial Studies* 2021 ; Liu, Tsyvinski & Wu, *Journal of Finance* 2022) documente **un seul facteur robuste et persistant sur BTC : le momentum time-series** (1 à 4 semaines). Les croisements RSI/MACD/MA ont un edge in-sample mais qui a largement décru et disparaît hors échantillon sur Bitcoin (Hudson & Urquhart 2019 ; Frömmel & Deprez 2024).
- Recommandation : abandonner l'approche « BUY only + oscillateurs » au profit d'un **trend-following momentum long/flat/short** (canal Donchian ou MA 50/200 + filtre ADX/régime) avec **volatility targeting** et **stops basés sur l'ATR**, en risquant 0,5-1% du capital par trade (fractional Kelly). C'est la seule famille avec un edge documenté après frais et qui gère le bear market.

## Key Findings

### 1. Le win rate de 5% est un bug, pas une stratégie perdante
Le point de départ n'est pas de chercher de meilleures stratégies mais de comprendre pourquoi le win rate est statistiquement impossible. Avec un ratio R:R de 1:1, il faut 50% de win rate pour être à l'équilibre ; à 2:1 (TP à 2×SL), le seuil de breakeven tombe à 33,3% [formule : 1/(1+R)] ; à 3:1, à 25%. Un système long-only en bear market perd de l'argent (espérance négative) mais devrait quand même gagner 30-45% de ses trades. **5% signifie que les trades sont fermés en perte de façon quasi systématique avant d'avoir la moindre chance d'atteindre le TP.** Les causes classiques, documentées dans la littérature sur les écarts backtest/live :
- **Stop loss trop serré vs volatilité intraday.** BTC a un range quotidien moyen (high-low) d'environ 3,3-4% et un mouvement 1-sigma quotidien d'environ 2,2-2,9% sur les périodes récentes. Un SL fixe à 0,5-1% est traversé par le simple bruit intraday (« stop hunt ») presque à chaque trade.
- **Fill au high/low au lieu du close.** Si le simulateur vérifie si le low de la bougie a touché le SL ET si le high a touché le TP dans la même bougie, et qu'il résout systématiquement en faveur du SL, on obtient un win rate artificiellement effondré.
- **Repainting / recalcul sur bougie non clôturée.** Calculer RSI/MACD sur la bougie en cours (non fermée) crée un signal qui « bouge » puis se retourne — le backtest voit un signal qui n'existe pas en live. C'est un piège classique documenté sur les plateformes de backtest.
- **Erreur de signe/comparaison** dans les conditions d'entrée (ex. acheter quand RSI > 70 au lieu de < 30).
- **Timing 5 min vs bougies 15m/1h/4h** : déclencher une entrée sur une bougie 4h non clôturée, ou rafraîchir le signal toutes les 5 min sur un indicateur 4h, produit des entrées incohérentes avec le backtest.
- **Double comptage des frais** ou frais appliqués deux fois (entrée + sortie comptées à chaque cycle de 5 min).

### 2. Ce qui a un edge documenté sur BTC
**Momentum time-series = le facteur le plus robuste.** Liu & Tsyvinski (*Review of Financial Studies*, 2021) établissent « a strong time-series momentum effect » sur BTC aux fréquences journalière et hebdomadaire ; Liu, Tsyvinski & Wu (*Journal of Finance*, 2022, « Common Risk Factors in Cryptocurrency ») confirment que trois facteurs — marché, taille, momentum — capturent le cross-section des rendements crypto. Le momentum 1-4 semaines domine.

**Le trend-following (Donchian / MA) surperforme le buy-and-hold en risque ajusté.** Grayscale (2023) montre qu'une simple stratégie de moyenne mobile 50 jours sur BTC a produit un Sharpe de 1,9 contre 1,3 pour le buy-and-hold (janvier 2012-juillet 2023), essentiellement en évitant les gros drawdowns de Q4 2021 et Q2 2022. Des backtests d'ensembles Donchian (2015-2025) rapportent un CAGR de 30%, Sharpe 1,58 et un max drawdown réduit à 19% contre plus de 80% pour le BTC passif.

**Les oscillateurs (RSI/MACD/croisements MA) : edge in-sample mais décroissant et fragile hors échantillon.** C'est le point critique et la raison profonde pour laquelle il faut changer d'approche. Hudson & Urquhart (*Annals of Operations Research*, 2019, « Technical trading and cryptocurrencies ») testent 14 919 règles avec corrections multi-tests (Bonferroni, Holm, Benjamini-Hochberg, Benjamini-Yekutieli) : 20-50% des règles restent significatives in-sample, avec des coûts de transaction breakeven élevés (jusqu'à 66 bps sur CoinDesk). **Mais hors échantillon (premier semestre 2018), les meilleures règles sur Bitcoin produisent un Sharpe négatif** — les auteurs écrivent : *« In the out-of-sample periods, we find negative annualized returns, Sharpe ratios and Sortino ratios for both Bitcoin prices… Bitcoin may be the least profitable cryptocurrency in the out-of-sample setting »*, alors que les trois autres cryptos moins liquides restent positives. Frömmel & Deprez (*International Review of Economics & Finance*, 2024, « Are simple technical trading rules profitable in bitcoin markets? ») confirment : *« The trading rules have a better performance before 2014, which is in line with the literature finding that the bitcoin market is becoming more efficient over time. »* Le mécanisme est l'Hypothèse des Marchés Adaptatifs : Urquhart (2016, « The inefficiency of Bitcoin »), Bariviera (2017) et Khuntia & Pattanayak (*Economics Letters*, 2018) documentent une prévisibilité qui évolue dans le temps et un exposant de Hurst tendant vers 0,5 (marche aléatoire) après ~2014.

**Momentum vs mean-reversion selon le régime.** Le momentum/trend-following domine dans les marchés en tendance ; le mean-reversion fonctionne dans les marchés en range. Un backtest public rapporte que le momentum a mieux performé avant 2021 (marchés en tendance) tandis qu'une mean-reversion résiduelle neutre au marché a excellé après 2021 (marchés plus choppy), un portefeuille 50/50 atteignant un Sharpe de 1,71 (avec les réserves d'usage sur le survivorship bias et l'overfitting propres aux backtests de blog).

### 3. Gestion du risque : les paramètres qui comptent
- **Risk par trade :** la littérature recommande 0,5-1% du capital par trade pour survivre aux séries de pertes inévitables. Le « 1% rule » est le point de départ standard pour les 50-100 premiers trades.
- **Fractional Kelly :** le full Kelly maximise la croissance mais avec des drawdowns dévastateurs (jusqu'à 60-82% dans les simulations Monte-Carlo). Le half-Kelly capture ~75% de la croissance en réduisant le drawdown d'environ moitié ; le quarter-Kelly est recommandé pour le crypto vu l'incertitude des estimations de probabilité. Un Kelly négatif = espérance négative = ne pas trader la stratégie du tout.
- **Volatility targeting :** c'est l'amélioration la mieux documentée. Barroso & Santa-Clara (*Journal of Financial Economics*, 2015, vol. 116(1), pp. 111-120) en scalant le momentum par l'inverse de sa variance réalisée : *« Managing this risk virtually eliminates crashes and nearly doubles the Sharpe ratio of the momentum strategy »* — précisément **de 0,53 (momentum non géré) à 0,97 (version risk-managée)**. Appliqué au crypto (Finance Research Letters, 2025), le momentum risk-managé fait passer le Sharpe annualisé de 1,12 à 1,42.
- **Stops ATR vs stops fixes en % :** les stops basés sur l'ATR (1,5-2× ATR) s'adaptent à la volatilité et surperforment les stops fixes en périodes de forte volatilité. C'est directement la solution au problème du bot — un stop qui « respire » avec la volatilité intraday de BTC.
- **R:R :** viser un minimum de 2:1, ce qui autorise la rentabilité même à 40% de win rate (breakeven à 33%).

### 4. Filtres, régimes et effets calendaires
- **Détection de régime :** ADX (>25 tendance, <20 range), pente de MA, largeur des bandes de Bollinger, et exposant de Hurst (H>0,55 tendance, H<0,45 mean-reversion, 0,45-0,55 = random walk où il faut réduire la taille ou s'abstenir). L'ADX est réactif mais retardé (lookback ~14 barres) ; le Hurst mesure la persistance structurelle sur 100-500 barres. Utiliser les deux de façon complémentaire, avec une règle anti-whipsaw (exiger 2 clôtures avant de changer de régime).
- **Effets calendaires :** l'expiration des futures CME (dernier vendredi du mois, 16h London ; plus les nouveaux Bitcoin Friday Futures hebdomadaires) génère une hausse documentée du volume et de la volatilité dans les 15h précédant l'expiration (Blasco, Corredor & Satrústegui ; études d'effet d'expiration sur ScienceDirect). L'effet « lundi » est en réalité un artefact d'agrégation : en données horaires il se concentre sur le dimanche 23h-00h UTC (retour des traders retail US). La plupart des autres effets jour-de-la-semaine sont fragiles et relèvent du data-mining — à ne pas surexploiter.

### 5. Erreurs classiques et validation statistique
- **Pourquoi les bots retail perdent :** frais + slippage + sur-trading + overfitting. Les frais Binance spot sont de 0,10% maker/taker (0,075% avec le rabais BNB de 25%) ; futures 0,02% maker / 0,05% taker (rabais BNB de 10%). Un aller-retour spot coûte ~0,2%, ce qui détruit les stratégies à haute fréquence. Les perpétuels ajoutent le funding rate versé toutes les 8h. Le slippage réel se situe entre 0,1% et 0,6% par ordre et peut dépasser 1,5% en période volatile — un coût que le paper trading masque totalement.
- **Détection d'overfitting :** Deflated Sharpe Ratio (Bailey & López de Prado, *Journal of Portfolio Management*, 2014) qui corrige pour le nombre d'essais, la non-normalité (skew/kurtosis) et la longueur d'échantillon ; Probability of Backtest Overfitting (PBO, Bailey et al. 2015, *Journal of Computational Finance*) ; walk-forward analysis ; combinatorial purged cross-validation (CPCV, avec purge et embargo pour éliminer le leakage). Harvey, Liu & Zhu recommandent un seuil de t-stat de 3,0 (pas 2,0) vu le « factor zoo ».
- **Nombre minimum de trades :** viser 100+ trades pour une expectancy fiable ; 30-50 est un minimum absolu. La notion de *Minimum Backtest Length* de López de Prado formalise combien d'historique est nécessaire pour éviter de sélectionner une stratégie à Sharpe in-sample élevé mais nul hors échantillon.
- **Biais de backtest :** look-ahead, survivorship, slippage sous-estimé, frais mal modélisés, funding rates ignorés, repainting d'indicateurs (indicateurs qui recalculent leurs valeurs passées : ZigZag, certains volume profiles, ATR sur bougie non clôturée).

## Details

### Le calcul qui prouve que c'est un bug
Espérance = (win rate × gain moyen) − (loss rate × perte moyenne). Même le pire scénario réaliste — long-only, entrées aléatoires, bear market à −25% — ne produit pas 5% de win rate sauf si les trades gagnants sont systématiquement empêchés d'aboutir. Si le SL est à ~1% mais que le range quotidien de BTC représente ~3-4% et que le cycle de décision est de 5 min sur des signaux 4h, chaque position est ouverte puis fermée par le bruit avant maturation. Le SL à 1% correspond à environ 0,25-0,3× ATR quotidien — soit à l'intérieur du bruit normal de la journée. La checklist de diagnostic ci-dessous doit être exécutée avant toute autre chose.

### Pourquoi le trend-following gère le bear market
Un système long/flat/short sort du marché (ou passe short) quand le prix casse sous sa MA/canal, ce qui a historiquement réduit le max drawdown de BTC de >80% à ~19-60% selon les implémentations. Le win rate d'un trend-follower est structurellement BAS (30-45%) — c'est normal et attendu ; l'edge vient de quelques gros gagnants (winners 3-5× la taille des perdants), pas de la fréquence de victoire. Il faut donc juger le système au **profit factor et au drawdown, pas au win rate**. C'est un changement de paradigme complet par rapport aux 10 stratégies actuelles « BUY only » optimisées implicitement pour un win rate élevé.

## Recommandations

### Étape 0 — Débogage obligatoire (avant toute nouvelle stratégie)
Checklist de diagnostic concrète :
1. **Logger chaque trade** : prix d'entrée, prix de SL, prix de TP, prix de sortie réel, raison de sortie, timestamp et bougie utilisée. Inspecter manuellement 10 trades perdants.
2. **Vérifier le sens des comparaisons** : RSI oversold = RSI < 30 (achat) ; MACD crossover haussier = ligne MACD croise AU-DESSUS du signal ; Bollinger bounce = achat sur la bande BASSE.
3. **Fill logic** : à l'entrée, utiliser le close de la bougie clôturée (ou l'open de la suivante), jamais le high/low. Pour SL/TP dans une même bougie, adopter une hypothèse conservatrice mais cohérente (ex. si la bougie est baissière, supposer SL touché avant TP).
4. **Ratio SL/ATR** : calculer ATR(14) et vérifier que SL ≥ 1,5× ATR. Un SL à 0,5-1% est probablement < 0,3× ATR = liquidation par le bruit.
5. **Bougies clôturées uniquement** : tous les indicateurs sur bougie[−1] fermée, jamais sur la bougie en cours (anti-repainting).
6. **Timing** : aligner le cycle de décision sur la clôture de la bougie de la timeframe utilisée (15m/1h/4h), pas sur un tick arbitraire de 5 min.
7. **Frais** : compter 0,1% une seule fois à l'entrée et une fois à la sortie (0,2% aller-retour).
8. **Sanity check** : lancer une stratégie « buy-and-hold » et une stratégie « entrées aléatoires » dans le même moteur ; si le buy-and-hold affiche aussi un win rate aberrant, le bug est dans le moteur de backtest, pas dans les stratégies.

### Étape 1 — Trois stratégies implémentables avec les indicateurs disponibles (RSI, MACD, Bollinger, MA, volume, ATR calculable depuis l'OHLCV)

**Stratégie A — Donchian/MA trend-following long/flat/short (cœur du système)**
- Timeframe : 4h (décision à la clôture de chaque bougie 4h).
- Entrée long : close > plus haut des 20 dernières bougies (canal Donchian 20) ET close > MA50 ET ADX > 20.
- Entrée short : close < plus bas des 20 dernières bougies ET close < MA50 ET ADX > 20.
- Sinon : flat.
- Stop : 2× ATR(14) du côté opposé, en trailing (le stop ne recule jamais, il ne fait que se resserrer en faveur du trade).
- Pas de TP fixe : laisser courir via le trailing stop (les gros gagnants font l'edge). Optionnel : partial TP à 3× ATR sur la moitié de la position.
- Taille : quantité = (0,75% du capital) / (2× ATR), puis ajustée par volatility targeting.
- Pourquoi ça surperforme les stratégies actuelles : c'est la seule famille avec edge académique documenté sur BTC (Liu & Tsyvinski, Grayscale), elle est **directionnelle** (donc gère le bear via le short/flat, contrairement aux 10 stratégies BUY-only), et elle est jugée au profit factor et non au win rate.

**Stratégie B — Momentum time-series avec filtre de régime (long/flat, la plus étayée académiquement)**
- Timeframe : 1h ou 4h.
- Signal : rendement cumulé sur 7-28 jours positif → long ; négatif → flat (ou short si autorisé).
- Filtre : n'agir que si Hurst > 0,55 OU ADX > 25 (régime en tendance) ; sinon rester flat.
- Stop : 2-2,5× ATR ; taille via volatility targeting.
- Pourquoi : implémentation directe du facteur momentum de Liu & Tsyvinski, la découverte la plus robuste et peer-reviewed de la littérature crypto.

**Stratégie C — Mean-reversion Bollinger conditionnée au régime (complément, marchés en range)**
- Timeframe : 15m ou 1h.
- Entrée : UNIQUEMENT si ADX < 20 (range confirmé) : achat quand close < bande de Bollinger basse (20, 2σ) ET RSI < 35 ; volume confirmant.
- Sortie : retour à la MA20 (bande médiane) ; stop 1,5× ATR sous l'entrée.
- Ne JAMAIS lancer cette stratégie quand ADX > 25 (marché en tendance = mean-reversion perd systématiquement).
- Pourquoi : capture l'edge mean-reversion documenté en régime choppy, complémentaire du trend-following. C'est une version disciplinée et filtrée de la « Bollinger bounce » actuelle.

### Étape 2 — Money management (transverse à toutes les stratégies)
- Risk 0,5-1% par trade, quarter-Kelly au départ (le temps d'estimer un win rate/R:R fiable sur 100+ trades).
- Volatility targeting : scaler la taille par (volatilité cible / volatilité réalisée sur 20 jours), plafonnée pour éviter le levier excessif.
- Un seul régime actif à la fois : router A/B en tendance, C en range, flat en random walk (0,45 < H < 0,55).

### Étape 3 — Validation avant tout passage en réel
- Minimum 100 trades ; walk-forward analysis + hold-out de 30% des données jamais touché pendant le développement.
- Calculer le Deflated Sharpe Ratio en déclarant honnêtement le nombre de stratégies/paramètres testés (vous en avez déjà testé 10+ → forte pénalité de sélection).
- Modéliser 0,1% de frais + slippage réaliste (0,1-0,6%) + funding si perpétuels.

### Seuils qui changent la recommandation
- Si après débogage le win rate long-only remonte à 35-45% en bear market : le moteur était bien le problème, et les stratégies méritent d'être ré-évaluées proprement.
- Si le trend-following affiche un profit factor < 1,2 après frais sur walk-forward : réduire la fréquence, élargir les canaux (Donchian 55), ou renoncer à cette stratégie.
- Si le DSR ≤ 0 : la stratégie est probablement un artefact d'overfitting — ne pas la déployer.
- Si le Hurst de BTC reste durablement dans 0,45-0,55 : réduire l'exposition, aucune famille (momentum ni mean-reversion) n'a d'edge fiable dans ce régime.

## Caveats
- **Honnêteté sur les limites :** aucune stratégie retail n'a d'edge durable garanti après frais. La littérature peer-reviewed (Hudson & Urquhart 2019, Frömmel & Deprez 2024, Ahmed-Grobys-Sapkota 2020) montre que même les edges techniques réels sur BTC se sont largement arbitrés depuis 2014-2018, et que **Bitcoin est la crypto la moins profitable hors échantillon** parce que c'est la plus liquide et efficiente. Le trend-following/momentum est la famille la mieux étayée, mais avec de longues périodes de drawdown (4-6 mois de pertes en marché choppy) et un Sharpe réaliste de 1-1,5, pas les chiffres mirobolants des sites de signaux.
- **La plupart des « backtests » cités sur des blogs commerciaux (win rate 77%, 86% d'accuracy, etc.) sont non vérifiables et probablement overfittés ou repaintés** — à ignorer, conformément à votre contrainte. Les sources fiables sont les papers peer-reviewed (Journal of Finance, Review of Financial Studies, Annals of Operations Research, Journal of Financial Economics) et les corrections statistiques (DSR, PBO).
- **Le momentum intraday de Bitcoin (Shen, Urquhart & Wang, *Financial Review*, 2022) est statistiquement robuste en brut** (t≈4,4, gains de market timing jusqu'à ~16,7% annualisés) **mais sa survie après frais à fréquence intraday n'est PAS confirmée** dans les sources accessibles — à traiter avec prudence, car la haute rotation est exactement le point le plus vulnérable à l'érosion par les coûts.
- **La majorité des comptes de bots crypto automatisés échouent rapidement** — la source For Traders indique que « 73% of automated crypto trading accounts fail within six months » et « 52% within three months », la cause principale étant les décalages d'exécution (slippage, latence) plutôt que des signaux défaillants. Le paper trading masque intégralement ces coûts, donc des résultats corrects en paper ne garantissent rien en réel.
- La détection de régime améliore les résultats mais ajoute des paramètres = risque d'overfitting supplémentaire. Rester parcimonieux : 2-3 indicateurs maximum par stratégie (un pour la tendance, un pour le timing, un filtre structurel), au-delà les signaux deviennent trop rares pour être statistiquement significatifs.