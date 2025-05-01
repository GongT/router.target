function ensure_line_exists() {
	local file="$1"
	local line="$2"
	if ! grep -qF "$line" "$file"; then
		echo "$line" >> "$file"
	fi
}
