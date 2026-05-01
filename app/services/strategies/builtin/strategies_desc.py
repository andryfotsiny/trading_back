# app/services/strategies/builtin/strategies_desc.py
STRATEGY_DESCRIPTIONS = {
    "rsi_oversold": "BUY quand RSI sort de zone survendue, SELL quand sort de zone surachetee",
    "macd_crossover": "BUY quand MACD croise signal vers le haut, SELL inverse",
    "sma_crossover": "BUY quand SMA rapide croise SMA lente vers le haut, SELL inverse",
    "bollinger_bounce": "BUY au rebond bande basse, SELL au rebond bande haute",
    "grid_trading": "BUY/SELL automatique sur une grille de prix dans un range",
    "dca_bot": "BUY quand le prix baisse sous la SMA (accumulation progressive)",
    "rsi_macd_combo": "BUY/SELL quand RSI + MACD + Bollinger confirment ensemble",
    "mtf_confluence": "Analyse HTF pour la direction + LTF pour l'entree precise. Trade uniquement dans le sens du trend global",
    "bos_structure": "Detecte les Break of Structure (cassure de plus haut/bas). Base du trading institutionnel",
    "liquidity_sweep": "Detecte les pieges institutionnels (sweep au-dessus/dessous des niveaux cles) puis entre en sens inverse",
}
