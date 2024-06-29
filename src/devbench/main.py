import typer
from typing import Optional
import importlib.metadata
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, TaskID
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

# region Doctor Command


DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS = {
    "compilation": {
        "C (gcc)": ["gcc", "--version"],
        "C++ (g++)": ["g++", "--version"],
        "C# (dotnet)": ["dotnet", "--info"],
        "Java (javac)": ["javac", "-version"],
        "Rust (rustc)": ["rustc", "--version"],
        "Go (go)": ["go", "version"],
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


def _check_env_command(cmd: list[str]):
    subprocess.run(cmd, env=os.environ, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)


def _check_env(cmd: list[str]) -> str:
    try:
        _check_env_command(cmd)
        return "✅"
    except FileNotFoundError:
        return "❌"


def _add_check_env_result_to_table(table: Table, env: str, status: str):
    table.add_row(env, status)


def _check_envs(env_type: str, table: Table):
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), transient=True) as progress:
        task = progress.add_task(f"[green]Checking {env_type}...", total=len(
            DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type]))
        for _, (env, cmd) in enumerate(DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS[env_type].items(), start=1):
            status = _check_env(cmd)
            _add_check_env_result_to_table(table, env, status)
            progress.update(task, advance=1, description=f"[green]Checking {
                            env_type}: {env}")


def _run_envs_check():
    for env_type in DOCTOR_COMMAND_ENVIRONMENT_CHECK_COMMANDS:
        table = Table(title=f"\n{env_type.capitalize()
                                 } Environments", title_justify="left")
        table.add_column("Environment")
        table.add_column("Status")
        _check_envs(env_type, table)
        print(table)


@ app.command()
def doctor():
    print("[bold purple]DevBench Doctor[/bold purple]")
    print(f"[purple]DevBench Version v{__version__}[/purple]\n")

    _run_envs_check()

# endregion

# region Compilation Benchmark Command


COMPILATION_BENCHMARK_COMMANDS = {
    "C (gcc)": ["gcc", "-o", "build_artifacts/hello_world_c", "c/hello_world.c"],
    "C++ (g++)": ["g++", "-o", "build_artifacts/hello_world_cpp", "cpp/hello_world.cpp"],
    "C# (dotnet)": ["dotnet", "build", "-o", "build_artifacts", "csharp/hello_world.csproj"],
    "Java (javac)": ["javac", "-d", "build_artifacts", "java/hello_world.java"],
    "Rust (rustc)": ["rustc", "-o", "build_artifacts/hello_world", "rust/hello_world.rs"],
    "Go (gc)": ["go", "build", "-o", "build_artifacts/hello_world_go", "go/hello_world.go"],
}


def _clean_build_artifacts():
    build_artifacts_path = './samples/build_artifacts'
    if os.path.exists(build_artifacts_path):
        for file in os.listdir(build_artifacts_path):
            file_path = os.path.join(build_artifacts_path, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def _compile_benchmark_command(command: list[str]):
    subprocess.run(command, env=os.environ,
                   cwd="./samples", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _measure_benchmark_time(command: list[str]):
    start = time.perf_counter_ns()
    _compile_benchmark_command(command)
    end = time.perf_counter_ns()
    return (end - start) / 1e9


def _add_compile_benchmark_result_to_table(table: Table, language: str, warmup: int, iterations: int, times: list[float]):
    table.add_row(language,
                  f"({warmup}) + {iterations}",
                  f"{sum(times) / len(times):.6f}",
                  f"{min(times):.6f}",
                  f"{max(times):.6f}",
                  f"{statistics.stdev(times):.6f}",
                  f"{statistics.variance(times):.6f}")


def _compile_benchmark_language(language: str, warmup: int, iterations: int, table: Table, progress: Progress, task: TaskID):
    times = []
    for _ in range(warmup):
        _compile_benchmark_command(COMPILATION_BENCHMARK_COMMANDS[language])
        _clean_build_artifacts()
        progress.update(task, advance=1, description=f"[green]Compiling {
                        language} (Warmup) {_ + 1}/{warmup}")

    for _ in range(iterations):
        times.append(_measure_benchmark_time(
            COMPILATION_BENCHMARK_COMMANDS[language]))
        _clean_build_artifacts()
        progress.update(task, advance=1, description=f"[green]Compiling {
                        language} (Iteration) {_ + 1}/{iterations}")

    _add_compile_benchmark_result_to_table(
        table, language, warmup, iterations, times)


def _compile_benchmark_languages(languages: list[str], warmup: int, iterations: int):

    table = Table(
        title="[bold purple]DevBench Compilation Benchmark[/bold purple]", title_justify="left")
    table.add_column("Language (Compiler)")
    table.add_column("(Warmup) + Iterations")
    table.add_column("Average Time (s)")
    table.add_column("Minimum Time (s)")
    table.add_column("Maximum Time (s)")
    table.add_column("Standard Deviation")
    table.add_column("Variance")

    _clean_build_artifacts()

    with Progress(TextColumn(text_format="[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), transient=True) as progress:
        task = progress.add_task(
            f"[green]Compiling", total=(len(languages) * (iterations + warmup)))
        for language in languages:
            _compile_benchmark_language(
                language, warmup, iterations, table, progress, task)

    print(table)


def _query_languages_to_compile_benchmark():
    languages = list(COMPILATION_BENCHMARK_COMMANDS.keys())

    app = SelectionListApp(options=languages,
                           title="Choose a Language to Benchmark")
    app.run()

    return app.get_selected()


def run_compile_benchmarks(iterations: int, warmup: int):
    languages = _query_languages_to_compile_benchmark()
    _compile_benchmark_languages(languages, warmup, iterations)


@ app.command()
def compile(iterations: int = 15, warmup: int = 3):
    run_compile_benchmarks(iterations, warmup)

# endregion


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
