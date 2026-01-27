#!/usr/bin/env python3
import click
from ingestion.scraper import scrape
from notifications.email import send_digest

@click.group()
def cli():
    """Raider Power Zone CLI."""
    pass

@cli.command()
def ingest():
    """Run ingestion job."""
    scrape()

@cli.command()
def digest():
    """Send daily email digest."""
    from notifications.email import send_digest
    send_digest()

@cli.command()
def alert():
    """Check and send low usage alert if conditions are met."""
    from notifications.email import check_and_send_alert
    check_and_send_alert()

@cli.command()
def sample_data():
    """Generate sample data for testing."""
    from scripts.generate_sample_data import generate_sample_data
    generate_sample_data()

if __name__ == "__main__":
    cli()
