import jellyfish

JARO_WINKLER_THRESHOLD = 0.90
MAX_LENGTH_RATIO = 0.25  # reject if length difference exceeds 25% of the shorter string


def _length_ratio_ok(a: str, b: str) -> bool:
    shorter = min(len(a), len(b))
    if shorter == 0:
        return True
    return abs(len(a) - len(b)) / shorter <= MAX_LENGTH_RATIO


def fuzzy_match_gazetteer(tokens: list[str], alias_to_canonical: dict[str, str]) -> set[str]:
    """Match tokens against gazetteer aliases via Jaro-Winkler, Metaphone, and Soundex.
    Only runs on tokens of length >= 4 to avoid over-matching short words.
    Length ratio check prevents matching overly dissimilar-length strings."""
    matched: set[str] = set()
    candidates = [t for t in tokens if len(t) >= 4]

    # Also try adjacent bigrams for multi-word aliases
    bigrams = [
        f"{tokens[i]} {tokens[i + 1]}"
        for i in range(len(tokens) - 1)
        if len(tokens[i]) >= 3 and len(tokens[i + 1]) >= 3
    ]
    candidates.extend(bigrams)

    for candidate in candidates:
        try:
            cand_first = candidate.split()[0]
            candidate_meta = jellyfish.metaphone(cand_first)
            candidate_soundex = jellyfish.soundex(cand_first)
        except Exception:
            candidate_meta = ""
            candidate_soundex = ""

        for alias, canonical in alias_to_canonical.items():
            if len(alias) < 4:
                continue

            alias_first = alias.split()[0]

            # Jaro-Winkler with length ratio guard
            if _length_ratio_ok(candidate, alias):
                try:
                    jw = jellyfish.jaro_winkler_similarity(candidate, alias)
                    if jw >= JARO_WINKLER_THRESHOLD:
                        matched.add(canonical)
                        continue
                except Exception:
                    pass

            # Metaphone (first word) — require meaningful code length
            try:
                alias_meta = jellyfish.metaphone(alias_first)
                if (candidate_meta and alias_meta
                        and candidate_meta == alias_meta
                        and len(candidate_meta) >= 3
                        and _length_ratio_ok(cand_first, alias_first)):
                    matched.add(canonical)
                    continue
            except Exception:
                pass

            # Soundex (first word) — catches phonetic variants like Depew/DePuy
            try:
                alias_soundex = jellyfish.soundex(alias_first)
                if (candidate_soundex and alias_soundex
                        and candidate_soundex == alias_soundex
                        and candidate_soundex != "0000"
                        and len(cand_first) >= 4
                        and _length_ratio_ok(cand_first, alias_first)):
                    matched.add(canonical)
            except Exception:
                pass

    return matched
