#define KBUILD_MODNAME "count_network_bytes_per_ip"
#include <linux/bpf.h>
#include <linux/ip.h>
#include <linux/tcp.h>

struct ip_details
{
    unsigned int ip;
    unsigned int bytes;
    unsigned int protocol;
};

BPF_RINGBUF_OUTPUT(events, 128);

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
            struct ip_details *ip_and_byte = events.ringbuf_reserve(sizeof(struct ip_details));
            if (!ip_and_byte)
            {
                return 1;
            }
            unsigned int source_ip = ip_packet->saddr;
            unsigned int ethernet_size_in_bytes = (ethernet_end - ethernet_start);
            ip_and_byte->ip = source_ip;
            ip_and_byte->bytes = ethernet_size_in_bytes;
            ip_and_byte->protocol = ip_packet->protocol;
            events.ringbuf_submit(ip_and_byte, 0);
        }
    }

    return XDP_PASS;
}
