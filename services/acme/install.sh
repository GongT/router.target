P=$(pwd)

if pushd /data/DevelopmentRoot/github.com/acmesh-official/acme.sh &>/dev/null; then
	systemd_add_unit "$P/acme-renew.timer"
	systemd_add_unit "$P/acme-renew.service"

	./acme.sh --install \
		--home "$ROOT_DIR/dist/acme.sh" \
		--config-home "${AppDataDir}/ACME" \
		--cert-home "${AppDataDir}/ACME/certs" \
		--accountkey "${AppDataDir}/ACME/account.key" \
		--accountconf "${AppDataDir}/ACME/account.conf" \
		--useragent "router.target/acme(https://github.com/gongt/router.target)" \
		--nocron --no-profile
	popd &>/dev/null
else
	echo "missing acme.sh client source code." >&2
fi
