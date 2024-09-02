#!/usr/bin/env bash

set -Eeuo pipefail

cd config
sed -e '/^#/d' tlds-alpha-by-domain.txt | awk '{print "address=/"$1"/::\nlocal=/"$1"/"}' > tlds.conf
# sed -e '/^#/d' tlds-alpha-by-domain.txt | awk '{print "address=/"$1"/::\nserver=/"$1"/::1#53"}' > tlds.conf
