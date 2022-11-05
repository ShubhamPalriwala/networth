#define KBUILD_MODNAME "print_on_every_packet"
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>

BPF_HISTOGRAM(counter, u64);

int print_on_every_packet(struct xdp_md *ctx)
{
    bpf_trace_printk("packet recd at NIC level");
    return XDP_PASS;
}