import math


def calculate_win_probability(score: int) -> int:
    """
    Convert score (0–100) into probability % (0–100)
    using logistic curve.
    """
    prob = 1 / (1 + math.exp(-(score - 50) / 10))
    return int(prob * 100)