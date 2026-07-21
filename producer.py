import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

def push_tasks(total_pages=30):
    print("[*] Clearing old queues and result buffers...")
    r.delete('scrape_queue')
    r.delete('scraped_results')
    r.set('scraped_progress', 0)

    for page in range(1, total_pages + 1):
        task = {"source": "Findwork", "page": page}
        r.rpush('scrape_queue', json.dumps(task))

    for page in range(1, total_pages + 1):
        task = {"source": "ArbeitNow", "page": page}
        r.rpush('scrape_queue', json.dumps(task))

    print(f"[✓] Enqueued {r.llen('scrape_queue')} tasks across Findwork and ArbeitNow.")

if __name__ == "__main__":
    try:
        user_input = input(
            'Enter number of pages to scrape per source [Default: 60]: '
        ).strip()
        pages_to_scrape = int(user_input) if user_input else 60
    except ValueError:
        print('[-] Invalid input. Defaulting to 60 pages.')
        pages_to_scrape = 60

    push_tasks(pages_to_scrape)