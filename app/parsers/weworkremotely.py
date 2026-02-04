"""
WeWorkRemotely Parser - Fetch jobs from WeWorkRemotely RSS feeds
"""

import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)

# WWR RSS feed URLs
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]


class WeWorkRemotelyParser(BaseParser):
    """Parser for WeWorkRemotely RSS feeds."""

    @property
    def source_name(self) -> str:
        return "weworkremotely"

    def parse(self, html: str, email_date: str) -> list:
        """
        Not used for WWR - use fetch_jobs() instead.

        This method exists to satisfy the abstract base class.
        WWR uses RSS feeds, not email HTML.
        """
        return []

    def fetch_jobs(self, days_back: int = 7) -> list:
        """
        Fetch remote jobs from WeWorkRemotely RSS feeds.

        Args:
            days_back: Only return jobs published within this many days (default: 7)

        Returns:
            List of job dictionaries
        """
        jobs = []
        cutoff = datetime.now() - timedelta(days=days_back)

        for feed_url in WWR_FEEDS:
            try:
                req = urllib.request.Request(feed_url, headers={"User-Agent": "JobTracker/1.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()

                root = ET.fromstring(xml_data)

                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    pub_date_elem = item.find("pubDate")

                    if title_elem is None or link_elem is None:
                        continue

                    title = title_elem.text or ""
                    url = self.clean_job_url(link_elem.text or "")
                    description = desc_elem.text if desc_elem is not None else ""

                    company = ""
                    job_title = title
                    if ":" in title:
                        parts = title.split(":", 1)
                        company = parts[0].strip()
                        job_title = parts[1].strip()

                    pub_date = datetime.now().isoformat()
                    if pub_date_elem is not None and pub_date_elem.text:
                        try:
                            from email.utils import parsedate_to_datetime

                            dt = parsedate_to_datetime(pub_date_elem.text)
                            if dt < cutoff:
                                continue
                            pub_date = dt.isoformat()
                        except:
                            pass

                    if description:
                        soup = BeautifulSoup(description, "html.parser")
                        description = soup.get_text(" ", strip=True)[:2000]

                    job_id = self.generate_job_id(url, job_title, company)

                    jobs.append(
                        {
                            "job_id": job_id,
                            "title": job_title[:200],
                            "company": company[:100],
                            "location": "Remote",
                            "url": url,
                            "source": self.source_name,
                            "raw_text": description or title,
                            "description": description,
                            "created_at": pub_date,
                            "email_date": pub_date,
                        }
                    )

            except Exception as e:
                logger.error(f"WWR feed error ({feed_url}): {e}")

        return jobs


def fetch_wwr_jobs(days_back: int = 7) -> list:
    """
    Convenience function to fetch WWR jobs.

    Args:
        days_back: Only return jobs published within this many days

    Returns:
        List of job dictionaries
    """
    parser = WeWorkRemotelyParser()
    return parser.fetch_jobs(days_back)
