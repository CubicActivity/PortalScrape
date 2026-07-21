from pathlib import Path
import subprocess
import sys
import time
import redis
from tqdm import tqdm


def main():
  try:
    worker_input = input('Enter number of parallel workers (default 4): ').strip()
    num_workers = int(worker_input) if worker_input else 4
  except ValueError:
    print('[!] Invalid input. Defaulting to 4 workers.')
    num_workers = 4

  base_dir = Path(__file__).resolve().parent
  python_exec = base_dir / '.venv' / 'Scripts' / 'python.exe'
  producer_script = base_dir / 'producer.py'
  worker_script = base_dir / 'worker.py'
  export_script = base_dir / 'export.py'


  r = redis.Redis(host='localhost', port=6379, decode_responses=True)
  r.set('scraped_progress', 0)

  print(f'\n[*] Starting pipeline with {num_workers} workers...')
  start_time = time.time()

  print('[*] Running producer to enqueue tasks...')
  prod_result = subprocess.run([str(python_exec), str(producer_script)])
  if prod_result.returncode != 0:
    print('[!] Producer failed. Aborting.')
    sys.exit(1)

  total_tasks = r.llen('scrape_queue')

  print(f'[*] Launching {num_workers} worker processes...')
  workers = []
  for i in range(1, num_workers + 1):
    worker_name = f'Worker-{i}'
    p = subprocess.Popen([str(python_exec), str(worker_script), worker_name])
    workers.append(p)

  with tqdm(
      total=total_tasks, desc='[*] Scraping Progress', unit='tasks'
  ) as pbar:
    last_val = 0
    while any(p.poll() is None for p in workers):
      current_val = int(r.get('scraped_progress') or 0)
      if current_val > last_val:
        pbar.update(current_val - last_val)
        last_val = current_val
      time.sleep(0.1)

    final_val = int(r.get('scraped_progress') or 0)
    if final_val > last_val:
      pbar.update(final_val - last_val)

  for p in workers:
    p.wait()

  print('\n[*] All workers finished. Exporting results...')

  exp_result = subprocess.run([str(python_exec), str(export_script)])
  if exp_result.returncode != 0:
    print('[!] Export failed.')
    sys.exit(1)

  elapsed_time = time.time() - start_time
  print(f'[+] Fetching complete in {elapsed_time:.2f} seconds!')


if __name__ == '__main__':
  main()