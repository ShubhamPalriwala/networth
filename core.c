#define KBUILD_MODNAME "find_whether_tcp_or_udp"
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>

int find_whether_tcp_or_udp(struct xdp_md *ctx)
{
    // We mark the start and end of our ethernet frame
    void *ethernet_start = (void *)(long)ctx->data;
    void *ethernet_end = (void *)(long)ctx->data_end;

    struct ethhdr *ethernet_frame = ethernet_start;

    // Check if we have the entire ethernet frame
    if ((void *)ethernet_frame + sizeof(ethernet_frame) <= ethernet_end)
    {
        struct iphdr *ip_packet = ethernet_start + sizeof(*ethernet_frame);

        // Check if the entire IP is inside this ethernet frame
        if ((void *)ip_packet + sizeof(*ip_packet) <= ethernet_end)
        {
            // If TCP packet
            if (ip_packet->protocol == IPPROTO_TCP)
            {
                bpf_trace_printk("Found TCP packet");
            }
            // If TCP packet
            else if (ip_packet->protocol == IPPROTO_UDP)
            {
                bpf_trace_printk("Found UDP packet");
            }
        }
    }

    return XDP_PASS;
}