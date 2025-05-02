from router.target import systemd_add_unit


systemd_add_unit("ddns.timer")
systemd_add_unit("ddns.service")
