1. Install dependencies
In the terminal, run these two commands in order:

python -m pip install packages/spacetime-2.1.1-py3-none-any.whl
python -m pip install -r packages/requirements.txt


2. Connect to UCI VPN and Run a test crawl
Always use --restart for test runs so you start fresh each time:

python launch.py --restart

Let it run for 30 minutes to 1 hour for a test. Or even hours.


3. Stop the crawler
Press Ctrl+C (Cmd+C on Mac) in the terminal where it's running.

You may need to press it twice.


4. Check the stats file
Open crawl_stats.json in your code editor. It looks like:
{
  "unique_url_count": 425,
  "longest_page": {
    "url": "https://www.ics.uci.edu/...",
    "word_count": 8234
  },
  "top_50_words": [
    ["research", 412],
    ["student", 387],
    ...
  ],
  "subdomains": [
    ["cs.uci.edu", 32],
    ["ics.uci.edu", 287],
    ...
  ]
}
This file updates automatically every 25 pages while the crawler runs.


5. Check the log
Open the Logs/ folder. You'll see Worker.log — that's where every URL the crawler tried to fetch is recorded.

To see just the most recent activity:

On Windows (PowerShell):

Get-Content Logs\Worker.log -Tail 100
On Mac/Linux:


tail -n 100 Logs/Worker.log


6. Spot bad patterns and add trap rules (the actual point of test runs)
Scroll through the recent log lines and look for anything weird.
If you spot a new pattern not already covered, tell the team and we'll add it to scraper.py.


7. Repeat
After adding new trap rules:

python launch.py --restart

Run again, watch the log, repeat. Goal: by the last test run, the log should look with mostly real ICS/CS/Informatics/Stat content URLs.


NOTE:
Schedule reminder!
Test Period (practice run)
now → Fri May 1, 8 PM
Deployment (real run, only 3 restarts allowed total)
Fri May 1, 9 PM → Thu May 7, 8 AM
Submit on Canvas
by Thu May 7, 8 AM


TLDR: just run the crawler, wait 30–60 minutes, hit Ctrl+C, then open crawl_stats.json and check the log.


EXAMPLE TRAPS!
Example 1: Same URL pattern repeating:

Downloaded https://www.ics.uci.edu/calendar/2024/01/, status <200>
Downloaded https://www.ics.uci.edu/calendar/2024/02/, status <200>
Downloaded https://www.ics.uci.edu/calendar/2024/03/, status <200>
Downloaded https://www.ics.uci.edu/calendar/2024/04/, status <200>
Downloaded https://www.ics.uci.edu/calendar/2024/05/, status <200>
... (200 more lines like this)
That's a calendar trap. The crawler is stuck. You'd add a rule for /calendar/ to BAD_PATHS.


Example 2: Lots of identical URLs with different query params:

Downloaded https://www.ics.uci.edu/post?utm_source=facebook
Downloaded https://www.ics.uci.edu/post?utm_source=twitter
Downloaded https://www.ics.uci.edu/post?utm_source=email
... (many more)
That's a tracking parameter trap. Same content, different URL each time. Add utm_source to BAD_QUERY_PARAMS.


Example 3: Lots of 6xx errors
Downloaded https://www.ics.uci.edu/x, status <603>
Downloaded https://www.ics.uci.edu/y, status <603>
Downloaded https://www.ics.uci.edu/z, status <603>
Cache server is down. Wait it out AND don't restart aggressively.


Healthy log looks like this!
Downloaded https://www.ics.uci.edu/people/professor-name, status <200>
Downloaded https://www.cs.uci.edu/research/areas/security, status <200>
Downloaded https://www.informatics.uci.edu/courses/, status <200>
Downloaded https://www.ics.uci.edu/news/2024-graduate-research, status <200>
Downloaded https://stat.uci.edu/people/students/, status <200>
Different URLs, real content paths, no obvious patterns. That's the goal.


Optional: pretty-print JSON in terminal

python -m json.tool crawl_stats.json