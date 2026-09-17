#!/usr/bin/env bash

set -Eeuo pipefail

LIBEXEC_ROOT=${LIBEXEC_ROOT:-/usr/local/libexec/router}

#shellcheck source=/usr/local/libexec/router/acme.sh/environment.sh
source "${LIBEXEC_ROOT}/acme.sh/environment.sh"

CF_SECRET_FILE="${LIBEXEC_ROOT}/acme.sh/secret.env"
if [[ -e ${CF_SECRET_FILE} ]]; then
    set -a
    # shellcheck source=/usr/local/libexec/router/acme.sh/secret.env
    source "${CF_SECRET_FILE}"
    set +a
fi

if [[ -z ${CF_Token:-} || -z ${CF_Account_ID:-} || -z ${CF_Zone_ID:-} ]]; then
    echo "缺少 Cloudflare 配置, 创建并编辑 ${CF_SECRET_FILE} 文件，添加以下内容:" >&2
    echo "CF_Token='your_cf_token'" >&2
    echo "CF_Account_ID='your_cf_account_id'" >&2
    echo "CF_Zone_ID='your_cf_zone_id'" >&2
    exit 1
fi

action=""
directory=""
reloadcmd="systemctl reload --no-block nginx"
domain=""
debug=""

usage() {
    cat <<EOF
用法: $0 [--request | --deploy] [--directory=DIR] [--debug=0|1|2] DOMAIN
EOF
    exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
    --request | --deploy)
        if [[ -n $action ]]; then
            echo "参数错误: --request 和 --deploy 互斥" >&2
            usage 1
        fi
        action="${1#--}"
        shift
        ;;

    --reloadcmd=*)
        reloadcmd="${1#--reloadcmd=}"

        if [[ -z $reloadcmd ]]; then
            echo "参数错误: --reloadcmd 不可为空" >&2
            usage 1
        fi

        shift
        ;;

    --directory=*)
        directory="${1#--directory=}"

        if [[ -z $directory ]]; then
            echo "参数错误: --directory 不可为空" >&2
            usage 1
        fi

        shift
        ;;

    --debug=*)
        debug="${1#--debug=}"

        if [[ -z $debug ]]; then
            echo "参数错误: --debug 不可为空" >&2
            usage 1
        fi

        shift
        ;;

    --help | -h)
        usage 0
        ;;

    --*)
        echo "参数错误: 未知选项: $1" >&2
        usage 1
        ;;

    *)
        if [[ -n $domain ]]; then
            echo "参数错误: 只能指定一个 DOMAIN 参数" >&2
            usage 1
        fi

        domain="$1"
        shift
        ;;
    esac
done

if [[ -z $domain ]]; then
    echo "参数错误: 必须指定 DOMAIN" >&2
    usage 1
fi

PUB_ARGS=()
if [[ -n $debug ]]; then
    PUB_ARGS+=("--debug" "$debug")
fi

if [[ $action == "request" ]]; then
    echo "执行申请: $domain" >&2

    acme "${PUB_ARGS[@]}" --issue --ecc --dns dns_cf --domain "$domain"

    echo "申请完成: $domain , 使用 --deploy 执行部署" >&2
elif [[ $action == "deploy" ]]; then
    echo "执行部署: $domain (存放目录: $directory, 重载命令: $reloadcmd)" >&2
    mkdir -p "$directory"
    acme "${PUB_ARGS[@]}" --install-cert --domain "$domain" \
        --reloadcmd "$reloadcmd" \
        --cert-file "$directory/cert.pem" \
        --key-file "$directory/privkey.pem" \
        --fullchain-file "$directory/fullchain.pem" \
        --ca-file "$directory/ca.pem"
else
    # echo "申请证书: $domain" >&2
    # acme "${PUB_ARGS[@]}" --issue --ecc --dns dns_cf --dns-persist --make-dns-persist-value --domain "$domain"
    # echo "完成以上操作后，添加参数 --request 执行申请" >&2

    echo "当前不支持 dns-persist，设置 --request 参数直接申请" >&2
    exit 1
fi
