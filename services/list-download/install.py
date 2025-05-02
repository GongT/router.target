from router.target import (
    systemd_add_unit,
)

systemd_add_unit("list-download.service")
systemd_add_unit("list-download.timer")
