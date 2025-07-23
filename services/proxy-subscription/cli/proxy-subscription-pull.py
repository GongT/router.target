from pathlib import Path
from sys import argv
from urllib.parse import urlparse

from router.target import constants, http_client, logger, proxy

if len(argv) != 3:
    logger.die("Usage: proxy-subscription-pull.py <name> <subscription_url>")

name = argv[1]
subscription_url = urlparse(argv[2])

if not subscription_url.scheme or not subscription_url.netloc:
    logger.die("Invalid subscription URL format. Please provide a valid URL.")

print(f"Name: {name}")
print(f"Subscription URL: {subscription_url.geturl()}")

output_file = (
    Path(constants.ROUTER_DATA_PATH)
    .joinpath("proxy/custom-subscriptions")
    .joinpath(f"{name}.txt")
)
output_file.parent.mkdir(parents=True, exist_ok=True)

print("Pulling subscription...")
http_client.download_file(url=subscription_url.geturl(), output_path=output_file)

proxy.tools.fix_base64_padding(output_file)

logger.success(f"Subscription pulled successfully to {output_file.as_posix()}")
