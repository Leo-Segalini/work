# Model card — M4

## Modèle capteur (random_forest)

- **Cible :** détection provenance fabriquée vs réelle
- **Features :** règles M3 binaires + valeur + capteur one-hot
- **Calibration F1 :** 0.782609
- **Limites :** ne prédit pas une panne ; données synthétiques formation

## RAG

- **Modèle embeddings :** sentence-transformers/all-MiniLM-L6-v2
- **Corpus :** 8 documents versionnés
- **Contrat :** citation obligatoire, abstention sans preuve
