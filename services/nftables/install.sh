echo "### This file is replaced by router.target
### use nftables@xxx.service instead

" >/etc/sysconfig/nftables.conf

mkdir -p "${AppDataDir}/firewall"
if ! [[ -e "${AppDataDir}/firewall/main.nft" ]]; then
	touch "${AppDataDir}/firewall/main.nft"
fi

find /etc/nftables -name '*.nft' -print0 | xargs -t -0 -n1 sed -Ei 's/^[^#]*flush .+$/## \0 # no flush command/g'

systemd_add_unit nftables@.service
systemd_enable_unit nftables@router.service
