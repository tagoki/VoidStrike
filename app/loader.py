import os
from typing import List


def load_prompts(file_path: str = "prompts.txt") -> List[str]:
    """
    Считывает файл с тестовыми векторами (prompts.txt).
    Промпты разделяются строкой '----'.
    Пустые блоки игнорируются.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        return []

    # Разделяем по маркеру '----' на отдельной строке
    raw_prompts = content.split("----")
    prompts = [p.strip() for p in raw_prompts if p.strip()]
    return prompts
