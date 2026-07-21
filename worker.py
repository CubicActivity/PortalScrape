import asyncio
import json
import random
import re
import sys
import aiohttp
from bs4 import BeautifulSoup
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

SKILL_KEYWORDS = {
    'UI/UX Design': [
        re.compile(r'\bux\b'),
        re.compile(r'\bui\b'),
        re.compile(r'user experience'),
        re.compile(r'user interface'),
        re.compile(r'product design'),
        re.compile(r'product designer'),
        re.compile(r'visual designer'),
        re.compile(r'web designer'),
        re.compile(r'design system'),
    ],
    'Design Tools & Motion': [
        re.compile(r'figma'),
        re.compile(r'framer'),
        re.compile(r'rive'),
        re.compile(r'webflow'),
        re.compile(r'sketch'),
        re.compile(r'adobe xd'),
        re.compile(r'canva'),
        re.compile(r'framer motion'),
    ],
    'CMS & E-Commerce': [
        re.compile(r'wordpress'),
        re.compile(r'\bwp\b'),
        re.compile(r'shopify'),
        re.compile(r'bigcommerce'),
        re.compile(r'magento'),
        re.compile(r'woocommerce'),
        re.compile(r'squarespace'),
        re.compile(r'wix'),
        re.compile(r'strapi'),
        re.compile(r'contentful'),
        re.compile(r'sanity'),
        re.compile(r'ghost'),
    ],
    'No-Code & Automation': [
        re.compile(r'airtable'),
        re.compile(r'gohighlevel'),
        re.compile(r'zapier'),
        re.compile(r'make\.com'),
        re.compile(r'n8n'),
        re.compile(r'bubble'),
        re.compile(r'retool'),
    ],
    'Frontend / JS Frameworks': [
        re.compile(r'react'),
        re.compile(r'next\.js'),
        re.compile(r'vue'),
        re.compile(r'nuxt'),
        re.compile(r'angular'),
        re.compile(r'svelte'),
        re.compile(r'typescript'),
        re.compile(r'\bjs\b'),
        re.compile(r'javascript'),
        re.compile(r'tailwind'),
        re.compile(r'css'),
        re.compile(r'html'),
        re.compile(r'bootstrap'),
        re.compile(r'sass'),
    ],
    'Full-Stack': [
        re.compile(r'fullstack'),
        re.compile(r'full-stack'),
        re.compile(r'full stack'),
        re.compile(r'mern'),
        re.compile(r'mean'),
    ],
    'CRO & Growth Web': [
        re.compile(r'\bcro\b'),
        re.compile(r'conversion rate'),
        re.compile(r'funnel'),
        re.compile(r'landing page'),
        re.compile(r'vsl'),
        re.compile(r'ab test'),
        re.compile(r'martech'),
        re.compile(r'attribution'),
        re.compile(r'google ads'),
        re.compile(r'meta ads'),
        re.compile(r'\bppc\b'),
        re.compile(r'\bseo\b'),
    ],
    'CRM Systems': [
        re.compile(r'\bcrm\b'),
        re.compile(r'hubspot'),
        re.compile(r'salesforce'),
        re.compile(r'zoho'),
        re.compile(r'activecampaign'),
        re.compile(r'klaviyo'),
        re.compile(r'dynamics 365'),
        re.compile(r'intercom'),
    ],
    'AI / LLM / Agentic': [
        re.compile(r'\bai\b'),
        re.compile(r'\bllm\b'),
        re.compile(r'genai'),
        re.compile(r'agentic'),
        re.compile(r'openai'),
        re.compile(r'langchain'),
        re.compile(r'bedrock'),
        re.compile(r'prompt engineer'),
        re.compile(r'\bnlp\b'),
        re.compile(r'vector'),
    ],
    'Backend Languages': [
        re.compile(r'python'),
        re.compile(r'node'),
        re.compile(r'express'),
        re.compile(r'\bgo\b'),
        re.compile(r'golang'),
        re.compile(r'rust'),
        re.compile(r'ruby'),
        re.compile(r'rails'),
        re.compile(r'php'),
        re.compile(r'laravel'),
        re.compile(r'c#'),
        re.compile(r'\.net'),
        re.compile(r'java'),
        re.compile(r'spring'),
    ],
    'Cloud & DevOps': [
        re.compile(r'aws'),
        re.compile(r'azure'),
        re.compile(r'gcp'),
        re.compile(r'devops'),
        re.compile(r'docker'),
        re.compile(r'kubernetes'),
        re.compile(r'\bk8s\b'),
        re.compile(r'terraform'),
        re.compile(r'ci/cd'),
        re.compile(r'\bsre\b'),
        re.compile(r'site reliability'),
    ],
    'Web3 & Crypto': [
        re.compile(r'web3'),
        re.compile(r'crypto'),
        re.compile(r'blockchain'),
        re.compile(r'solidity'),
        re.compile(r'smart contract'),
        re.compile(r'ethereum'),
        re.compile(r'solana'),
    ],
}

