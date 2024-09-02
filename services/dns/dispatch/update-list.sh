#!/usr/bin/env bash

set -Eeuo pipefail

cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

wget 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf' -O auto/china-list.apple.conf
# wget 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf' -O auto/china-list.google.conf
wget 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf' -O auto/china-list.cdn.conf
wget 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/bogus-nxdomain.china.conf' -O auto/china-list.bogus-nxdomain.conf

mapfile -t FILES < <(find auto -type f)
for F in "${FILES[@]}"; do
	sed -i 's/114\.114\.114\.114/::1#8806/g' "$F"
done

sites.default-oversea.conf
