import asyncio
import aiohttp
import pandas as pd
import os
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup

# To bypass cloudflare flagging
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]
# Up to 29 requests at the same time (higher than this script crashes)
sem = asyncio.Semaphore(29)


#
def extract_skills(title):
    keywords = {'Python': ['python', 'django', 'flask'], 'JavaScript': ['javascript', 'js', 'react'],
                'Backend': ['backend', 'sql', 'api'], 'Frontend': ['frontend', 'css', 'html'],
                'DevOps': ['aws', 'docker']}
    found = [skill for skill, kws in keywords.items() if any(kw in title.lower() for kw in kws)]
    return ", ".join(found) if found else "General"

async def fetch_findwork(session, page):
    async with sem:
        url = f"https://findwork.dev/?remote=true&page={page}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            await asyncio.sleep(random.uniform(0, 0.3))
            async with session.get(url, headers=headers, timeout=12) as response:
                if response.status != 200: return []
                html = await response.text()
                soup = BeautifulSoup(html, "lxml")
                job_rows = soup.select('div[id^="job-"]')

                jobs = []
                for row in job_rows:
                    title_el = row.select_one("h4.text-dark")
                    link_el = row.select_one("a[rel='cannonical']")

                    if title_el and link_el:
                        full_title = title_el.get_text(strip=True)
                        company = "N/A"
                        if "," in full_title:
                            parts = full_title.split(",")
                            title = parts[0].strip()
                            company = parts[1].strip()
                        else:
                            title = full_title

                        jobs.append({
                            "title": title,
                            "url": "https://findwork.dev" + link_el['href'],
                            "source": "Findwork",
                            "company": company,
                            "skills": extract_skills(title)
                        })
                return jobs
        except:
            return []


async def fetch_arbeitnow(session, page):
    async with sem:
        url = f"https://www.arbeitnow.com/?search=&tags=&sort_by=null&page={page}"
        try:
            await asyncio.sleep(random.uniform(0.1, 0.4))
            async with session.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15) as resp:
                if resp.status != 200: return []
                soup = BeautifulSoup(await resp.text(), "lxml")
                job_items = soup.select('li[class*="border"]') or soup.find_all("li")
                jobs = []
                for row in job_items:
                    title_el = row.select_one('[itemprop="title"]')
                    link_el = row.select_one('a[href*="/jobs/"]')
                    if title_el and link_el:
                        title_text = title_el.get_text(strip=True)
                        full_url = link_el['href']
                        if not full_url.startswith('http'): full_url = "https://www.arbeitnow.com" + full_url
                        jobs.append({"title": title_text, "url": full_url, "source": "ArbeitNow", "company": "N/A",
                                     "skills": extract_skills(title_text)})
                return jobs
        except:
            return []


async def fetch_api_portal(session, url, source, title_key, url_key):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        async with session.get(url, headers=headers, timeout=15) as resp:
            data = await resp.json()
            raw_jobs = data[1:] if source == "RemoteOK" else data.get('jobs', [])
            return [{"title": j[title_key], "url": j[url_key], "source": source, "company": j.get('company', 'N/A'),
                     "skills": extract_skills(j[title_key])} for j in raw_jobs if title_key in j]
    except:
        return []


async def PortalScrape():
    start_time = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(script_dir, "Results")
    if not os.path.exists(results_path): os.makedirs(results_path)

    print("Starting PortalScrape execution...")

    async with aiohttp.ClientSession() as session:
        tasks = []
        for p in range(1, 101): tasks.append(fetch_findwork(session, p))
        for p in range(1, 101): tasks.append(fetch_arbeitnow(session, p))
        tasks.append(fetch_api_portal(session, "https://jobicy.com/api/v2/remote-jobs", "Jobicy", "jobTitle", "url"))
        tasks.append(fetch_api_portal(session, "https://remoteok.com/api", "RemoteOK", "position", "url"))

        results = await asyncio.gather(*tasks)
        all_jobs = [item for sublist in results for item in sublist]

        df = pd.DataFrame(all_jobs)
        if not df.empty:
            df.drop_duplicates(subset=['url'], inplace=True)

            print("Scraping finished...")
            print("Result:")
            print("--------------------")
            result = df['source'].value_counts().reset_index()
            result.columns = ['Name', 'Jobs']
            print(result.to_string(index=False))
            print("--------------------")

            timestamp = datetime.now().strftime('%d.%m.%Y_%H-%M%p')
            filename = os.path.join(results_path, f"PortalScrape_{timestamp}.csv")
            df.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')

            duration = time.time() - start_time
            print(f"Scraping successful! Saved {len(df)} unique jobs in {duration:.2f}s at ./Results/PortalScrape_{timestamp}.csv")
        else:
            print("All sources returned 0 results.")


if __name__ == "__main__":
    asyncio.run(PortalScrape())