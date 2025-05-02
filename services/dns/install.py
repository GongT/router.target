from router.target import (
    get_assets_path,
    read_filtered_file,
    systemd_add_unit,
    write_if_change,
)

# systemd_add_unit("dnscache.service", "cache/dnsmasq.service")


systemd_add_unit("dnsconvert.service", "convert/coredns.service")

config_file = read_filtered_file("dispatch/files/config-template")
write_if_change(get_assets_path("dispatch-config"), config_file)
systemd_add_unit("dnsdispatch.service", "dispatch/chinadns-ng.service")


systemd_add_unit("dnsproxy.service", "proxy/dns-proxy.service")
