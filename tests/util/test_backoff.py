import logging
from typing import Tuple

import backoff
import pytest
import starlette.status as status
from fastapi import FastAPI
from fastapi.responses import Response as fastapi_responses
from httpx import AsyncClient, Response
from testfixtures.logcapture import LogCapture

logger = logging.getLogger(__name__)

#############################################
# fastapi
app = FastAPI()


@app.get("/sucess")
def sucess():
    return "Hello, world!"


@app.get("/faile/{count}")
def faile_count(count):
    return fastapi_responses(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/faile")
def faile():
    return fastapi_responses(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


#############################################

#############################################
# テスト準備
@pytest.fixture
async def test_client_async():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


#############################################


#############################################
# ロジック
def retry_check(e: Response):
    return 500 <= e.status_code < 600


#
@backoff.on_predicate(
    # フィボナッチ数列によるリトライ
    # backoff.fibo,
    # フィボナッチ数列に待ち内で使用するジェネレーター初期化値
    # max_value=13,
    backoff.expo,
    # リトライする条件
    lambda x: retry_check(x),
    # 諦めるまでに経過する時間
    #    max_time=30,
    # リトライ回数
    max_tries=5,
    # ロガー
    logger=logger,
)
async def get_url(client: AsyncClient, url: str) -> Response:
    return await client.get(url=url)


#############################################

#############################################
# テストコード
def retry_log_count(lc: LogCapture) -> int:
    """
    リトライ回数のカウント
    """
    retry_logs = [s for s in lc.records if "Backing off" in str(s.msg) or "Giving up" in str(s.msg)]

    return len(retry_logs)


async def get_response_retrycount(client: AsyncClient, url: str) -> Tuple[Response, int]:
    # Act
    with LogCapture(level=logging.INFO) as lc:
        response: Response = await get_url(client=client, url=url)

        return (response, retry_log_count(lc))


@pytest.mark.asyncio
async def test_成功時は即時に抜けること(test_client_async):
    # Act
    response, retry_count = await get_response_retrycount(client=test_client_async, url="/sucess")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert retry_count == 0


@pytest.mark.asyncio
async def test_失敗した場合はリトライデフォルト5回行われていること(test_client_async):
    # Act
    response, retry_count = await get_response_retrycount(client=test_client_async, url="/faile")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert retry_count == 5


#############################################
