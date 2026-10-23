import os
from typing import Optional


def append_result(
    model_name: str,
    prompt_id: int,
    iteration: int,
    total_iterations: int,
    status: str,
    prompt_input: str,
    output: Optional[str] = None,
    file_path: str = "result.txt",
) -> None:
    """
    Дозаписывает результат выполнения теста в файл отчета (TXT или MD).
    Формат определяется автоматически по расширению file_path (.md или .txt).
    """
    output_text = output if output is not None else ""
    is_markdown = file_path.lower().endswith(".md")

    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    if is_markdown:
        # Если файл еще не создан, формируем титульный заголовок Markdown-отчета
        file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0
        header = ""
        if not file_exists:
            header = (
                f"# VoidStrike Red Teaming Report\n\n"
                f"- **Target Model:** `{model_name}`\n"
                f"- **Date:** {os.path.basename(file_path).replace('result_', '').replace('.md', '')}\n\n"
                f"---\n\n"
            )

        # Выбираем бейдж статуса
        if status == "REFUSED":
            status_badge = "🛡️ **[REFUSED]**"
        elif status == "POTENTIAL BYPASS":
            status_badge = "⚠️ **[POTENTIAL BYPASS]**"
        else:
            status_badge = "❌ **[ERROR]**"

        record = (
            header
            + f"### Prompt #{prompt_id} | Iteration {iteration}/{total_iterations}\n\n"
            + f"- **Model:** `{model_name}`\n"
            + f"- **Status:** {status_badge}\n\n"
            + "#### Input:\n"
            + "```text\n"
            + f"{prompt_input}\n"
            + "```\n\n"
            + "#### Output:\n"
            + "```text\n"
            + f"{output_text}\n"
            + "```\n\n"
            + "---\n\n"
        )
    else:
        # Стандартный формат TXT
        record = (
            "========================================\n"
            f"Model Name: {model_name}\n"
            f"Prompt ID:  {prompt_id} | Iteration: {iteration}/{total_iterations}\n"
            f"Status:     {status}\n"
            f"Input:      {prompt_input}\n"
            f"Output:     {output_text}\n"
            "========================================\n"
        )

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(record)
