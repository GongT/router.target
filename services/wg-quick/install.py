from router.target import systemd_add_unit, systemd_override

systemd_override("wg-quick@.service", "create-dhcp/wg-quick-override.service")
