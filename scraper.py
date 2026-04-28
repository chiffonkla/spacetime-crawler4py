import hashlib
import re
from urllib.parse import urldefrag, urljoin, urlparse, parse_qsl
from bs4 import BeautifulSoup
from stats import STATS, simhash, tokenize

ALLOWED_DOMAINS = (
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
)

MAX_URL_LENGTH = 300
MAX_PATH_DEPTH = 10
MAX_QUERY_PARAMS = 6
MAX_PAGE_SIZE = 8 * 1024 * 1024  
MIN_WORDS_PER_PAGE = 50
DUPLICATE_THRESHOLD = 3

# File extensions
BAD_EXTENSIONS = re.compile(
    r".*\.("
    r"css|js|json|xml|rss|atom"
    r"|bmp|gif|jpe?g|ico|png|tiff?|svg|webp"
    r"|mp[234]|mid|ram|wav|m4[av]|wma|ogg|flac|aac"
    r"|avi|mov|mpeg|mkv|ogv|webm|wmv|swf|rm|smil"
    r"|pdf|ps|eps|tex|ppt|pptx|ppsx|thmx|mso|rtf|key|odp|ods|odt"
    r"|doc|docx|xls|xlsx|csv|tsv|dat|data|names|arff"
    r"|exe|msi|bin|apk|dll|jar|war|class"
    r"|bz2|tar|gz|tgz|7z|rar|zip|lz|lzma|xz"
    r"|psd|ai|dmg|iso|epub|cnf|sha1|sha256|md5|asc|sig"
    r"|woff2?|ttf|otf|eot|sql|sqlite|db|ipynb|mat|fig|nb"
    r")$",
    re.IGNORECASE,
)

# Path fragments 
BAD_PATHS = re.compile(
    r"(?:/wp-(?:login|admin|json)|/login|/signup|/signin|/logout|/register"
    r"|/share|/sharer|/replytocom|/feed|/atom|/rss"
    r"|/trackback|/pingback|/embed|/attachment|/cas/login)",
    re.IGNORECASE,
)

# Query parameter keys 
BAD_QUERY_PARAMS = frozenset({
    "ical", "outlook-ical", "share", "sharer",
    "action", "do",
    "rev", "revision", "diff", "version", "oldid", "history",
    "redirect_to", "redirect", "replytocom",
    "format", "print", "printable",
    "phpsessid", "sid", "session",
    "filter", "sort_by", "orderby",
    "tribe-bar-date", "eventdate",
})

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    if resp is None:
        return []

    if 300 <= resp.status < 400:
        headers = getattr(resp.raw_response, "headers", None) or {}
        location = headers.get("Location") or headers.get("location")
        if not location:
            return []
        target, _ = urldefrag(urljoin(url, location.strip()))
        return [target] if target else []

    if resp.status != 200:
        return []
    if resp.raw_response is None or not resp.raw_response.content:
        return []

    if len(resp.raw_response.content) > MAX_PAGE_SIZE:
        return []

    final_url, _ = urldefrag(resp.url or url)
    if not _in_scope(final_url):
        return []

    try:
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        except Exception:
            return []

    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    tokens = tokenize(text)

    STATS.record_page(final_url, tokens)

    if len(tokens) >= MIN_WORDS_PER_PAGE:
        text_hash = hashlib.md5(
            " ".join(tokens).encode("utf-8", "ignore")
        ).hexdigest()
        fingerprint = simhash(tokens)
        if STATS.is_duplicate(text_hash, fingerprint, DUPLICATE_THRESHOLD):
            return []
        STATS.add_fingerprint(text_hash, fingerprint)

    base_tag = soup.find("base", href=True)
    base = base_tag["href"].strip() if base_tag else final_url

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        try:
            absolute, _ = urldefrag(urljoin(base, href))
        except ValueError:
            continue
        if absolute and absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if len(url) > MAX_URL_LENGTH:
        return False
    if not _in_scope(url):
        return False

    path = parsed.path or "/"
    if BAD_EXTENSIONS.match(path) or BAD_PATHS.search(path):
        return False

    parts = [s for s in path.split("/") if s]
    if len(parts) > MAX_PATH_DEPTH:
        return False
    if _has_repeating_parts(parts):
        return False
    if sum(1 for s in parts if s.isdigit()) > 4:
        return False

    if parsed.query:
        try:
            params = parse_qsl(parsed.query, keep_blank_values=True)
        except ValueError:
            return False
        if len(params) > MAX_QUERY_PARAMS:
            return False
        for key, _ in params:
            if key.lower() in BAD_QUERY_PARAMS:
                return False
    return True

def _in_scope(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)

def _has_repeating_parts(parts, window=3):
    n = len(parts)
    for i in range(n - 2):
        if parts[i] == parts[i + 1] == parts[i + 2]:
            return True
    for i in range(n - 2 * window + 1):
        if parts[i:i + window] == parts[i + window:i + 2 * window]:
            return True
    return False
