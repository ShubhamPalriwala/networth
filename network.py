
import os
import requests
from dotenv import load_dotenv
import prometheus

# Load the environment variables to fetch the API Key
load_dotenv()

ip_info_api_key = os.getenv("IP_INFO_IO_API_KEY")

# Format IP address from number to octet format (a.b.c.d)


def format_ip_address(addr: str):
    formatted_ip = b""
    for class_of_ip in range(0, 4):
        formatted_ip = formatted_ip + str(addr & 0xFF).encode()
        if class_of_ip != 3:
            formatted_ip = formatted_ip + b"."
        addr = addr >> 8
    return formatted_ip


# Dictionary to store the corresponding divisor for the data type needed in the form of log
output_power_from_bytes = {"b": 0, "kb": 1, "mb": 2, "gb": 3}


# Convert the bytes to the preferred data size format
def datatype_conversion(value_in_bytes: int, output_data_type: str):
    return value_in_bytes / (1024 ** output_power_from_bytes[output_data_type])


def get_location_from_ip(ip_address: str):
    try:
        res_in_json = requests.get(
            "http://ipinfo.io/" + ip_address + "?token=" + ip_info_api_key
        ).json()

        city = res_in_json["city"]
        (latitude, longitude) = res_in_json["loc"].split(",")
        return city, latitude, longitude

    except KeyError:
        return None, None, None


def send_if_location_exists_else_find(ip_address: str, location_of_ip: dict, unable_to_find: set, ip_yet_to_find: set, worldmap):
    if not location_of_ip.get(ip_address) and ip_address not in unable_to_find:
        ip_yet_to_find.add(ip_address)
    elif ip_address not in unable_to_find:
        (city, latitude, longitude) = location_of_ip.get(ip_address)
        prometheus.send_data_to_geomap(
            worldmap, city, latitude, longitude)
