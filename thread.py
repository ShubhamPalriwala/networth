import threading
import prometheus
import network

# Define an isolated thread function to run every 3 seconds that parallely queries the IP addresses for their location and pushed to Prometheus


def find_and_send_new_location(ip_yet_to_find: set, unable_to_find: set, worldmap, location_of_ip: dict):
    threading.Timer(3.0, find_and_send_new_location, args=[ip_yet_to_find,
                    unable_to_find, worldmap, location_of_ip]).start()
    # We define a daemon so that it will also exit once we call sys exit
    threading.Timer.daemon = True
    # We create a copy here as the ip_to_find is also being used parallely by the eBPF for population
    for ip in ip_yet_to_find.copy():
        city, latitude, longitude = network.get_location_from_ip(ip)
        try:
            if city == None:
                unable_to_find.add(ip)
            else:
                prometheus.send_data_to_geomap(
                    worldmap, city, latitude, longitude)
                location_of_ip[ip] = [city, latitude, longitude]
            ip_yet_to_find.remove(ip)
        except KeyError:
            # Happens when concurrently the thread already removed it since this is happening on the original data
            pass
