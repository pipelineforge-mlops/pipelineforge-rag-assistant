# Rapport de Qualité des Données (Sprint 2)

## 1. Volumétrie
- **Nombre total de chunks évalués :** 32146

## 2. Détection de doublons
- **Doublons stricts d'identifiants (chunk_id) :** 0
- **Doublons de textes parfaits :** 5 (soit 0.02% du corpus)
  *Seuil d'alerte métier : < 1% toléré (phrases types répétées).*

## 3. Validation du Schéma et Encodage (Pydantic)
- **Erreurs de structure / encodage détectées :** 0

## 4. Statistiques de longueurs (caractères)
- **Minimum :** 250
- **Médiane :** 1000
- **Moyenne :** 1053
- **Maximum :** 2438

## 5. Conclusion

**RÉSULTAT : SUCCÈS ✅**
Les données sont intègres, correctement formatées et validées. Elles sont prêtes pour les embeddings.