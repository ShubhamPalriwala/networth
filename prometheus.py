import prometheus_client


# Disable default Prometheus metrics that aren't needed
def disable_default_prom_metrics():
    prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
    prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)


def send_data_for_total_bytes(prom_metric: prometheus_client.Gauge, ip: str, data_transmitted: int):
    prom_metric.labels(ip).set(data_transmitted)


def send_data_to_geomap(prom_metric: prometheus_client.Gauge, city: str, lat: str, lon: str):
    prom_metric.labels(city, lat, lon)


# Start a Prometheus server and a couple of data models
def initialise(port: int):
    disable_default_prom_metrics()
    prometheus_client.start_http_server(port)

    data_per_ip = prometheus_client.Gauge(
        "bytes_per_ip", "Bytes transmitted for this IP", ["ip_address"])
    worldmap = prometheus_client.Gauge(
        "geoip", "Ethernet frames Location-wise", [
            "city", "latitude", "longitude"]
    )
    return data_per_ip, worldmap
