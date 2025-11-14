# data/generate_word_dataset.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from systems import db_manager
from wordfreq import top_n_list
from nltk.corpus import wordnet as wn


def build_dataset():
    print("Building full English word list…")

    # wordfreq 20k
    freq_words = top_n_list("en", 20000)

    # WordNet lemmas
    wn_words = set()
    for syn in wn.all_synsets():
        for lemma in syn.lemmas():
            wn_words.add(lemma.name())

    raw = set(freq_words) | wn_words

    def is_clean(w):
        return (
            w.isalpha() and len(w) >= 3 and len(w) <= 10
        )

    clean_words = [w.lower() for w in raw if is_clean(w)]
    clean_words = list(set(clean_words))

    print(f"Clean words: {len(clean_words)}")

    def meaning(word):
        syns = wn.synsets(word)
        if syns:
            return syns[0].definition()
        return "Meaning not available."

    count = 0
    for w in clean_words:
        db_manager.insert_word(w.upper(), meaning(w), None)
        count += 1

    print(f"Inserted {count} words.")
    print("Final DB total:", db_manager.count_words())


if __name__ == "__main__":
    build_dataset()
