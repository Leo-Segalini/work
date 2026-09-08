# Remédiation

À compléter après l'incident. Exemples de lignes types (à activer selon cause) :

| Action | Hypothèse | Responsable | Échéance | Test de non-régression | Statut |
|---|---|---|---|---|---|
| Ajouter alerte Prometheus sur `diagops_index_valid == 0` | Détection trop lente / silencieuse | Apprenant | J+1 post game day | Injecter `faults.json` → alerte visible &lt; 2 min | Prévu |
| Documenter seed history avant promo | History vide si first promote | Apprenant | Immédiat | `test_rollback` + scénario seed | Fait (rapport_rollback) |
| Étendre gate latence p95 | Régression perf non couverte | Apprenant | Avant M6 | `capacity_probe` + seuil dans gates | Ouvert |
| Rejouer scénario injecté | Correctif non vérifié | Apprenant | Fin phase 4 h remédiation | Même injection → détection+rollback | En attente injection |

## Rejeu obligatoire (phase 3)

```bash
# 1. Réinjecter le scénario (commande fournie par le formateur)
# 2. Chronométrer détection
# 3. Rollback / fix
# 4. pytest + ci_local.sh + ready 200
```
