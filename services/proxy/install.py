import re

from router.target import (
    DIST_ROOT,
    extract_archive,
    git_clone_or_pull,
    github_api,
    github_download_release,
    is_install,
    logger,
    systemd_add_unit,
)

g = github_api()
print(g.get_repo("MetaCubeX/Yacd-meta").get_releases().get_page(0)[0].zipball_url)

# 安装sing-box
distBin = DIST_ROOT / "sing-box/sing-box"
if not distBin.exists() or is_install:
    zipfile = github_download_release(
        "SagerNet/sing-box", re.compile(r"^sing-box-.+-linux-amd64\..+$")
    )

    try:
        extract_archive(zipfile, DIST_ROOT / "sing-box", stripe_components=1)
    except Exception as e:
        if not distBin.exists():
            raise
        logger.error(f"Failed to extract sing-box: {e}")

# 安装webui
webui = DIST_ROOT / "sing-box/webui"
if not webui.exists() or is_install:
    git_clone_or_pull("https://github.com/MetaCubeX/Yacd-meta.git", "gh-pages", webui)


systemd_add_unit("proxy.service")
