import os
from pathlib import Path

import requests

from . import logger


def download_file(url: str, output_path: str | Path, disable_proxy=False, check=True):
    """
    Download a file from the given URL to the specified output path.
    """

    temp_output = Path(output_path).with_suffix(".downloading")
    logger.dim(f"downloading {url} to {temp_output.as_posix()}")

    if disable_proxy:
        logger.dim("[proxy] disabled")
        proxies = {"http": "", "https": ""}
    else:
        GOT_PROXY = get_proxy()
        logger.dim(f"[proxy] server = {GOT_PROXY}")
        if GOT_PROXY:
            proxies = {"http": GOT_PROXY, "https": GOT_PROXY}
        else:
            proxies = {}

    headers = {"user-agent": "GongT (https://github.com/gongt/router.target)"}

    try:
        response = requests.get(url, stream=True, proxies=proxies, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        with open(temp_output, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        temp_output.rename(output_path)
        logger.dim(f"download complete")
    except requests.RequestException as e:
        if check:
            logger.die(f'failed to download file from "{url}": {e}')
        else:
            logger.error(f"failed to download: {e}")


__proxy = None


def get_proxy():
    global __proxy
    if __proxy is None:
        __proxy = __get_proxy()
        if not __proxy:
            __proxy = ""

    return __proxy


def __get_proxy():
    """
    Get the proxy setting from environment variables.
    """
    proxy = os.environ.get("PROXY", None)
    if proxy:
        return proxy
    https_proxy = os.environ.get("https_proxy", None)
    if https_proxy:
        return https_proxy
    http_proxy = os.environ.get("http_proxy", None)
    if http_proxy:
        return http_proxy

    from . import subprocess

    PROXY = subprocess.execute_output(
        "env", "-i", "bash", "--login", "-c", "echo $PROXY", ignore=True
    )
    if not PROXY:
        return None
