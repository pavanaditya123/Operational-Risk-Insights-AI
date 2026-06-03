from collections import Counter, defaultdict
import re


def normalize_phrase(phrase):
    phrase = phrase.lower()
    phrase = phrase.replace("-", " ")
    phrase = re.sub(r"[^a-z0-9\s]", "", phrase)
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase.strip()


def display_priority(phrase):
    phrase = str(phrase)
    uppercase_count = sum(1 for char in phrase if char.isupper())
    separator_count = phrase.count("-")
    return (normalize_phrase(phrase), -uppercase_count, -separator_count, phrase.lower())


class PhraseAggregator:
    def __init__(self):
        self.counts = Counter()
        self.record_map = defaultdict(set)
        self.display_names = {}

    def add(self, record_id, phrases):
        unique_phrases = {}
        for phrase in sorted(phrases, key=display_priority):
            key = normalize_phrase(phrase)
            if not key:
                continue

            unique_phrases.setdefault(key, phrase)
            if key not in self.display_names:
                self.display_names[key] = phrase

        for key in sorted(unique_phrases):
            self.counts[key] += 1
            self.record_map[key].add(record_id)

    def results(self, min_count=2):
        output = []

        sorted_counts = sorted(
            self.counts.items(),
            key=lambda item: (-item[1], self.display_names[item[0]].lower(), item[0]),
        )

        for key, count in sorted_counts:
            if count < min_count:
                continue

            output.append(
                {
                    "keyword": self.display_names[key],
                    "count": count,
                    "file_numbers": sorted(self.record_map[key]),
                }
            )
        return output
