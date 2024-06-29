import typer
from typing import Optional
import importlib.metadata
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.table import Table
from rich import print
import subprocess
import time
import statistics
import os
import shutil
from pyfiglet import Figlet
from devbench.components.selection_list.selection_list_app import SelectionListApp

__version__ = importlib.metadata.version('devbench')

app = typer.Typer(name="devbench", add_completion=False)

DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS = {
    "compilation": {
        "C": ["gcc", "--version"],
        "C++": ["g++", "--version"],
        "C#": ["dotnet", "--info"],
        "Java": ["javac", "-version"],
        "Rust": ["rustc", "--version"],
        "Go": ["go", "version"],
    },
    "runtime": {
        "C#": ["dotnet", "--version"],
        "Java": ["java", "-version"],
        "Go": ["go", "version"],
        "Node.js": ["node", "--version"],
        "Python": ["python", "--version"],
        "Ruby": ["ruby", "--version"],
    },
    "tools": {
        "git": ["git", "--version"],
        "Gradle": ["gradle", "-version"],
        "Docker": ["docker", "--version"],
    },
}

COMPILATION_BENCHMARK_COMMANDS = {
    "C": ["gcc", "-o", "build_artifacts/hello_world_c", "c/hello_world.c"],
    "C++": ["g++", "-o", "build_artifacts/hello_world_cpp", "cpp/hello_world.cpp"],
    "C#": ["dotnet", "build", "-o", "build_artifacts", "csharp/hello_world.csproj"],
    "Java": ["javac", "-d", "build_artifacts", "java/hello_world.java"],
    "Rust": ["rustc", "-o", "build_artifacts/hello_world", "rust/hello_world.rs"],
    "Go": ["go", "build", "-o", "build_artifacts/hello_world_go", "go/hello_world.go"],
}


def check_environment(cmd: list[str]) -> str:
    try:
        subprocess.run(cmd, env=os.environ,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "✅"
    except FileNotFoundError:
        return "❌"


def check_environments(env_type: str, table: Table):
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), transient=True) as progress:
        task = progress.add_task(f"[green]Checking {env_type}...", total=len(
            DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type]))
        for _, (env, cmd) in enumerate(DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type].items(), start=1):
            status = check_environment(cmd)
            table.add_row(env, status)
            progress.update(task, advance=1, description=f"[green]Checking {
                            env_type}: {env}")


@app.command()
def doctor():
    print("[bold purple]DevBench Doctor[/bold purple]")
    print(f"[purple]DevBench Version v{__version__}[/purple]\n")

    for env_type in DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS:
        table = Table(title=f"\n{env_type.capitalize()
                                 } Environments", title_justify="left")
        table.add_column("Environment")
        table.add_column("Status")
        check_environments(env_type, table)
        print(table)


def clean_build_environment():
    build_artifacts_path = './samples/build_artifacts'
    if os.path.exists(build_artifacts_path):
        for file in os.listdir(build_artifacts_path):
            file_path = os.path.join(build_artifacts_path, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


@app.command()
def compile(iterations: int = 10, warmup: int = 3):

    languages = list(COMPILATION_BENCHMARK_COMMANDS.keys())

    app = SelectionListApp(options=languages,
                           title="Choose a Language to Benchmark")
    app.run()

    selected_languages = app.get_selected()

    table = Table(title="Compilation Benchmark", title_justify="left")
    table.add_column("Language")
    table.add_column("Average Time (s)")
    table.add_column("Iterations")
    table.add_column("Minimum Time (s)")
    table.add_column("Maximum Time (s)")
    table.add_column("Standard Deviation")
    table.add_column("Variance")

    clean_build_environment()

    with Progress(TextColumn(text_format="[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), transient=True) as progress:
        task = progress.add_task(
            f"[green]Compiling", total=(len(selected_languages) * (iterations + warmup)))
        for language in selected_languages:
            for _ in range(warmup):
                subprocess.run(COMPILATION_BENCHMARK_COMMANDS[language], env=os.environ,
                               cwd="./samples", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                clean_build_environment()
                progress.update(task, advance=1,
                                description=f"[green]Compiling {language} - Warmup {_ + 1}/{warmup}")

            times = []
            for _ in range(iterations):
                start = time.perf_counter_ns()
                subprocess.run(COMPILATION_BENCHMARK_COMMANDS[language], env=os.environ,
                               cwd="./samples", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                end = time.perf_counter_ns()
                times.append((end - start) / 1e9)
                clean_build_environment()
                progress.update(task, advance=1,
                                description=f"[green]Compiling {language} - Iteration {_ + 1}/{iterations}")

            table.add_row(language,
                          f"{sum(times) / len(times):.6f}",
                          str(iterations),
                          f"{min(times):.6f}"
                          f"{max(times):.6f}",
                          f"{statistics.stdev(times):.6f}",
                          f"{statistics.variance(times):.6f}")

    print(table)


@ app.command()
def runtime(language: Optional[str] = None, test: Optional[str] = None, iterations: Optional[str] = None):
    typer.echo("Runtime Benchmark")


@ app.command()
def tools(tool: Optional[str] = None, iterations: Optional[str] = None):
    typer.echo("Tool Benchmark")


@ app.command()
def all(iterations: Optional[str] = None):
    typer.echo("Run All Benchmarks")


def version_callback(value: bool):
    if value:
        f = Figlet(font="slant")
        print(f.renderText("DevBench"))
        print(f"[purple]Version {__version__}[purple]")
        raise typer.Exit()


@ app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    pass


if __name__ == "__main__":
    app()
