from router.target import tools

output = ""
for tld in tools.www.tlds():
    output += f"server=/{tld.lower()}/127.0.0.1#5300\n"

print(output)
