# Model Card: Netflix Cross-Sell Propensity

## Model Details
- **Algorithm:** XGBoost Classifier
- **Version:** 2.0 (Optuna-tuned)
- **Date:** June 2026
- **Input Features:** 15 engineered features (RFM, behavior, demographics)
- **Output:** Probability (0-1) of cross-sell conversion

## Intended Use
- **Primary:** Rank Netflix users by likelihood to purchase a recommended product
- **Out-of-scope:** Not for credit scoring, hiring, or any decision with legal implications

## Training Data
- **Source:** Netflix Prize dataset (100M ratings, subset to 10K users)
- **Time Range:** 1999-2005
- **Demographic Representation:** Skewed toward early DVD adopters

## Evaluation Results
| Metric | Value |
|--------|-------|
| AUC | 0.9999 |
| Accuracy | 0.9965 |
| Precision | 0.99 |
| Recall | 0.99 |

## Limitations
- **Temporal bias:** Data ends in 2005; streaming behavior may differ
- **Geographic bias:** Primarily US users
- **Fairness concerns:** Model may over-weight high-frequency users, disadvantaging casual viewers

## Ethical Considerations
- This model influences agent priorities – human oversight is required before final decisions
- Regular bias audits should be conducted on recommendation distributions across user segments

## Citation
If you use this model card template, cite: Mitchell et al. (2019) Model Cards for Model Reporting.
