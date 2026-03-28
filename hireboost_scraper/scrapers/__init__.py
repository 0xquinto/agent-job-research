from hireboost_scraper.scrapers.base import BaseScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {}


def register(cls: type[BaseScraper]) -> type[BaseScraper]:
    """Decorator to register a scraper class."""
    SCRAPER_REGISTRY[cls.name] = cls
    return cls


def get_all_scrapers() -> list[BaseScraper]:
    """Instantiate and return all registered scrapers."""
    return [cls() for cls in SCRAPER_REGISTRY.values()]
