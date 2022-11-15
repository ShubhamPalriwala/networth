import os
import threading

import requests
from bcc import BPF
from dotenv import load_dotenv
from prometheus_client import (GC_COLLECTOR, PLATFORM_COLLECTOR,
                               PROCESS_COLLECTOR, REGISTRY, Gauge,
                               start_http_server)

# Specify the Interface (if in doubt, run `ip addr` and change the interface accordingly)
device = "wlan0"

# Loading the source file to be compiled against the bpf target
b = BPF(src_file="core.c")

# Load the specified function and specify the program type
fn = b.load_func("count_network_bytes_per_ip", BPF.XDP)

# We now finally attach the function to the device and no flags (0)
b.attach_xdp(device, fn, 0)

# Load the environment variables to fetch the API Key
load_dotenv()

ip_info_api_key = os.getenv("IP_INFO_IO_API_KEY")

# Define global variables
location_of_ip = {}
ip_to_find = set()
unable_to_find = set()


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


def disable_default_prom_metrics():
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(GC_COLLECTOR)

# Define an isolated thread function to run every 3 seconds that parallely queries the IP addresses for their location and pushed to Prometheus
def find_location_from_ip():
    threading.Timer(3.0, find_location_from_ip).start()
    # We define a daemon so that it will also exit once we call sys exit
    threading.Timer.daemon = True
    # We create a copy here as the ip_to_find is also being used parallely by the eBPF for population
    for ip in ip_to_find.copy():
        try:
            res_in_json = requests.get(
                "http://ipinfo.io/" + ip + "?token=" + ip_info_api_key
            ).json()

            city = res_in_json["city"]
            (latitude, longitude) = res_in_json["loc"].split(",")
            print(city, latitude, longitude)
            worldmap.labels(city, latitude, longitude)

            location_of_ip[ip] = [city, latitude, longitude]
            ip_to_find.remove(ip)

        except KeyError:
            unable_to_find.add(ip)
            ip_to_find.remove(ip)


def fetch_location(ip_address):
    if not location_of_ip.get(ip_address) and ip_address not in unable_to_find:
        ip_to_find.add(ip_address)
    elif ip_address not in unable_to_find:
        (city, latitude, longitude) = location_of_ip.get(ip_address)
        worldmap.labels(city, latitude, longitude)


# Parse the event in the eBPF buffer
def parse_ip_event(_, data, size):
    ip_and_bytes = b["events"].event(data)
    ip_in_octet = format_ip_address(ip_and_bytes.ip).decode()

    data_transmitted = datatype_conversion(ip_and_bytes.bytes)
    fetch_location(ip_in_octet)

    print("%-32s %-6d" % (ip_in_octet, data_transmitted))

    g.labels(ip_in_octet).set(data_transmitted)


print("\n%-24s %-6s" % ("IP Address", output_data_type))

# Open the ring buffer and provide a callback function for any event
b["events"].open_ring_buffer(parse_ip_event)
try:
    start_http_server(8000)
    disable_default_prom_metrics()

    g = Gauge("bytes_per_ip", "Bytes transmitted for this IP", ["ip_address"])
    worldmap = Gauge(
        "geoip", "Ethernet frames Location-wise", [
            "city", "latitude", "longitude"]
    )

    # Launch the thread
    find_location_from_ip()

    while 1:
        # Start polling the ring buffer for event
        b.ring_buffer_poll()

except KeyboardInterrupt:
    exit()

# Gracefully remove the loaded xdp program from the device and again with no flags
b.remove_xdp(device, 0)
