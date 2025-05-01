systemd_add_unit ipchange-monitor.service
systemd_add_unit ipchange@.service
systemd_add_unit ipchange.service
systemd_add_unit ipsets-generate.service ipsets-generation/ipsets-generate.service

#### copy ipsets shape file to firewalld
cp -nvr ./firewalld-template-ipsets/. /etc/firewalld/ipsets

CHANGED=0
LST=$(firewall-offline-cmd --get-ipsets)
for TYPE in wan localhost lan; do
	for INET in 4 6; do
		NAME="${TYPE}-${INET}"
		if ! echo "$LST" | grep -q "$NAME"; then
			CHANGED=1
		fi
	done
done

if [[ $CHANGED -eq 1 ]]; then
	echo "restarting firewalld.service"
	systemctl --no-block restart firewalld.service
fi
