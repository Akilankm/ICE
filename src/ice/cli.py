from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from ice.orchestrator.runner import IntegratedRunner

app = typer.Typer(help="ICE — Integrated Codebase Engine")


@app.command()
def normalize(
    input_csv: Path = typer.Option(..., "--input", help="Raw product input CSV."),
    output_root: Path = typer.Option(..., "--output-root", help="Run output folder."),
    config_file: Path | None = typer.Option(None, "--config", help="Integrated YAML config."),
    env_file: Path | None = typer.Option(None, "--env-file", help="Optional .env file."),
) -> None:
    runner = IntegratedRunner.from_config_file(config_file, env_file=env_file)
    df = runner.normalize_input(input_csv, output_root)
    rprint(f"[green]Canonical input written[/green]: {output_root / 'canonical_input.csv'} rows={len(df)}")


@app.command("run")
def run_command(
    input_csv: Path = typer.Option(..., "--input", help="Raw product input CSV."),
    pg_feature_input_csv: Path = typer.Option(..., "--pg-feature-input", help="PG feature coding input CSV."),
    output_root: Path = typer.Option(..., "--output-root", help="Run output folder."),
    mode: str = typer.Option("manager_validation", "--mode", help="poc_fast, manager_validation, production_audit"),
    config_file: Path | None = typer.Option("configs/integrated.yaml", "--config", help="Integrated YAML config."),
    env_file: Path | None = typer.Option(None, "--env-file", help="Optional .env file."),
    no_search: bool = typer.Option(False, "--no-search", help="Skip search and reuse existing search output."),
    no_scrape: bool = typer.Option(False, "--no-scrape", help="Skip scrape and reuse existing scrape output."),
    no_coding: bool = typer.Option(False, "--no-coding", help="Skip product coding."),
) -> None:
    runner = IntegratedRunner.from_config_file(config_file, mode=mode, env_file=env_file)
    result = runner.run(
        input_csv=input_csv,
        pg_feature_input_csv=pg_feature_input_csv,
        output_root=output_root,
        run_search=not no_search,
        run_scrape=not no_scrape,
        run_coding=not no_coding,
    )
    rprint("[green]ICE run complete[/green]")
    for key, value in result.items():
        rprint(f"{key}: {value}")


def run() -> None:
    app()


if __name__ == "__main__":
    app()
