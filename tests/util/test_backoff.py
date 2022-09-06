from http import HTTPStatus

import backoff
import requests
from requests import Response


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def get_url(url) -> Response:
    return requests.get(url)


def test_get_rul():
    response: Response = get_url("http://google.com")

    assert response.status_code == HTTPStatus.OK
