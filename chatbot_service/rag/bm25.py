# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations
import math
from typing import Callable

def default_tokenizer(text: str) -> list[str]:
    import re
    return [match.group(0).lower() for match in re.finditer(r'[a-zA-Z][a-zA-Z0-9_]{1,}', text)]

class BM25:
    def __init__(self, corpus: list[str], tokenizer: Callable[[str], list[str]] = default_tokenizer, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.tokenizer = tokenizer
        
        self.doc_len: list[int] = []
        self.doc_freqs: list[dict[str, int]] = []
        self.idf: dict[str, float] = {}
        self.nd = len(corpus)
        self.avgdl = 0.0
        
        if self.nd == 0:
            return
            
        nd_word = {}
        sum_dl = 0
        
        for document in corpus:
            tokens = self.tokenizer(document)
            self.doc_len.append(len(tokens))
            sum_dl += len(tokens)
            
            frequencies = {}
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.doc_freqs.append(frequencies)
            
            for token in frequencies:
                nd_word[token] = nd_word.get(token, 0) + 1
                
        self.avgdl = sum_dl / self.nd
        
        for word, freq in nd_word.items():
            self.idf[word] = math.log(1 + (self.nd - freq + 0.5) / (freq + 0.5))
            
    def get_scores(self, query: str) -> list[float]:
        scores = [0.0] * self.nd
        if self.nd == 0:
            return scores
            
        tokens = self.tokenizer(query)
        for index in range(self.nd):
            score = 0.0
            doc_len = self.doc_len[index]
            frequencies = self.doc_freqs[index]
            for token in tokens:
                if token not in frequencies:
                    continue
                freq = frequencies[token]
                num = freq * (self.k1 + 1)
                den = freq + self.k1 * (1 - self.b + self.b * doc_len / (self.avgdl or 1))
                score += self.idf.get(token, 0.0) * (num / den)
            scores[index] = score
        return scores
