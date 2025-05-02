from router.target import systemd_add_unit

systemd_add_unit("tlds-download.service")
systemd_add_unit("tlds-download.timer")
