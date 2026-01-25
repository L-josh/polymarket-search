"""CLI for polymarket-utils."""

from datetime import date, datetime
from typing import Optional

import click

from polymarket_utils.client import GammaClient
from polymarket_utils.config import (
    load_config,
    Config,
    DEFAULT_CONFIG_TEMPLATE,
    CONFIG_FILE,
)
from polymarket_utils.models import Event, Market

# Load config once at module level
_config: Config = load_config()


def format_volume(volume: float) -> str:
    """Format volume as human-readable USD."""
    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.1f}M"
    if volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    return f"${volume:.0f}"


def print_events_table(events: list[Event]) -> None:
    """Print events in a simple table format."""
    if not events:
        click.echo("No events found.")
        return

    # Column widths
    id_w, title_w, vol_w, markets_w = 8, 50, 10, 8

    # Header
    click.echo(
        f"{'ID':<{id_w}} {'Title':<{title_w}} {'Volume':>{vol_w}} {'Markets':>{markets_w}}"
    )
    click.echo("-" * (id_w + title_w + vol_w + markets_w + 3))

    # Rows
    for event in events:
        title = (
            event.title[:title_w]
            if len(event.title) <= title_w
            else event.title[: title_w - 3] + "..."
        )
        click.echo(
            f"{event.id:<{id_w}} {title:<{title_w}} {format_volume(event.volume):>{vol_w}} {event.market_count:>{markets_w}}"
        )


def print_event_detail(event: Event) -> None:
    """Print detailed event information."""
    click.echo(f"Event: {event.title}")
    click.echo(f"ID: {event.id}")
    click.echo(f"Volume: {format_volume(event.volume)}")
    click.echo(f"Category: {event.category or 'N/A'}")
    click.echo(
        f"End Date: {event.end_date.strftime('%Y-%m-%d') if event.end_date else 'N/A'}"
    )
    click.echo(f"Active: {'Yes' if event.is_active else 'No'}")

    if event.description:
        click.echo(f"\nDescription:\n{event.description[:500]}")

    if event.markets:
        click.echo(f"\nMarkets ({event.market_count}):")
        click.echo("-" * 60)
        for market in event.markets:
            prices = ", ".join(
                f"{outcome}: {price:.0%}"
                for outcome, price in zip(market.outcomes, market.outcome_prices)
            )
            click.echo(f"  [{market.id}] {market.question[:50]}")
            click.echo(f"       {prices}")


def print_market_detail(market: Market) -> None:
    """Print detailed market information."""
    click.echo(f"Market: {market.question}")
    click.echo(f"ID: {market.id}")
    click.echo(f"Volume: {format_volume(market.volume)}")
    click.echo(f"Liquidity: {format_volume(market.liquidity)}")
    click.echo(f"Category: {market.category or 'N/A'}")
    click.echo(
        f"End Date: {market.end_date.strftime('%Y-%m-%d') if market.end_date else 'N/A'}"
    )
    click.echo(f"Active: {'Yes' if market.is_active else 'No'}")

    if market.outcomes and market.outcome_prices:
        click.echo("\nOutcomes:")
        for outcome, price, token_id in zip(
            market.outcomes, market.outcome_prices, market.clob_token_ids or []
        ):
            click.echo(f"  {outcome}: {price:.1%}")
            if token_id:
                click.echo(f"    Token ID: {token_id}")

    if market.description:
        click.echo(f"\nDescription:\n{market.description[:500]}")


def _get_client() -> GammaClient:
    """Create a GammaClient with config settings."""
    return GammaClient(
        cache_dir=_config.cache.dir,
        cache_ttl=_config.cache.ttl,
    )


def _progress_callback(count: int) -> None:
    """Print progress during fetch."""
    click.echo(f"\rFetching events... {count}", nl=False)


@click.group()
def main() -> None:
    """CLI utilities for Polymarket."""
    pass


@main.group()
def event() -> None:
    """Event commands."""
    pass


@main.group()
def market() -> None:
    """Market commands."""
    pass


@main.group()
def cache() -> None:
    """Cache management commands."""
    pass


@main.group()
def config() -> None:
    """Configuration commands."""
    pass


