from collections import Counter,defaultdict
import re

def normalize_phrase(phrase):
    phrase=phrase.lower()
    phrase=phrase.replace("-"," ")
    phrase=re.sub(r"[^a-z0-9\s]","",phrase)
    phrase=re.sub(r"\s+"," ",phrase)
    return phrase.strip()

class PhraseAggregator:
    def __init__(self):
        self.counts=Counter()
        self.record_map=defaultdict(set)
        self.display_names={}

    def add(self,record_id,phrases):
        unique_phrases=set()
        for phrase in phrases:
            key=normalize_phrase(phrase)
            if not  key:
                continue

            unique_phrases.add(key)
            if key not in self.display_names:
                self.display_names[key]=phrase

        for key in unique_phrases:
            self.counts[key]+=1
            self.record_map[key].add(record_id)
    
    def results(self,min_count=2):
        output=[]

        for key,count in self.counts.most_common():
            if count<min_count:
                continue

            output.append(
                {
                    "keyword":self.display_names[key],
                    "count":count,
                    "file_numbers":sorted(self.record_map[key])
                }
            )
        return output
    
    
