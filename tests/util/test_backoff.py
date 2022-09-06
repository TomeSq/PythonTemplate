import logging

import backoff
import pytest
import starlette.status as status
from fastapi import FastAPI
from fastapi.responses import Response as fastapi_responses
from httpx import AsyncClient, HTTPStatusError, Response
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
def fatal_code(e):
    return 400 <= e.response.status_code < 500


@backoff.on_exception(
    backoff.expo,
    # リトライ例外
    HTTPStatusError,
    # 諦めるまでに経過する時間
    #    max_time=30,
    # リトライ回数
    max_tries=3,
    # リトライ条件
    giveup=fatal_code,
    # ロガー
    logger=logger,
)
async def get_url(client: AsyncClient, url: str) -> Response:
    response = await client.get(url=url)
    response.raise_for_status()
    return response


#############################################

#############################################
# テストコード
@pytest.mark.asyncio
async def test_get_rul(test_client_async):
    response: Response = await get_url(client=test_client_async, url="/sucess")

    assert response.status_code == status.HTTP_200_OK


def retry_log_count(lc: LogCapture) -> int:
    """
    リトライ回数のカウント
    """
    retry_logs = [s for s in lc.records if "Backing off" in str(s.msg) or "Giving up" in str(s.msg)]
    return len(retry_logs)


@pytest.mark.asyncio
async def test_get_rul_faile(test_client_async):
    # Act
    with LogCapture(level=logging.INFO) as lc:
        try:
            await get_url(client=test_client_async, url="/faile")
        except HTTPStatusError as e:
            logger.error(e)
            # Asset
            assert e.response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            retry_count = retry_log_count(lc)
            assert retry_count == 3


#############################################
