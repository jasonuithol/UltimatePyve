import urllib.request

SERVICES = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://checkip.amazonaws.com",
]

def get_external_ip():
    for url in SERVICES:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.read().decode().strip()
        except Exception:
            continue
    raise RuntimeError("All external IP services failed")

if __name__ == "__main__":
    print("External IP:", get_external_ip())