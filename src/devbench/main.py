import typer
from typing import Optional
import importlib.metadata
from rich.progress import Progress
from rich.console import Console
from rich.table import Table
from rich import print
import subprocess
import os

__version__ = importlib.metadata.version('devbench')

app = typer.Typer(name="devbench", add_completion=False)


@app.command()
def doctor():
    print("[bold purple]DevBench Doctor[/bold purple]")
    print(f"[purple]DevBench Version v{__version__}[/purple]\n")

    compilation_environments = {
        "C": ["gcc", "--version"],
        "C++": ["g++", "--version"],
        "C#": ["dotnet", "--info"],
        "Java": ["javac", "-version"],
        "Kotlin": ["kotlin", "-version"],
        "Rust": ["rustc", "--version"],
        "Go": ["go", "version"],
    }

    runtime_environments = {
        "C#": ["dotnet", "--version"],
        "Java": ["java", "-version"],
        "Kotlin": ["kotlin", "-version"],
        "Go": ["go", "version"],
        "Node.js": ["node", "--version"],
        "Python": ["python", "--version"],
        "Ruby": ["ruby", "--version"],
    }

    tool_environments = {
        "git": ["git", "--version"],
        "pip": ["pip", "--version"],
        "npm": ["npm", "--version"],
        "gem": ["gem", "--version"],
        "cargo": ["cargo", "--version"],
        "Gradle": ["Gradle", "--version"],
        "Docker": ["docker", "--version"],
    }

    console = Console()

    compilation_table = Table(
        title="Compilation Environments", title_justify="left")
    compilation_table.add_column("Environment")
    compilation_table.add_column("Status")
    check_environments(compilation_environments,
                       compilation_table, console)

    runtime_table = Table(title="\nRuntime Environments", title_justify="left")
    runtime_table.add_column("Environment")
    runtime_table.add_column("Status")
    check_environments(runtime_environments, runtime_table, console)

    runtime_table = Table(title="\nTool Environments", title_justify="left")
    runtime_table.add_column("Environment")
    runtime_table.add_column("Status")
    check_environments(tool_environments, runtime_table, console)


def check_environments(environments, table, console):
    with Progress(transient=True) as progress:
        task = progress.add_task(
            "[green]Checking...", total=len(environments))

        for env, cmd in environments.items():
            progress.update(
                task, description=f"[green]Checking {env}...")

            try:
                subprocess.run(
                    cmd, env=os.environ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                status = "✅"
            except FileNotFoundError:
                status = "❌"

            table.add_row(env, status)
            progress.update(task, advance=1)

    console.print(table)


@app.command()
def compile(language: Optional[str] = None, test: Optional[str] = None, iterations: Optional[str] = None):
    typer.echo("Compilation Benchmark")


@app.command()
def runtime(language: Optional[str] = None, test: Optional[str] = None, iterations: Optional[str] = None):
    typer.echo("Runtime Benchmark")


@app.command()
def tools(tool: Optional[str] = None, iterations: Optional[str] = None):
    typer.echo("Tool Benchmark")


@app.command()
def all(iterations: Optional[str] = None):
    typer.echo("Run All Benchmarks")


def version_callback(value: bool):
    if value:
        print(f"DevBench v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    pass


if __name__ == "__main__":
    app()
