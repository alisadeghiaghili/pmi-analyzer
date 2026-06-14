"""CLI for pmi_analyzer."""

import click
from pathlib import Path
from pmi_analyzer.i18n import _, set_locale


@click.group()
@click.option("--locale", default="fa", type=click.Choice(["fa", "en"]), help="Language (fa/en)")
def cli(locale: str):
    """PMI Analyzer - Shamkh (PMI) analysis tool."""
    set_locale(locale)


@cli.command()
@click.option("--download", is_flag=True, help="Download latest report from iccima.ir")
@click.option("--pdf", type=click.Path(exists=True), help="Path to local PDF file")
@click.option(
    "--output", type=click.Path(), default="output", show_default=True, help="Output directory"
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

    if not download and not pdf:
        raise click.UsageError(_("Either --download or --pdf required"))

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download
    pdf_path = Path(pdf) if pdf else None
    if download:
        click.echo("Downloading latest Shamkh report...")
        downloader = ICCIMADownloader()
        pdf_path = downloader.download_latest()
        click.echo(f"Downloaded: {pdf_path}")

    # Parse
    click.echo(f"Parsing: {pdf_path}")
    parser = PDFParser()
    metrics = parser.parse(pdf_path)

    # Calculate
    calculator = MetricsCalculator()
    df = calculator.calculate(metrics)

    # Save CSV
    csv_path = output_dir / "shamkh_data.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    click.echo(_("Output CSV: {path}").format(path=csv_path))

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
