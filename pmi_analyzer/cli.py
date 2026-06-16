"""CLI for pmi_analyzer."""

import logging
import click
from pathlib import Path
from pmi_analyzer.i18n import _, set_locale

DEFAULT_HISTORICAL_CSV = Path("data") / "shamkh_historical.csv"


@click.group()
@click.option("--locale", default="fa", type=click.Choice(["fa", "en"]), help="Language (fa/en)")
def cli(locale: str):
    """PMI Analyzer - Shamkh (PMI) analysis tool."""
    set_locale(locale)


# --------------------------------------------------------------------------- #
#  build-historical
# --------------------------------------------------------------------------- #


@cli.command("build-historical")
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(),
    default=str(DEFAULT_HISTORICAL_CSV),
    show_default=True,
    help="Path to shamkh_historical.csv",
)
@click.option(
    "--pdf-dir",
    type=click.Path(),
    default="data/pdfs",
    show_default=True,
    help="Directory to store downloaded PDFs",
)
@click.option(
    "--delay",
    type=float,
    default=1.5,
    show_default=True,
    help="Delay (seconds) between HTTP requests",
)
@click.option("--verbose", is_flag=True, help="Show debug logs")
def build_historical(csv_path: str, pdf_dir: str, delay: float, verbose: bool):
    """Bootstrap shamkh_historical.csv from scratch.

    Scrapes ALL historical Shamkh PDF links from otaghiranonline.ir and
    iccima.ir, downloads every PDF, parses each one, and writes the full
    history to the CSV.  Safe to re-run: already-present months are skipped.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    from pmi_analyzer.scraper.archive_scraper import ArchiveScraper
    from pmi_analyzer.scraper.batch_downloader import BatchDownloader
    from pmi_analyzer.scraper.batch_parser import BatchParser
    from pmi_analyzer.data.loader import append_record

    csv = Path(csv_path)
    pdfs = Path(pdf_dir)

    # ---- Phase 1: discover ------------------------------------------------
    click.echo("🔍  Phase 1: Discovering all historical report links...")
    scraper = ArchiveScraper(delay=delay)
    links = scraper.discover_all()
    click.echo(f"    Found {len(links)} unique links.")

    if not links:
        click.echo("❌  No links found. Check your internet connection or site availability.")
        raise SystemExit(1)

    # ---- Phase 1b: resolve missing PDF URLs --------------------------------
    missing = sum(1 for lnk in links if not lnk.pdf_url)
    if missing:
        click.echo(f"🔗  Phase 1b: Resolving {missing} missing PDF URLs...")
        links = scraper.resolve_missing_pdfs(links)

    # ---- Phase 2: download -------------------------------------------------
    click.echo(f"⬇️   Phase 2: Downloading PDFs to {pdfs}/ ...")
    downloader = BatchDownloader(pdf_dir=pdfs, delay=delay)
    results = downloader.download_all(links, skip_existing=True)
    downloaded = sum(1 for _, p in results if p and p.exists())
    click.echo(f"    Downloaded: {downloaded}/{len(links)}")

    # ---- Phase 3: parse + append ------------------------------------------
    click.echo("📄  Phase 3: Parsing PDFs and writing to CSV...")
    parser = BatchParser()
    all_metrics = parser.parse_all(results)

    new_records = 0
    existing_months: set = set()
    if csv.exists():
        from pmi_analyzer.data.loader import load_historical

        existing_months = {m.month for m in load_historical(csv)}

    for m in all_metrics:
        if m.month not in existing_months:
            append_record(m, csv)
            existing_months.add(m.month)
            new_records += 1

    click.echo(f"✅  Done. {new_records} new records written → {csv}")


# --------------------------------------------------------------------------- #
#  analyse
# --------------------------------------------------------------------------- #


@cli.command()
@click.option("--download", is_flag=True, help="Download latest report from iccima.ir")
@click.option("--pdf", type=click.Path(exists=True), help="Path to local PDF file")
@click.option(
    "--output", type=click.Path(), default="output", show_default=True, help="Output directory"
)
@click.option(
    "--historical-csv",
    "historical_csv",
    type=click.Path(),
    default=str(DEFAULT_HISTORICAL_CSV),
    show_default=True,
    help="Path to shamkh_historical.csv",
)
@click.option("--plot", is_flag=True, help="Generate full sub-indicators chart")
@click.option("--composite", is_flag=True, help="Generate composite indicators chart")
@click.option("--inventory", is_flag=True, help="Generate inventory comparison chart")
@click.option("--expectations", is_flag=True, help="Generate production expectations chart")
@click.option("--labor", is_flag=True, help="Generate employment & exports chart")
def analyse(
    download: bool,
    pdf: str,
    output: str,
    historical_csv: str,
    plot: bool,
    composite: bool,
    inventory: bool,
    expectations: bool,
    labor: bool,
):
    """Analyze Shamkh (PMI) data."""
    from pmi_analyzer.downloader.iccima_downloader import ICCIMADownloader
    from pmi_analyzer.parser.pdf_parser import PDFParser
    from pmi_analyzer.metrics.calculator import MetricsCalculator
    from pmi_analyzer.plotter.plotly_plotter import PlotlyPlotter
    from pmi_analyzer.data.loader import load_historical, append_record

    if not download and not pdf:
        raise click.UsageError(_("Either --download or --pdf required"))

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    hist_csv = Path(historical_csv)

    # ---- Bootstrap historical CSV if missing ------------------------------
    if not hist_csv.exists():
        click.echo(
            "⚠️  shamkh_historical.csv not found.\n"
            "   Running full historical bootstrap first (this may take a few minutes)...\n"
            "   Tip: you can also run `pmi-analyzer build-historical` separately.\n"
        )
        from pmi_analyzer.scraper.archive_scraper import ArchiveScraper
        from pmi_analyzer.scraper.batch_downloader import BatchDownloader
        from pmi_analyzer.scraper.batch_parser import BatchParser

        scraper = ArchiveScraper(delay=1.5)
        links = scraper.discover_all()
        click.echo(f"   Discovered {len(links)} historical links.")

        missing_pdf = sum(1 for lnk in links if not lnk.pdf_url)
        if missing_pdf:
            links = scraper.resolve_missing_pdfs(links)

        pdf_dir = Path("data/pdfs")
        downloader = BatchDownloader(pdf_dir=pdf_dir, delay=1.5)
        results = downloader.download_all(links, skip_existing=True)
        click.echo(f"   Downloaded {sum(1 for _, p in results if p and p.exists())} PDFs.")

        parser_batch = BatchParser()
        all_metrics = parser_batch.parse_all(results)

        seen: set = set()
        for m in all_metrics:
            if m.month not in seen:
                append_record(m, hist_csv)
                seen.add(m.month)

        click.echo(f"   Historical bootstrap complete: {len(seen)} records → {hist_csv}\n")

    # ---- Download latest --------------------------------------------------
    pdf_path = Path(pdf) if pdf else None
    if download:
        click.echo("Downloading latest Shamkh report...")
        downloader_latest = ICCIMADownloader()
        pdf_path = downloader_latest.download_latest()
        click.echo(f"Downloaded: {pdf_path}")

    # ---- Parse this month -------------------------------------------------
    click.echo(f"Parsing: {pdf_path}")
    parser = PDFParser()
    metrics_list = parser.parse(pdf_path)

    # ---- Append new month to historical CSV -------------------------------
    if hist_csv.exists():
        existing_months = {m.month for m in load_historical(hist_csv)}
    else:
        existing_months = set()

    for m in metrics_list:
        if m.month not in existing_months:
            append_record(m, hist_csv)
            click.echo(f"   Appended new record ({m.month}) → {hist_csv}")
        else:
            click.echo(f"   Month {m.month!r} already in historical CSV, skipping append.")

    # ---- Calculate + save current-month CSV -------------------------------
    calculator = MetricsCalculator()
    df = calculator.calculate(metrics_list)

    csv_path = output_dir / "shamkh_data.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    click.echo(_("Output CSV: {path}").format(path=csv_path))

    # ---- Charts -----------------------------------------------------------
    plotter = PlotlyPlotter()

    if plot:
        path = plotter.plot_full_shamkh(df, output_dir)
        click.echo(_("Chart saved: {path}").format(path=path))

    if composite:
        path = plotter.plot_composite_indicators(df, output_dir)
        click.echo(_("Chart saved: {path}").format(path=path))

    if inventory:
        path = plotter.plot_inventory_comparison(df, output_dir)
        click.echo(_("Chart saved: {path}").format(path=path))

    if expectations:
        path = plotter.plot_production_expectations(df, output_dir)
        click.echo(_("Chart saved: {path}").format(path=path))

    if labor:
        path = plotter.plot_labor_and_exports(df, output_dir)
        click.echo(_("Chart saved: {path}").format(path=path))


if __name__ == "__main__":
    cli()
