from bcc import BPF
import socket

# Specify the Interface (if in doubt, run `ip addr` and change the interface accordingly)
device = "wlan0"

# Loading the source file to be compiled against the bpf target
b = BPF(src_file="core.c")

# Load the specified function and specify the program type
fn = b.load_func("count_network_bytes_per_ip", BPF.XDP)

# We now finally attach the function to the device and no flags (0)
b.attach_xdp(device, fn, 0)

# Format IP address from number to octet format (a.b.c.d)
def format_ip_address(addr):
    formatted_ip = b""
    for class_of_ip in range(0, 4):
        formatted_ip = formatted_ip + str(addr & 0xFF).encode()
        if class_of_ip != 3:
            formatted_ip = formatted_ip + b"."
        addr = addr >> 8
    return formatted_ip


print("Activating the monitoring, press Ctrl+C to stop and view results.")

while 1:
    try:
        # Parse the trace values we receive
        (wifi_driver, idk_what_this_is, cpu, flags, timestamp, msg) = b.trace_fields()

    except KeyboardInterrupt:
        print("\n%-24s %-6s" % ("IP Address", "bytes transmitted"))

        dist = b.get_table("counter")
        for k, v in dist.items():
            ip_in_octet = format_ip_address(k.value).decode()
            try:
                host = socket.gethostbyaddr(ip_in_octet)[0]
            except socket.error:
                host = ip_in_octet

            print("%-32s %-6d" % (host, v.value))
        exit()

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
