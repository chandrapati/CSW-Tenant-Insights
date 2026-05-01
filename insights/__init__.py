"""Shared analytics that turn an evidence bundle into rendering-ready insights.

The two flavor renderers (CISO, POV) consume the structures produced here so
they stay narrative-focused and don't re-implement scoring or extraction logic.
"""

from .bundle import EvidenceBundle, load_bundle
from .posture import PostureScore, score_posture
from .risks import Risk, top_risks
from .wins import Win, top_wins
from .actions import Action, action_plan

__all__ = [
    "EvidenceBundle",
    "load_bundle",
    "PostureScore",
    "score_posture",
    "Risk",
    "top_risks",
    "Win",
    "top_wins",
    "Action",
    "action_plan",
]
