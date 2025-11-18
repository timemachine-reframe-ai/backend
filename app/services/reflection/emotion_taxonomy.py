"""
Emotion taxonomy and normalization utilities for Korean emotion labels.
Provides a fixed taxonomy, synonym mappings, polarity defaults, and VAD baselines.
"""

# Fixed Korean emotion labels (12-16 items)
EMOTION_TAXONOMY_KO = [
    "불안",  # anxiety
    "당황",  # embarrassment
    "화남",  # anger
    "슬픔",  # sadness
    "기쁨",  # joy
    "죄책감",  # guilt
    "수치심",  # shame
    "안도",  # relief
    "기대",  # expectation
    "좌절",  # frustration
    "실망",  # disappointment
    "긴장",  # tension
    "혼란",  # confusion
    "짜증",  # irritation
    "무력감",  # helplessness
    "흥분",  # excitement
]

# Simple synonym mapping to canonical taxonomy labels
EMOTION_SYNONYMS = {
    "걱정": "불안",
    "초조": "불안",
    "부끄러움": "수치심",
    "짜증남": "짜증",
    "분노": "화남",
    "희열": "기쁨",
    "즐거움": "기쁨",
}

# Default polarity mapping: label -> {"neg", "neu", "pos"}
DEFAULT_POLARITY = {
    "불안": "neg",
    "당황": "neg",
    "화남": "neg",
    "슬픔": "neg",
    "기쁨": "pos",
    "죄책감": "neg",
    "수치심": "neg",
    "안도": "pos",
    "기대": "pos",
    "좌절": "neg",
    "실망": "neg",
    "긴장": "neu",
    "혼란": "neu",
    "짜증": "neg",
    "무력감": "neg",
    "흥분": "pos",
}

# Default VAD (Valence, Arousal, Dominance) baseline in [0, 1]
# Optional: provides dimensional representation for each emotion
DEFAULT_VAD = {
    "불안": {"valence": 0.2, "arousal": 0.7, "dominance": 0.3},
    "당황": {"valence": 0.3, "arousal": 0.6, "dominance": 0.3},
    "화남": {"valence": 0.1, "arousal": 0.8, "dominance": 0.6},
    "슬픔": {"valence": 0.2, "arousal": 0.3, "dominance": 0.2},
    "기쁨": {"valence": 0.9, "arousal": 0.7, "dominance": 0.7},
    "죄책감": {"valence": 0.2, "arousal": 0.5, "dominance": 0.2},
    "수치심": {"valence": 0.2, "arousal": 0.5, "dominance": 0.2},
    "안도": {"valence": 0.7, "arousal": 0.3, "dominance": 0.6},
    "기대": {"valence": 0.7, "arousal": 0.6, "dominance": 0.6},
    "좌절": {"valence": 0.2, "arousal": 0.6, "dominance": 0.3},
    "실망": {"valence": 0.3, "arousal": 0.4, "dominance": 0.3},
    "긴장": {"valence": 0.4, "arousal": 0.7, "dominance": 0.4},
    "혼란": {"valence": 0.4, "arousal": 0.6, "dominance": 0.3},
    "짜증": {"valence": 0.3, "arousal": 0.7, "dominance": 0.5},
    "무력감": {"valence": 0.2, "arousal": 0.3, "dominance": 0.1},
    "흥분": {"valence": 0.7, "arousal": 0.9, "dominance": 0.7},
}
