import datetime
import logging
import os
from typing import Tuple

import backoff
import pytest
import starlette.status as status
from fastapi import FastAPI
from fastapi.responses import Response as fastapi_responses
from httpx import AsyncClient, Response
from pytest import MonkeyPatch
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
    print("●aceess")
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


def get_max_tries() -> int:
    """最大リトライ回数の取得"""
    return int(os.environ.get("MAX_TRIES", 5))


def get_expo_base() -> float:
    """指数関数 base"""
    return float(os.environ.get("EXPO_BASE", 1.74))


def get_expo_factor() -> float:
    """指数関数 因子"""
    return float(os.environ.get("EXPO_FACTOR", 5))


@backoff.on_predicate(
    # 指数関数リトライ
    backoff.expo,
    # リトライする条件
    lambda x: retry_check(x),
    # backoff.expoの指数関数定数
    # 次の計算式でライブラリ内で次回周期を計算(factor * base ** n)
    base=get_expo_base,
    factor=get_expo_factor,
    # 何回でやめるか(初回も含むので+1する)
    max_tries=get_max_tries() + 1,
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

    for i, log in enumerate(retry_logs):
        log_datetime = datetime.datetime.fromtimestamp(log.created) + datetime.timedelta(
            milliseconds=log.msecs
        )

        # 前回との差分を求める
        time_diff: datetime.timedelta = datetime.timedelta(0)
        if 0 < i:
            old_log = retry_logs[i - 1]
            log_old_datetime = datetime.datetime.fromtimestamp(
                old_log.created
            ) + datetime.timedelta(milliseconds=old_log.msecs)
            time_diff = log_datetime - log_old_datetime

        str_datetime = log_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{str_datetime}\t{log.msg} (+{str(time_diff.total_seconds())} sec)")

    return len(retry_logs)


async def get_response_retrycount(client: AsyncClient, url: str) -> Tuple[Response, int]:
    # Act
    with LogCapture(level=logging.INFO) as lc:
        response: Response = await get_url(client=client, url=url)

        return (response, retry_log_count(lc))


@pytest.mark.asyncio
async def test_タイムアウト確認(test_client_async):
    # Act
    await get_url(client=test_client_async, url="/faile")


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


@pytest.mark.asyncio
async def test_失敗した場合はリトライデフォルト2回行われていること(test_client_async: AsyncClient, monkeypatch: MonkeyPatch):
    # Arrage
    monkeypatch.setenv("MAX_TRIES", "2")

    # Act
    response, retry_count = await get_response_retrycount(client=test_client_async, url="/faile")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert retry_count == 2


#############################################

#############################################
