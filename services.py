# Разрешенные регионы.
# Это пример бизнес-справочника.
ALLOWED_REGIONS = {
    "Krasnodar",
    "Rostov",
    "Stavropol"
}


def is_region_allowed(region: str) -> bool:
    """Проверяет бизнес-правило допустимого региона."""
    return region in ALLOWED_REGIONS


def get_risk_level(score: float) -> str:
    """
    Преобразует score в категорию риска.
    """

    if score < 0.3:
        return "low"

    if score < 0.7:
        return "medium"

    return "high"


def get_recommendation(level: str) -> str:
    """
    Возвращает рекомендацию в зависимости от категории риска.
    """

    if level == "low":
        return "Стандартное рассмотрение"

    if level == "medium":
        return "Требуется дополнительная проверка"

    return "Высокий риск. Требуется ручное рассмотрение"
