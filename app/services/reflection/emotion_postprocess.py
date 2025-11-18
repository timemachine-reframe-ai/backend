"""
Post-processing and validation utilities for emotion analysis.
Normalizes labels, validates evidence, and cleans up LLM outputs.
"""

from typing import List, Dict, Any, Optional, Tuple
from .emotion_taxonomy import (
    EMOTION_TAXONOMY_KO,
    EMOTION_SYNONYMS,
    DEFAULT_POLARITY,
    DEFAULT_VAD,
)


def normalize_label(label: str) -> Optional[str]:
    """
    Normalize emotion label using synonyms and validate against taxonomy.
    Returns the canonical label if valid, None otherwise.
    """
    if not label:
        return None

    label = label.strip()

    # Check if already in taxonomy
    if label in EMOTION_TAXONOMY_KO:
        return label

    # Apply synonym mapping
    if label in EMOTION_SYNONYMS:
        canonical = EMOTION_SYNONYMS[label]
        if canonical in EMOTION_TAXONOMY_KO:
            return canonical

    return None


def clip01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    try:
        val = float(x)
        return max(0.0, min(1.0, val))
    except (TypeError, ValueError):
        return 0.5


def ensure_polarity(label: str, polarity: Optional[str]) -> str:
    """
    Ensure polarity is valid (neg/neu/pos).
    Falls back to default for the label if invalid.
    """
    if polarity in ["neg", "neu", "pos"]:
        return polarity

    # Use default polarity for this label
    return DEFAULT_POLARITY.get(label, "neu")


def ensure_vad(label: str, vad: Optional[Dict[str, float]]) -> Dict[str, float]:
    """
    Ensure VAD (valence, arousal, dominance) dict is valid.
    Falls back to default for the label if invalid or missing.
    """
    if not vad or not isinstance(vad, dict):
        return DEFAULT_VAD.get(
            label, {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
        )

    return {
        "valence": clip01(vad.get("valence", 0.5)),
        "arousal": clip01(vad.get("arousal", 0.5)),
        "dominance": clip01(vad.get("dominance", 0.5)),
    }


def validate_evidence(
    evidence: str, full_text: str, max_len: int = 200
) -> Tuple[str, List[Dict[str, int]]]:
    """
    Validate evidence string against full text.
    Returns (evidence, spans) where spans is list of {start, end} dicts.
    If evidence not found in full_text, returns ("", []).
    """
    if not evidence or not full_text:
        return ("", [])

    evidence = evidence.strip()
    if len(evidence) > max_len:
        evidence = evidence[:max_len]

    # Try to find evidence in full_text
    start_idx = full_text.find(evidence)
    if start_idx >= 0:
        return (evidence, [{"start": start_idx, "end": start_idx + len(evidence)}])

    # Evidence not found exactly, return empty
    return ("", [])


def build_emotions(
    public_emotions: List[str], emotions_detailed: List[Dict[str, Any]]
) -> List[str]:
    """
    Build top 1-3 emotion labels from emotionsDetailed by score.
    Falls back to provided public_emotions if emotionsDetailed is invalid.
    """
    if not emotions_detailed or not isinstance(emotions_detailed, list):
        return public_emotions[:3] if public_emotions else []

    # Sort by score descending
    sorted_emotions = sorted(
        emotions_detailed, key=lambda e: e.get("score", 0.0), reverse=True
    )

    # Extract top 3 labels
    top_labels = []
    for em in sorted_emotions[:3]:
        if isinstance(em, dict) and "label" in em:
            label = em["label"]
            if label and label not in top_labels:
                top_labels.append(label)

    return top_labels if top_labels else public_emotions[:3]


def postprocess_emotions(parsed: Dict[str, Any], full_text: str) -> Dict[str, Any]:
    """
    Normalize and validate emotionsDetailed array.
    Updates parsed dict in-place and returns it.
    """
    emotions_detailed = parsed.get("emotionsDetailed", [])
    if not emotions_detailed or not isinstance(emotions_detailed, list):
        return parsed

    cleaned = []
    for em in emotions_detailed:
        if not isinstance(em, dict):
            continue

        label = em.get("label", "")
        normalized_label = normalize_label(label)
        if not normalized_label:
            continue

        score = clip01(em.get("score", 0.5))
        polarity = ensure_polarity(normalized_label, em.get("polarity"))
        vad = ensure_vad(normalized_label, em.get("vad"))

        evidence_raw = em.get("evidence", "")
        evidence, spans = validate_evidence(evidence_raw, full_text, max_len=200)

        cleaned.append(
            {
                "label": normalized_label,
                "score": score,
                "polarity": polarity,
                "vad": vad,
                "evidence": evidence,
                "spans": spans,
            }
        )

    parsed["emotionsDetailed"] = cleaned

    # Rebuild public emotions from detailed
    public_emotions = parsed.get("emotions", [])
    parsed["emotions"] = build_emotions(public_emotions, cleaned)

    return parsed


def clamp_mood_timeline(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and limit moodTimeline to ~8 segments max,
    each segment with up to top-2 labels with clamped scores.
    Updates parsed dict in-place and returns it.
    """
    timeline = parsed.get("moodTimeline", [])
    if not timeline or not isinstance(timeline, list):
        return parsed

    cleaned = []
    for segment in timeline[:8]:  # Limit to 8 segments
        if not isinstance(segment, dict):
            continue

        t = segment.get("t", 0)
        labels_raw = segment.get("labels", [])

        if not isinstance(labels_raw, list):
            continue

        # Clean and normalize labels
        cleaned_labels = []
        for lbl in labels_raw:
            if not isinstance(lbl, dict):
                continue

            label = lbl.get("label", "")
            normalized_label = normalize_label(label)
            if not normalized_label:
                continue

            score = clip01(lbl.get("score", 0.5))
            cleaned_labels.append(
                {
                    "label": normalized_label,
                    "score": score,
                }
            )

        # Keep top 2 by score
        cleaned_labels.sort(key=lambda x: x["score"], reverse=True)
        cleaned_labels = cleaned_labels[:2]

        if cleaned_labels:
            cleaned.append(
                {
                    "t": t,
                    "labels": cleaned_labels,
                }
            )

    parsed["moodTimeline"] = cleaned
    return parsed
