from bcc import BPF

# Specify the Interface (if in doubt, run `ip addr` and change the interface accordingly)
device = "wlan0"

# Loading the source file to be compiled against the bpf target
b = BPF(src_file="core.c")

# Load the specified function and specify the program type
fn = b.load_func("find_whether_tcp_or_udp", BPF.XDP)

# We now finally attach the function to the device and no flags (0)
b.attach_xdp(device, fn, 0)

while 1:
    try:
        # Parse the trace values we receive
        (wifi_driver, idk_what_this_is, cpu, flags, timestamp, msg) = b.trace_fields()

        # Decode the string bytes using UTF-8
        d_msg = msg.decode()
        print(d_msg + " at", timestamp)

    except KeyboardInterrupt:
        print("\nEnding gracefully")
        exit()

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
