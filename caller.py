from bcc import BPF

# Specify the Interface (if in doubt, run `ip addr` and change the interface accordingly)
device = "wlan0"

# Loading the source file to be compiled against the bpf target
b = BPF(src_file="core.c")

# Load the specified function and specify the program type
fn = b.load_func("print_on_every_packet", BPF.XDP)

# We now finally attach the function to the device and no flags (0)
b.attach_xdp(device, fn, 0)

try:
    # Print the trace values we receive
    b.trace_print()

except KeyboardInterrupt:
    print("ending")

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
