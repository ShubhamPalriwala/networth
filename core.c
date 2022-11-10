#define KBUILD_MODNAME "count_network_bytes_per_ip"
#include <linux/bpf.h>
#include <linux/ip.h>

BPF_HISTOGRAM(counter, unsigned int);

int count_network_bytes_per_ip(struct xdp_md *ctx)
{
    // We mark the start and end of our ethernet frame
    void *ethernet_start = (void *)(long)ctx->data;
    void *ethernet_end = (void *)(long)ctx->data_end;

    struct ethhdr *ethernet_frame = ethernet_start;

    // Check if we have the entire ethernet frame
    if ((void *)ethernet_frame + sizeof(ethernet_frame) <= ethernet_end)
    {
        struct iphdr *ip_packet = ethernet_start + sizeof(*ethernet_frame);

        // Check if the IP packet is within the bounds of ethernet frame
        if ((void *)ip_packet + sizeof(*ip_packet) <= ethernet_end)
        {

            unsigned int value = ip_packet->saddr;
            unsigned int ethernet_size_in_bytes = (ethernet_end - ethernet_start);

            counter.increment(value, ethernet_size_in_bytes);
        }
    }

    return XDP_PASS;
}
