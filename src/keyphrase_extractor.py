import spacy


class KeyphraseExtractor:
    def __init__(self, model_name="en_core_web_sm"):
        self.nlp = spacy.load(model_name, disable=["ner"])

    def extract(self, text):
        doc = self.nlp(text)
        phrases = set()

        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip()

            if self._is_valid_phrase(phrase):
                phrases.add(phrase)

        return phrases

    def _is_valid_phrase(self, phrase):
        words = phrase.split()

        if len(words) < 2:
            return False

        if len(words) > 8:
            return False

        if len(phrase) < 5:
            return False

        return True
