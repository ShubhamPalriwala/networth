from bcc import BPF

import utils.network as network
import utils.prometheus as prometheus
import utils.thread as thread
import utils.protocol_translation as protocol_translation

# Specify the Interface (if in doubt, run `ip addr` and change the interface accordingly)
device = "wlan0"

# Loading the source file to be compiled against the bpf target
b = BPF(src_file="core.c")

# Load the specified function and specify the program type
fn = b.load_func("count_network_bytes_per_ip", BPF.XDP)

# We now finally attach the function to the device and no flags (0)
b.attach_xdp(device, fn, 0)

# Dict to store key/value pair of IP correspoonding to location to avoid repeat lookups
location_of_ip = {}
# Set of IPs yet to be queries by the thread for lookup
ip_yet_to_find = set()
# Set to eliminate the IPs whose location cannot be found to avoid repeated failed lookups
unable_to_find = set()


output_data_type = "b"


# This is the callback function that runs on every event at the NIC level
def runs_on_every_ethernet_frame(_, data, size):
    ip_and_bytes = b["events"].event(data)
    ip_in_octet = network.format_ip_address(ip_and_bytes.ip).decode()

    protocol = protocol_translation.translate_protocol(ip_and_bytes.protocol)

    data_transmitted = network.datatype_conversion(
        ip_and_bytes.bytes, output_data_type)

    prometheus.send_data_for_total_bytes(
        data_per_ip, ip_in_octet, data_transmitted)

    network.send_if_location_exists_else_find(
        ip_in_octet, location_of_ip, unable_to_find, ip_yet_to_find, worldmap)

    prometheus.send_data_for_protocols(protocols_used, protocol)


print("\n\n█▄░█ █▀▀ ▀█▀ █░█░█ █▀█ █▀█ ▀█▀ █░█")
print("█░▀█ ██▄ ░█░ ▀▄▀▄▀ █▄█ █▀▄ ░█░ █▀█\n\n")


print("Sending data over to Prometheus, check the logs at http://localhost:8000\n")
print("Head over to http://localhost:3000 and import the grafana JSON to view the data on the dashboard")


# Open the ring buffer and provide a callback function for any event
b["events"].open_ring_buffer(runs_on_every_ethernet_frame)
try:
    data_per_ip, worldmap, protocols_used = prometheus.initialise(8000)

    # Launch the thread
    thread.find_and_send_new_location(
        ip_yet_to_find, unable_to_find, worldmap, location_of_ip)

    while 1:
        # Start polling the ring buffer for event
        b.ring_buffer_poll()

except KeyboardInterrupt:
    print("\n\n\nFaced any issues? Feel free to open an issue at https://github.com/ShubhamPalriwala/networth/issues")
    exit()

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
