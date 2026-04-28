import json
import sys

def main(path: str = "crawl_stats.json") -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"No stats file at {path}. Has the crawler run yet?")
        return 1

    print("=" * 60)
    print("CRAWL REPORT")
    print("=" * 60)
    print(f"\n1. Unique pages found: {data.get('unique_url_count', 0)}")

    longest = data.get("longest_page", {})
    print(
        f"\n2. Longest page: {longest.get('url', '<none>')}"
        f"\n   Word count:  {longest.get('word_count', 0)}"
    )

    print("\n3. 50 most common words:")
    for i, (word, count) in enumerate(data.get("top_50_words", []), 1):
        print(f"   {i:>2}. {word:<20} {count}")

    subs = data.get("subdomains") or data.get("ics_subdomains") or []
    print(f"\n4. Subdomains under uci.edu found: {len(subs)}")
    for host, count in subs:
        print(f"   {host}, {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "crawl_stats.json"))
