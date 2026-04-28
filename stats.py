import json
import threading
from collections import Counter
from urllib.parse import urlparse


# English stopword list
STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be
because been before being below between both but by can can't cannot
could couldn't did didn't do does doesn't doing don't down during each
few for from further had hadn't has hasn't have haven't having he he'd
he'll he's her here here's hers herself him himself his how how's i i'd
i'll i'm i've if in into is isn't it it's its itself let's me more most
mustn't my myself no nor not of off on once only or other ought our ours
ourselves out over own same shan't she she'd she'll she's should
shouldn't so some such than that that's the their theirs them themselves
then there there's these they they'd they'll they're they've this those
through to too under until up very was wasn't we we'd we'll we're we've
were weren't what what's when when's where where's which while who who's
whom why why's with won't would wouldn't you you'd you'll you're you've
your yours yourself yourselves
ll re ve
""".split())


# Reused Assignment 1 tokenizer
def tokenize(text):
    tokens = []
    current = ""
    for ch in text:
        if ch.isalnum() and ch.isascii():
            current = current + ch.lower()
        else:
            if current != "":
                tokens.append(current)
                current = ""
    if current != "":
        tokens.append(current)
    return tokens


class Stats:
    def __init__(self, save_path="crawl_stats.json"):
        self.lock = threading.Lock()
        self.save_path = save_path
        self.unique_urls = set()
        self.longest_page_url = ""
        self.longest_page_words = 0
        self.word_counts = Counter()
        self.subdomain_pages = {}
        self.seen_text_hashes = set()
        self.pages_added = 0

    def is_duplicate(self, text_hash):
        with self.lock:
            return text_hash in self.seen_text_hashes

    def mark_seen(self, text_hash):
        with self.lock:
            self.seen_text_hashes.add(text_hash)

    def record_page(self, url, tokens):
        with self.lock:
            if url in self.unique_urls:
                return
            self.unique_urls.add(url)

            if len(tokens) > self.longest_page_words:
                self.longest_page_words = len(tokens)
                self.longest_page_url = url

            for word in tokens:
                if word not in STOPWORDS and len(word) >= 2:
                    self.word_counts[word] += 1

            host = (urlparse(url).hostname or "").lower()
            if host.endswith(".uci.edu") or host == "uci.edu":
                self.subdomain_pages.setdefault(host, set()).add(url)

            self.pages_added += 1
            if self.pages_added % 25 == 0:
                self._save_locked()

    def save(self):
        with self.lock:
            self._save_locked()

    def _save_locked(self):
        data = {
            "unique_url_count": len(self.unique_urls),
            "longest_page": {
                "url": self.longest_page_url,
                "word_count": self.longest_page_words,
            },
            "top_50_words": self.word_counts.most_common(50),
            "subdomains": [
                [host, len(urls)]
                for host, urls in sorted(self.subdomain_pages.items())
            ],
        }
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


STATS = Stats()
