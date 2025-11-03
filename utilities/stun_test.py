import stun

def discover():
    nat_type, external_ip, external_port = stun.get_ip_info()
    print("NAT Type:", nat_type)
    print("External IP:", external_ip)
    print("External Port:", external_port)

if __name__ == "__main__":
    discover()