def clean_text(text):
  if not text:
    return "N/A"
  cleaned = " ".join(text.split())
  cleaned = (
      cleaned.replace(";", " ")
      .replace(",", " ")
      .replace("&Amp", "&")
      .replace('"', "")
      .strip()
  )
  return cleaned if cleaned else "N/A"

def extract_skills(title):
  if not title or title == "N/A":
    return "General"

  title_lower = title.lower()
  found = []

  for category, patterns in SKILL_KEYWORDS.items():
    for pattern in patterns:
      if pattern.search(title_lower):
        found.append(category)
        break

  return " / ".join(found) if found else "General"

async def process_task(session, task):
  source = task['source']
  page = task['page']
  headers = {"User-Agent": random.choice(USER_AGENTS)}
  jobs = []

  if source == "Findwork":
    url = f"https://findwork.dev/?remote=true&page={page}"
    try:
      await asyncio.sleep(random.uniform(0, 0.3))
      async with session.get(url, headers=headers, timeout=12) as response:
        if response.status == 200:
          html = await response.text()
          soup = BeautifulSoup(html, "lxml")

          json_scripts = soup.find_all("script", type="application/ld+json")
          for script in json_scripts:
            try:
              if not script.string:
                continue
              data = json.loads(script.string)
              postings = data if isinstance(data, list) else [data]

              for item in postings:
                if (
                    isinstance(item, dict)
                    and item.get("@type") == "JobPosting"
                ):
                  title_raw = item.get("title", "")
                  job_url = item.get("url", "")
                  hiring_org = item.get("hiringOrganization", {})

                  company_raw = ""
                  if isinstance(hiring_org, dict):
                    company_raw = hiring_org.get("name", "")
                  elif isinstance(hiring_org, str):
                    company_raw = hiring_org

                  title = clean_text(title_raw)
                  company = clean_text(company_raw)

                  # Parse "Role at Company" out of title if schema missing name
                  if company == "N/A" and " at " in title:
                    parts = title.rsplit(" at ", 1)
                    title, company = clean_text(parts[0]), clean_text(parts[1])

                  if title != "N/A" and job_url:
                    full_url = (
                        job_url
                        if job_url.startswith("http")
                        else f"https://findwork.dev{job_url}"
                    )
                    jobs.append({
                        "title": title,
                        "url": full_url,
                        "source": "Findwork",
                        "company": company,
                        "skills": extract_skills(title),
                    })
            except (json.JSONDecodeError, AttributeError):
              continue

          if not jobs:
            job_rows = (
                soup.select('div[id^="job-"]')
                or soup.select("div.card")
                or soup.select("li.job")
                or soup.select("div.job-listing")
            )

            for row in job_rows:
              title_el = (
                  row.select_one("h4.text-dark")
                  or row.select_one("h4")
                  or row.select_one("a.job-title")
                  or row.select_one("h3")
              )
              link_el = row.select_one("a[rel='cannonical']") or row.select_one(
                  "a[href*='/jobs/']"
              )

              if not (title_el and link_el):
                continue

              raw_title = title_el.get_text(strip=True)
              company = "N/A"

              company_el = (
                  row.select_one("a[href*='/companies/']")
                  or row.select_one("a[href*='/company/']")
                  or row.select_one(".company-name")
                  or row.select_one("p.text-muted")
                  or row.select_one("p.text-secondary")
                  or row.select_one("span.company")
                  or row.select_one("div.company")
              )

              if company_el:
                company = clean_text(company_el.get_text())

              if company == "N/A":
                if " at " in raw_title:
                  parts = raw_title.rsplit(" at ", 1)
                  clean_title = clean_text(parts[0])
                  company = clean_text(parts[1])
                elif " - " in raw_title:
                  parts = raw_title.rsplit(" - ", 1)
                  clean_title = clean_text(parts[0])
                  company = clean_text(parts[1])
                elif "," in raw_title:
                  parts = raw_title.rsplit(",", 1)
                  clean_title = clean_text(parts[0])
                  company = clean_text(parts[1])
                else:
                  clean_title = clean_text(raw_title)
              else:
                clean_title = clean_text(raw_title)

              href = link_el["href"]
              full_url = (
                  href if href.startswith("http") else f"https://findwork.dev{href}"
              )

              jobs.append({
                  "title": clean_title,
                  "url": full_url,
                  "source": "Findwork",
                  "company": company,
                  "skills": extract_skills(clean_title),
              })

          if not jobs:
            for a_tag in soup.find_all(
                "a", href=re.compile(r"^/(jobs/|[a-zA-Z0-9]{5,8}/)")
            ):
              text = a_tag.get_text(strip=True)
              if " at " in text:
                parts = text.rsplit(" at ", 1)
                title = clean_text(parts[0])
                company = clean_text(parts[1])
                href = a_tag["href"]
                full_url = (
                    href
                    if href.startswith("http")
                    else f"https://findwork.dev{href}"
                )

                jobs.append({
                    "title": title,
                    "url": full_url,
                    "source": "Findwork",
                    "company": company,
                    "skills": extract_skills(title),
                })
    except Exception:
      print("error findwork")

  elif source == "ArbeitNow":
    url = f"https://www.arbeitnow.com/?search=&tags=&sort_by=null&page={page}"
    try:
      await asyncio.sleep(random.uniform(0.1, 0.4))
      async with session.get(url, headers=headers, timeout=15) as resp:
        if resp.status == 200:
          soup = BeautifulSoup(await resp.text(), "lxml")
          job_items = soup.select('li[class*="border"]') or soup.find_all("li")
          for row in job_items:
            title_el = (
                row.select_one('[itemprop="title"]')
                or row.select_one("h2")
                or row.select_one("h3")
            )
            link_el = row.select_one('a[href*="/jobs/"]')

            company_el = (
                row.select_one('[itemprop="hiringOrganization"]')
                or row.select_one('a[href*="/company/"]')
                or row.select_one('a[href*="/companies/"]')
                or row.select_one(".company-name")
                or row.select_one("p.text-gray-500")
                or row.select_one("span.text-muted")
            )

            if title_el and link_el:
              title_text = clean_text(title_el.get_text())
              company_text = (
                  clean_text(company_el.get_text()) if company_el else "N/A"
              )
              full_url = link_el["href"]
              if not full_url.startswith("http"):
                full_url = "https://www.arbeitnow.com" + full_url

              jobs.append({
                  "title": title_text,
                  "url": full_url,
                  "source": "ArbeitNow",
                  "company": company_text,
                  "skills": extract_skills(title_text),
              })
    except Exception:
      print("error arbeitnow")

  return jobs


async def worker_loop(worker_id):
  print(f"[*] Worker '{worker_id}' started. Listening for tasks...")

  async with aiohttp.ClientSession() as session:
    while True:
      try:
        item = r.blpop("scrape_queue", timeout=2)
      except Exception:
        print(f"[*] Worker '{worker_id}': Queue empty. Shutting down.")
        break

      if item is None:
        print(f"[*] Worker '{worker_id}': Queue empty. Shutting down.")
        break

      _, task_raw = item
      task = json.loads(task_raw)

      jobs = await process_task(session, task)
      for job in jobs:
        r.rpush("scraped_results", json.dumps(job))

      r.incr("scraped_progress")


if __name__ == "__main__":
  worker_name = sys.argv[1] if len(sys.argv) > 1 else "Worker-1"
  asyncio.run(worker_loop(worker_name))