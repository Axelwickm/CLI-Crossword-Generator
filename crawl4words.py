from collections import Counter
from html.parser import HTMLParser
import requests
import time
import re
from math import log
import random


# Settings
RATE = 0.35
domain = "https://de.wikipedia.org"
starting_url = "/wiki/Main_Page"
filepath = "./de_wikidict.txt"
banned_in_url = ["_talk:", "Special:", "User:", "Talk:", "Wikipedia:", "Help:", "Template:", "File:"]
word_matcher = re.compile(r"(?:^|(?<= ))[a-zåäöñíßüA-ZÅÄÖÑÍẞÜ0-9]+(?= |$)")


encountered = Counter()
url_queue = []
registered_urls = set()
visited = set()
total_words = 0

new_words = []


class LinksAndWords(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inContent = False
        self.depth = 0  # Variables for reading only body of Wikipedia article

    def handle_starttag(self, tag, attrs):
        if self.inContent and tag == "div":
            self.depth += 1

        for attr in attrs:
            # Start word extraction
            if tag == "div" and attr[0] == "id" and attr[1] == "content":
                self.inContent = True

            # Extract urls from site
            if attr[0] == "href" and attr[1].startswith("/wiki/"):
                url = attr[1].split("#")[0]
                if any(x in url for x in banned_in_url):
                    continue
                if url.endswith((".js", ".jpg", ".png", ".pdf", ".css", ".svg")):
                    continue
                if attr[1] not in registered_urls:
                    url_queue.append(url)
                    registered_urls.add(url)

    def handle_endtag(self, tag):
        if self.inContent and tag == "div":
            self.depth -= 1
            if self.depth == -1:
                self.inContent = False
                self.depth = 0

    def handle_data(self, data):
        global total_words
        if self.inContent:
            for match in word_matcher.finditer(data):
                word = match.group().upper()
                if word.isdigit():  # Skip digits
                    continue
                encountered[word] += 1
                total_words += 1
                if encountered[word] == 1:
                    new_words.append(word)

    def error(self, message):
        print("HTML parser error: ", message)


def save2file():
    all_words = encountered.most_common()
    with open(filepath, "w") as f:  # Save word and frequencies in log probability
        for word, occurrences in all_words:
            f.write("{}, {}, {}\n".format(word, log(occurrences/total_words), occurrences))


# Initiate parser
parser = LinksAndWords()

# Start loop
url_queue.append(starting_url)
while url_queue:
    sub_domain = url_queue.pop(random.randrange(len(url_queue)))
    now = time.time()
    current_url = domain+sub_domain
    visited.add(current_url)
    print("Visiting url: "+current_url)
    res = requests.get(current_url)
    parser.feed(res.text)
    print("Encountered unique words: ", len(encountered))
    print("Encountered total words: ", total_words)
    print("New words count: ", len(new_words))
    print("New words: ", new_words)
    print("Urls waiting to be visited: ", len(url_queue))
    print("Visited urls: ", len(visited))
    print("\n")
    new_words = []
    delta_time = time.time() - now
    time.sleep(max(RATE-delta_time, 0))
    if len(visited) % 50 == 0:
        save2file()
