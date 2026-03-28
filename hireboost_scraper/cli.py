from pathlib import Path

import click

from hireboost_scraper.runner import run_all

DEFAULT_QUERIES = [
    "Operations Manager AI",
    "AI Operations Lead",
    "Business Operations AI Integration",
    "AI Process Automation Manager",
    "Technical Operations Manager",
    "AI Agent Developer",
    "Developer Relations",
]

DEFAULT_OUTPUT = Path("research/phase-1-scrape")


@click.command()
@click.option(
    "-q", "--query",
    multiple=True,
    help="Search query (can specify multiple). Defaults to 7 built-in queries.",
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT,
    help=f"Output directory. Default: {DEFAULT_OUTPUT}",
)
@click.option(
    "-s", "--scraper",
    multiple=True,
    help="Run only specific scrapers (e.g., -s himalayas -s hn_hiring). Default: all.",
)
@click.option(
    "--remote-only/--include-onsite",
    default=True,
    help="Only include remote jobs. Default: remote-only.",
)
@click.option(
    "--list-scrapers",
    is_flag=True,
    help="List all available scrapers and exit.",
)
def main(query, output_dir, scraper, remote_only, list_scrapers):
    """HireBoost Scraper -- Multi-board job scraper for the HireBoost pipeline."""
    # Import here to trigger registration via module imports
    import hireboost_scraper.scrapers.jobspy_boards  # noqa: F401
    import hireboost_scraper.scrapers.himalayas  # noqa: F401
    import hireboost_scraper.scrapers.weworkremotely  # noqa: F401
    import hireboost_scraper.scrapers.hn_hiring  # noqa: F401
    import hireboost_scraper.scrapers.cryptojobslist  # noqa: F401
    import hireboost_scraper.scrapers.crypto_jobs  # noqa: F401
    import hireboost_scraper.scrapers.web3career  # noqa: F401
    import hireboost_scraper.scrapers.cryptocurrencyjobs  # noqa: F401

    from hireboost_scraper.scrapers import SCRAPER_REGISTRY

    if list_scrapers:
        click.echo("Available scrapers:")
        for name in sorted(SCRAPER_REGISTRY.keys()):
            click.echo(f"  - {name}")
        return

    queries = list(query) if query else DEFAULT_QUERIES
    scraper_filter = list(scraper) if scraper else None

    click.echo(f"Running {len(queries)} queries across {'all' if not scraper_filter else len(scraper_filter)} scrapers")
    click.echo(f"Output: {output_dir}")
    click.echo(f"Remote only: {remote_only}")
    click.echo("---")

    jobs = run_all(
        queries=queries,
        output_dir=output_dir,
        is_remote=remote_only,
        scrapers=scraper_filter,
    )

    click.echo(f"\nDone! {len(jobs)} unique postings written to {output_dir}/")


if __name__ == "__main__":
    main()
