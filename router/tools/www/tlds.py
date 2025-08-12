SRC_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
from ..._internal.constants import CACHE_ROOT
from ..._internal.http_client import download_file
from ..._internal import logger


def tlds():
    cache_file = CACHE_ROOT / "tlds.txt"
    if not cache_file.exists():
        logger.dim("Downloading TLD list...")
        download_file(SRC_URL, cache_file)

    r = []
    for line in cache_file.read_text("utf8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        r.append(line)
    return r
