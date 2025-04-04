# https://github.com/miniupnp/miniupnp
# cd miniupnp/miniupnpd

./configure --ipv6 --leasefile --vendorcfg --pcp-peer --portinuse --firewall=nftables --disable-fork --systemd
make -j

_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
PREFIX=$(realpath "${_DIR}/../../../dist/miniupnpd")
export PREFIX
make install

echo "installed to $PREFIX"
