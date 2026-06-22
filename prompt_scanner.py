from typing import Dict


HIGH_RISK_KEYWORDS = [
    "ignore previous instructions",
    "bypass",
    "jailbreak",
    "system prompt",
    "reveal secrets",
    "developer message"
]


def analyze_prompt(prompt: str) -> Dict:
    """
    Basic prompt risk scanner.
    """

    prompt_lower = prompt.lower()

    score = 0
    category = "normal"

    for keyword in HIGH_RISK_KEYWORDS:

        if keyword in prompt_lower:

            score += 50
            category = "prompt_injection"

    if len(prompt) > 180:
        score += 20

    if score >= 70:

        return {
            "risk_score": score,
            "risk_level": "high",
            "category": category,
            "action": "block"
        }

    elif score >= 30:

        return {
            "risk_score": score,
            "risk_level": "medium",
            "category": category,
            "action": "warn"
        }

    else:

        return {
            "risk_score": score,
            "risk_level": "low",
            "category": category,
            "action": "allow"
        }