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
    Дозаписывает результат выполнения теста в файл отчета в соответствии со спецификацией:
    ========================================
    Model Name: [имя модели]
    Prompt ID:  [номер промпта] | Iteration: [текущая итерация]/[N]
    Status:     [REFUSED / POTENTIAL BYPASS / ERROR]
    Input:      [запрос из prompts.txt]
    Output:     [ответ модели]
    ========================================
    """
    output_text = output if output is not None else ""
    record = (
        "========================================\n"
        f"Model Name: {model_name}\n"
        f"Prompt ID:  {prompt_id} | Iteration: {iteration}/{total_iterations}\n"
        f"Status:     {status}\n"
        f"Input:      {prompt_input}\n"
        f"Output:     {output_text}\n"
        "========================================\n"
    )

    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(record)
