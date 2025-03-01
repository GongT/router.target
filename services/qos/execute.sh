#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

### https://serverfault.com/questions/82751
### https://pastebin.com/f35557446

IFNAME=ppp0
MAX_MBPS=50

tc() {
   echo "+ tc $*" >&2
   /usr/sbin/tc "$@"
}

tc qdisc del dev "${IFNAME}" root 2>/dev/null
tc qdisc add dev "${IFNAME}" root handle 1: htb default 30 r2q 500

tc class add dev "${IFNAME}" parent 1: classid 1:1 htb rate "${MAX_MBPS}mbps" ceil "${MAX_MBPS}mbps"

up_c1=(htb
   rate "${MAX_MBPS}mbit"
   ceil "${MAX_MBPS}mbit"
   prio 1
)
up_c2=(htb
   rate $((8 * MAX_MBPS / 10))mbit
   ceil "${MAX_MBPS}mbit"
   burst 10mbit
   prio 2
)
up_c3=(htb
   rate $((4 * MAX_MBPS / 10))mbit
   ceil "${MAX_MBPS}mbit"
   burst 5mbit
   prio 3
)

tc class add dev "${IFNAME}" parent 1:1 classid 1:10 "${up_c1[@]}"
tc class add dev "${IFNAME}" parent 1:1 classid 1:20 "${up_c2[@]}"
tc class add dev "${IFNAME}" parent 1:1 classid 1:30 "${up_c3[@]}"

u32_up1() {
   tc filter add dev "${IFNAME}" protocol ip parent 1:0 prio 1 u32 "$@"
}
u32_up2() {
   tc filter add dev "${IFNAME}" protocol ip parent 1:0 prio 2 u32 "$@"
}

# ssh and icmp - very high up and down
u32_up1 match ip tos 0x10 0xff flowid 1:10
u32_up1 match ip protocol 1 0xff flowid 1:10

# ack - fairly high (but it does use a lot of bw)
u32_up1 \
   match ip protocol 6 0xff \
   match u8 0x05 0x0f at 0 \
   match u16 0x0000 0xffc0 at 2 \
   match u8 0x10 0xff at 33 \
   flowid 1:10

# desktop machines
u32_up1 match u8 0 0 at -14 match ether src 6C:B3:11:65:A9:BE flowid 1:20
u32_up1 match u8 0 0 at -14 match ether src A8:A1:59:DB:B4:72 flowid 1:20
u32_up1 match u8 0 0 at -14 match ether src 00:ca:e0:95:bd:13 flowid 1:20

u32_up2 match ip src 10.0.2.0/24 flowid 1:10

# network devices
u32_up2 match ip src 10.0.0.0/24 flowid 1:20

# server
u32_up2 match u8 0 0 at -14 match ether src 4A:E1:A2:4E:D5:6E flowid 1:30
u32_up2 match u8 0 0 at -14 match ether src f0:dd:7a:90:46:b8 flowid 1:30
u32_up2 match u8 0 0 at -14 match ether src f0:dd:7a:90:46:b6 flowid 1:30

u32_up1 match ip src 10.0.1.0/24 flowid 1:30

echo "Complete."
