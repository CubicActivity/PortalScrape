# PortalScrape
Asynchronous Python-based web scraper for gathering & storing hiring data from multiple hiring portals (currently scrapes from [Findwork](https://findwork.dev) and [ArbeitNow](https://www.arbeitnow.com)).

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- Python 3.10+ (3.14 recommended)

## Quick Start

1. **Start a Redis instance** on your machine:
```bash
   docker run -d --name redis-server -p 6379:6379 redis
```

2. **Create a virtual environment and install dependencies**:
```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   # source .venv/bin/activate  # macOS/Linux

   pip install -r requirements.txt
```

3. **Run the pipeline**:
```bash
   python run.py
```

   You'll be prompted for the number of parallel workers (default: 4). From there, `run.py`:
   - runs `producer.py`, which asks how many pages per source to scrape (default: 60) and enqueues the tasks into Redis
   - spins up worker processes that pull tasks off the queue and scrape concurrently, with a live `tqdm` progress bar
   - runs `export.py` once scraping finishes, writing results to `Results/PortalScrape_<timestamp>.csv`

> **Note:** `run.py` points at `.venv/Scripts/python.exe`, so it's Windows-only as written. For macOS/Linux, swap that path to `.venv/bin/python`.

## Requirements

- **Python:** 3.14+ (should also work on 3.10+)
- **Dependencies:** `aiohttp`, `beautifulsoup4`, `lxml`, `redis`, `tqdm`

## Project Files

| File | Purpose |
|---|---|
| `run.py` | Orchestrator — prompts for worker count, runs the producer, launches workers, tracks live progress via Redis, then runs the exporter. |
| `producer.py` | Prompts for pages per source, clears old queue/result data, and pushes one task per page into the `scrape_queue` Redis list. |
| `worker.py` | Pulls tasks from Redis, scrapes each source concurrently via `aiohttp` + `BeautifulSoup`, tags each job with a detected skill category, and pushes results into `scraped_results`. |
| `export.py` | Drains `scraped_results` from Redis and writes a clean, timestamped CSV into the `Results/` folder. |

## How It Works

A "task" is just one page of listings from one site — e.g. `{"source": "Findwork", "page": 3}`.

1. `producer.py` generates a task for every page of every source and pushes them into a Redis queue.
2. Multiple `worker.py` processes run in parallel, each pulling a task off the queue via `BLPOP`, scraping that page, and pushing structured job records back into Redis.
3. Job titles are matched against a keyword map (`SKILL_KEYWORDS` in `worker.py`) to tag each posting with relevant skill categories (e.g. `Frontend / JS Frameworks`, `AI / LLM / Agentic`).
4. `export.py` collects everything into a single CSV once all workers finish.

## Redis Keys Used

| Key | Type | Purpose |
|---|---|---|
| `scrape_queue` | list | Pending `(source, page)` tasks |
| `scraped_results` | list | Completed job records (JSON strings) |
| `scraped_progress` | int | Counter incremented per completed task, drives the progress bar |
