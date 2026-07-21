import csv
from datetime import datetime
import json
from pathlib import Path
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def export_results():
  print("[*] Fetching raw records from Redis...")
  records = []

  while True:
    item = r.lpop('scraped_results')
    if not item:
      break
    try:
      records.append(json.loads(item))
    except json.JSONDecodeError:
      continue

  print(f"[*] Fetched {len(records)} raw records from Redis...")

  results_dir = Path(__file__).resolve().parent / 'Results'
  results_dir.mkdir(parents=True, exist_ok=True)

  timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
  output_filename = f'PortalScrape_{timestamp}.csv'
  output_path = results_dir / output_filename

  fieldnames = ['title', 'company', 'source', 'skills', 'url']

  with open(output_path, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
      writer.writerow({
          'title': record.get('title', 'N/A'),
          'company': record.get('company', 'N/A'),
          'source': record.get('source', 'N/A'),
          'skills': record.get('skills', 'General'),
          'url': record.get('url', ''),
      })

  print(
      f"[+] Success! Exported {len(records)} clean records to '{output_path}'."
  )
  print("[+] Cleared 'scraped_results' from Redis.")


if __name__ == '__main__':
  export_results()