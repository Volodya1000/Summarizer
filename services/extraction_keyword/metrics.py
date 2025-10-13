# metrics.py

from typing import Set

def jaccard(a: Set[str], b: Set[str]) -> float:
    """Вычисляет коэффициент Жаккарда для двух множеств строк."""
    if not a and not b:
        return 0.0
    inter = a.intersection(b)
    uni = a.union(b)
    return len(inter) / len(uni) if uni else 0.0

# Другие метрики могут быть добавлены здесь