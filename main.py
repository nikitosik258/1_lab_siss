# ПРАКТИЧЕСКОЕ ЗАНЯТИЕ № 1
# Разработка REST API для AI-сервиса на FastAPI

import logging
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, status

from model import calculate_risk
from schemas import (
    FarmRequest,
    HealthResponse,
    ModelInfoResponse,
    PredictionResponse,
)
from services import (
    ALLOWED_REGIONS,
    get_recommendation,
    get_risk_level,
    is_region_allowed,
)
from storage import predictions


# ------------------------------------------------------------
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# FASTAPI-ПРИЛОЖЕНИЕ
# ------------------------------------------------------------

app = FastAPI(
    title="Agro Scoring API",
    description=(
        "REST API для оценки риска "
        "сельскохозяйственных предприятий."
    ),
    version="1.0.0"
)


# ------------------------------------------------------------
# КОНСТАНТЫ МОДЕЛИ
# ------------------------------------------------------------

MODEL_NAME = "agro-risk-model"
MODEL_VERSION = "1.0"
MODEL_TYPE = "risk-scoring"

# Имитируем состояние модели.
# Если установить False, /predict будет возвращать HTTP 503.
MODEL_READY = True


# ------------------------------------------------------------
# MIDDLEWARE
# Измеряем время обработки каждого HTTP-запроса.
# ------------------------------------------------------------

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """
    Добавляет в HTTP-ответ заголовок X-Process-Time
    со временем обработки запроса.
    """

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    response.headers["X-Process-Time"] = str(
        round(process_time, 6)
    )

    return response


# ------------------------------------------------------------
# GET /health
# ------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния API",
    description=(
        "Используется для проверки того, "
        "что REST API запущен и отвечает."
    )
)
def health():
    """Проверка работоспособности API."""

    return {
        "status": "ok"
    }


# ------------------------------------------------------------
# GET /model-info
# ------------------------------------------------------------

@app.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Информация о модели",
    description=(
        "Возвращает название, версию, тип "
        "и текущее состояние модели."
    )
)
def model_info():
    """Возвращает информацию об используемой ML-модели."""

    model_status = (
        "ready"
        if MODEL_READY
        else "unavailable"
    )

    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_type": MODEL_TYPE,
        "status": model_status
    }


# ------------------------------------------------------------
# POST /predict
# ------------------------------------------------------------

@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Оценить риск хозяйства",
    description=(
        "Принимает характеристики хозяйства, "
        "выполняет валидацию, инференс модели "
        "и возвращает оценку риска."
    )
)
def predict(request: FarmRequest):
    """Основной endpoint сервиса."""

    # 1. Проверяем состояние ML-модели
    if not MODEL_READY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is temporarily unavailable"
        )

    # 2. Бизнес-валидация региона
    if not is_region_allowed(request.region):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown region: {request.region}. "
                f"Allowed regions: "
                f"{sorted(ALLOWED_REGIONS)}"
            )
        )

    # 3. Логирование входящего запроса
    logger.info(
        "Prediction request received | farm_id=%s",
        request.farm_id
    )

    # 4. Инференс
    score = calculate_risk(request)

    # 5. Постпроцессинг
    level = get_risk_level(score)
    recommendation = get_recommendation(level)

    # 6. Создаем уникальный ID запроса
    request_id = str(uuid.uuid4())

    # 7. Формируем результат
    result = {
        "request_id": request_id,
        "farm_id": request.farm_id,
        "risk_score": score,
        "risk_level": level,
        "recommendation": recommendation,
        "model_version": MODEL_VERSION
    }

    # 8. Сохраняем результат
    predictions[request_id] = result

    # 9. Логирование результата
    logger.info(
        "Prediction completed | "
        "request_id=%s | "
        "farm_id=%s | "
        "risk_score=%s | "
        "risk_level=%s",
        request_id,
        request.farm_id,
        score,
        level
    )

    # 10. Возвращаем HTTP-ответ
    return result


# ------------------------------------------------------------
# GET /predictions
# Этот endpoint расположен ДО /predictions/{request_id}.
# ------------------------------------------------------------

@app.get(
    "/predictions",
    response_model=List[PredictionResponse],
    summary="Получить список прогнозов",
    description=(
        "Возвращает список выполненных прогнозов. "
        "Поддерживает ограничение количества результатов "
        "и фильтрацию по уровню риска."
    )
)
def get_predictions(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Максимальное количество результатов"
    ),
    risk_level: Optional[str] = Query(
        default=None,
        description=(
            "Фильтр по категории риска: "
            "low, medium или high"
        )
    )
):
    """Получение списка прогнозов."""

    values = list(predictions.values())

    allowed_levels = {
        "low",
        "medium",
        "high"
    }

    if risk_level is not None:
        if risk_level not in allowed_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "risk_level must be "
                    "'low', 'medium' or 'high'"
                )
            )

        values = [
            item
            for item in values
            if item["risk_level"] == risk_level
        ]

    return values[:limit]


# ------------------------------------------------------------
# GET /predictions/{request_id}
# ------------------------------------------------------------

@app.get(
    "/predictions/{request_id}",
    response_model=PredictionResponse,
    summary="Получить прогноз по request_id",
    description=(
        "Возвращает сохраненный прогноз "
        "по его уникальному идентификатору."
    )
)
def get_prediction(request_id: str):
    """Получение одного прогноза по request_id."""

    if request_id not in predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    return predictions[request_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
