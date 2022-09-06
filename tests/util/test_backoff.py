import backoff

from httpx import Request


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException)
def get_url(url):
    return requests.get(url)
