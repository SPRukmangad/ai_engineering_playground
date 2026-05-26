# This package contains the deterministic rule-based risk scoring engine:
#
#   risk_scorer.py - scores a release based on change volume, risk labels,
#                    categories, and component spread.
#
# No AI involved - scores are fully reproducible and explainable.
# This separation is intentional: rule-based scoring runs independently
# of the AI analysis and can be used standalone via the --no-ai flag.