@event.command("search")
@click.argument("keyword")
@click.option(
    "--all", "include_closed", is_flag=True, help="Include closed events (slower)"
)
@click.option("--fresh", is_flag=True, help="Bypass cache and fetch from API")
@click.option(
    "--min-volume",
    type=float,
    default=None,
    help=f"Minimum volume filter (default: {_config.filters.min_volume:,.0f})",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help=f"Max end date filter (default: {_config.filters.end_date_min})",
)
def event_search(
    keyword: str,
    include_closed: bool,
    fresh: bool,
    min_volume: Optional[float],
    end_date: Optional[datetime],
) -> None:
    """Search events by keyword."""
    # Use config defaults if not overridden
    active_only = _config.filters.active_only if not include_closed else False
    min_vol = min_volume if min_volume is not None else _config.filters.min_volume
    end_date_min: Optional[date] = (
        end_date.date() if end_date else _config.filters.end_date_min
    )

    with _get_client() as client:
        events = client.get_events(
            active_only=active_only,
            force_refresh=fresh,
            on_progress=_progress_callback,
        )
        click.echo("\r" + " " * 30 + "\r", nl=False)  # Clear progress line

    # Filter by keyword (case-insensitive)
    keyword_lower = keyword.lower()
    events = [e for e in events if keyword_lower in e.title.lower()]

    # Filter by min volume
    if min_vol > 0:
        events = [e for e in events if e.volume >= min_vol]

    # Filter by end date
    if end_date_min:
        events = [
            e for e in events if e.end_date is None or e.end_date.date() >= end_date_min
        ]

    # Sort by volume descending
    events.sort(key=lambda e: e.volume, reverse=True)

    print_events_table(events)


@event.command("info")
@click.argument("event_id")
def event_info(event_id: str) -> None:
    """Show details for a specific event."""
    with _get_client() as client:
        try:
            ev = client.get_event(event_id)
        except Exception as e:
            raise click.ClickException(f"Event not found: {event_id}") from e

    print_event_detail(ev)


@market.command("info")
@click.argument("market_id")
def market_info(market_id: str) -> None:
    """Show details for a specific market."""
    with _get_client() as client:
        try:
            mkt = client.get_market(market_id)
        except Exception as e:
            raise click.ClickException(f"Market not found: {market_id}") from e

    print_market_detail(mkt)


@cache.command("refresh")
@click.option(
    "--all",
    "include_closed",
    is_flag=True,
    help="Cache all events including closed (slower)",
)
def cache_refresh(include_closed: bool) -> None:
    """Refresh the event cache."""
    active_only = not include_closed
    label = "all" if include_closed else "active"

    with _get_client() as client:
        count = client.refresh_cache(
            active_only=active_only, on_progress=_progress_callback
        )
        click.echo("\r" + " " * 30 + "\r", nl=False)  # Clear progress line
        click.echo(f"Cached {count} {label} events.")


@config.command("path")
def config_path() -> None:
    """Show the config file path."""
    click.echo(CONFIG_FILE)


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    click.echo(f"Config file: {CONFIG_FILE}")
    click.echo(f"  exists: {CONFIG_FILE.exists()}")
    click.echo("")
    click.echo("[filters]")
    click.echo(f"  active_only = {_config.filters.active_only}")
    click.echo(f"  min_volume = {_config.filters.min_volume}")
    click.echo(f"  end_date_min = {_config.filters.end_date_min}")
    click.echo("")
    click.echo("[cache]")
    click.echo(f"  ttl = {_config.cache.ttl}")
    click.echo(f"  dir = {_config.cache.dir}")


@config.command("init")
def config_init() -> None:
    """Create a default config file."""
    if CONFIG_FILE.exists():
        raise click.ClickException(f"Config file already exists: {CONFIG_FILE}")

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(DEFAULT_CONFIG_TEMPLATE)
    click.echo(f"Created config file: {CONFIG_FILE}")


@config.command("edit")
def config_edit() -> None:
    """Open config file in $EDITOR."""
    import os
    import subprocess

    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(DEFAULT_CONFIG_TEMPLATE)
        click.echo(f"Created config file: {CONFIG_FILE}")

    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    subprocess.call([editor, str(CONFIG_FILE)])
