from abc import ABC, abstractmethod

from hireboost_scraper.models import JobPosting


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        """Scrape job postings for the given queries. Returns list of JobPosting."""
        ...
