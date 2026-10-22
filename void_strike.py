import os
import sys
import datetime
import json
import subprocess
import urllib.request
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.live import Live

from app.loader import load_prompts
from app.runner import run_tests

console = Console()


def get_ollama_models() -> List[str]:
    """
    Получает список локально доступных моделей Ollama.
    Сначала пытается через REST API ($OLLAMA_HOST/api/tags),
    в случае неудачи пробует через команду 'ollama list'.
    """
    base_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    # 1. Попытка через REST API
    try:
        req = urllib.request.Request(f"{base_host}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", []) if "name" in m]
            if models:
                return models
    except Exception:
        pass

    # 2. Fallback через subprocess 'ollama list'
    try:
        res = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        lines = [line.strip() for line in res.stdout.strip().splitlines()]
        models = []
        # Пропускаем заголовок (NAME ID SIZE MODIFIED)
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        if models:
            return models
    except Exception:
        pass

    return []


def read_key() -> str:
    """
    Считывает нажатие клавиши в терминале (поддержка Windows и Unix).
    Возвращает: 'UP', 'DOWN', 'ENTER' или строковое представление клавиши.
    """
    try:
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):  # Префикс спецклавиш в Windows
            arrow = msvcrt.getch()
            if arrow == b"H":
                return "UP"
            elif arrow == b"P":
                return "DOWN"
        elif ch == b"\r":
            return "ENTER"
        elif ch == b"\x03":
            raise KeyboardInterrupt
        return ch.decode(errors="ignore")
    except ImportError:
        # Для Unix-терминалов
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch1 = sys.stdin.read(1)
            if ch1 == "\x1b":
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == "[" and ch3 == "A":
                    return "UP"
                elif ch2 == "[" and ch3 == "B":
                    return "DOWN"
            elif ch1 in ("\r", "\n"):
                return "ENTER"
            elif ch1 == "\x03":
                raise KeyboardInterrupt
            return ch1
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def select_model_interactive(models: List[str]) -> str:
    """
    Интерактивное меню выбора модели стрелочками ВВЕРХ/ВНИЗ и клавишей ENTER.
    """
    if not models:
        return Prompt.ask(
            "Имя целевой модели (Ollama)",
            default="qwen2.5:3b",
        )

    current_idx = 0

    def render_menu(selected_idx: int) -> str:
        lines = ["[bold cyan]Выберите модель из списка (стрелочки ↑/↓, Enter для выбора):[/bold cyan]"]
        for idx, model in enumerate(models):
            if idx == selected_idx:
                lines.append(f"  [bold green]> ● {model}[/bold green]")
            else:
                lines.append(f"    ○ {model}")
        return "\n".join(lines)

    with Live(render_menu(current_idx), console=console, refresh_per_second=20, transient=True) as live:
        while True:
            live.update(render_menu(current_idx))
            try:
                key = read_key()
            except KeyboardInterrupt:
                console.print("\n[yellow]Отменено пользователем.[/yellow]")
                sys.exit(0)

            if key == "UP":
                current_idx = (current_idx - 1) % len(models)
            elif key == "DOWN":
                current_idx = (current_idx + 1) % len(models)
            elif key == "ENTER":
                break

    chosen_model = models[current_idx]
    console.print(f"Выбрана модель: [bold green]{chosen_model}[/bold green]")
    return chosen_model


def show_banner() -> None:
    banner_text = (
        "[bold cyan]Добро пожаловать в VoidStrike[/bold cyan]\n"
        "[dim]CLI-утилита для тестирования безопасности LLM (MVP V1)[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def show_menu() -> str:
    console.print("\n[bold]Главное меню:[/bold]")
    console.print("  [cyan][1][/cyan] — Начать проверку устойчивости")
    console.print("  [cyan][0][/cyan] — Выход")
    choice = Prompt.ask("\nВыберите действие", choices=["1", "0"], default="1")
    return choice


def configure_and_run() -> None:
    prompts = load_prompts("prompts.txt")
    if not prompts:
        console.print(
            "\n[bold yellow]Внимание:[/] Файл [bold]prompts.txt[/bold] пуст или не содержит тестовых векторов."
        )
        console.print(
            "[dim]Добавьте тестовые промпты в prompts.txt, разделяя их строкой '----'.[/dim]\n"
        )
        return

    console.print("\n[bold cyan]=== Параметры запуска ===[/bold cyan]")

    # Получаем локальные модели из Ollama и даем выбрать стрелочками
    available_models = get_ollama_models()
    if available_models:
        model_name = select_model_interactive(available_models)
    else:
        model_name = Prompt.ask(
            "Имя целевой модели (Ollama)",
            default="qwen2.5:3b",
        )

    iterations = IntPrompt.ask(
        "Количество итераций (N)",
        default=3,
    )

    temperature = FloatPrompt.ask(
        "Температура генерации (temperature)",
        default=0.7,
    )

    # Генерация имени уникального файла отчета со временем запуска в папке reports/
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, f"result_{timestamp}.txt")

    run_tests(
        prompts=prompts,
        model_name=model_name,
        iterations=iterations,
        temperature=temperature,
        report_file=report_file,
        console=console,
    )

    console.print(
        f"\n[bold green]Тестирование завершено![/] Результаты сохранены в [bold]{report_file}[/bold]\n"
    )


def main() -> None:
    show_banner()
    while True:
        choice = show_menu()
        if choice == "1":
            configure_and_run()
        elif choice == "0":
            console.print("\n[bold cyan]Выход из программы. До свидания![/bold cyan]")
            sys.exit(0)


if __name__ == "__main__":
    main()
