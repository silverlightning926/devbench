import typer
from typing import Optional, Dict, List
import importlib.metadata
from rich.progress import Progress, BarColumn, TimeElapsedColumn
from rich.console import Console
from rich.table import Table
from rich import print
import subprocess
import os
from pyfiglet import Figlet
from devbench.components.selection_list.selection_list import SelectionList

__version__ = importlib.metadata.version('devbench')

app = typer.Typer(name="devbench", add_completion=False)

DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS = {
    "compilation": {
        "C": ["gcc", "--version"],
        "C++": ["g++", "--version"],
        "C#": ["dotnet", "--info"],
        "Java": ["javac", "-version"],
        "Kotlin": ["kotlinc", "-version"],
        "Rust": ["rustc", "--version"],
        "Go": ["go", "version"],
    },
    "runtime": {
        "C#": ["dotnet", "--version"],
        "Java": ["java", "-version"],
        "Kotlin": ["kotlin", "-version"],
        "Go": ["go", "version"],
        "Node.js": ["node", "--version"],
        "Python": ["python", "--version"],
        "Ruby": ["ruby", "--version"],
    },
    "tools": {
        "git": ["git", "--version"],
        "pip": ["pip", "--version"],
        "npm": ["npm", "--version"],
        "gem": ["gem", "--version"],
        "cargo": ["cargo", "--version"],
        "Gradle": ["gradle", "-version"],
        "Docker": ["docker", "--version"],
    },
}

COMPILATION_BENCHMARK_COMMANDS = {
    "C": ["gcc", "-o", "test", "test.c"],
    "C++": ["g++", "-o", "test", "test.cpp"],
    "C#": ["dotnet", "build"],
    "Java": ["javac", "Test.java"],
    "Kotlin": ["kotlinc", "Test.kt"],
    "Rust": ["rustc", "test.rs"],
    "Go": ["go", "build", "test.go"],
}


def check_environment(cmd: List[str]) -> str:
    try:
        subprocess.run(cmd, env=os.environ,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "✅"
    except FileNotFoundError:
        return "❌"


def check_environments(env_type: str, table: Table, console: Console):
    with Progress(BarColumn(), TimeElapsedColumn(), transient=True) as progress:
        task = progress.add_task(
            f"[green]Checking {env_type}...", total=len(DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type]))
        for env, cmd in DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type].items():
            status = check_environment(cmd)
            table.add_row(env, status)
            progress.update(task, advance=1)


@app.command()
def doctor():
    print("[bold purple]DevBench Doctor[/bold purple]")
    print(f"[purple]DevBench Version v{__version__}[/purple]\n")

    console = Console()
    for env_type in DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS:
        table = Table(title=f"\n{env_type.capitalize()
                                 } Environments", title_justify="left")
        table.add_column("Environment")
        table.add_column("Status")
        check_environments(env_type, table, console)
        console.print(table)


@app.command()
def compile():
    typer.echo("Compilation Benchmark")

    languages = list(COMPILATION_BENCHMARK_COMMANDS.keys())

    app = SelectionList(options=languages)
    app.run()

    selected_languages = app.get_selected()


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
        f = Figlet(font="slant")
        print(f.renderText("DevBench"))
        print(f"[purple]Version {__version__}[purple]")
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
