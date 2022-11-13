from bcc import BPF

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


# Dictionary to store the corresponding divisor for the data type needed in the form of log
output_power_from_bytes = {"b": 0, "kb": 1, "mb": 2, "gb": 3}
output_data_type = "b"

# Convert the bytes to the preferred data size format
def datatype_conversion(value_in_bytes):
    return value_in_bytes / (1024 ** output_power_from_bytes[output_data_type])


# Parse the event in the eBPF buffer
def parse_ip_event(_, data, size):
    ip_and_bytes = b["events"].event(data)
    ip_in_octet = format_ip_address(ip_and_bytes.ip).decode()
    data_transmitted = datatype_conversion(ip_and_bytes.bytes)
    print("%-32s %-6d" % (ip_in_octet, data_transmitted))


print("\n%-24s %-6s" % ("IP Address", output_data_type))

# Open the ring buffer and provide a callback function for any event
b["events"].open_ring_buffer(parse_ip_event)
while 1:
    try:
        # Start polling the ring buffer for event
        b.ring_buffer_poll()

    except KeyboardInterrupt:
        exit()

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
