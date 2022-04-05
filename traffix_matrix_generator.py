import sys

DIST = 'dist'

K = 4
core_node_count = int((K / 2) ** 2)
pod_count = K
edge_per_pod_count = int(K / 2)
aggr_per_pod_count = edge_per_pod_count

index = '0'
interval_ms = 1000
packet_size_bytes = 64 * 1024
packet_arrival_delay_mean = 50
packet_arrival_delay_stddev = 10

with open(f"{DIST}/TM{index}.txt", "w") as f:
    indent = 0
    def writeline(s):
        tabs = ''.join(['\t'] * indent)
        f.write(f'{tabs}{s}\n')
        
    writeline(f"{interval_ms}")
    writeline(f"{packet_size_bytes} {packet_arrival_delay_mean} {packet_arrival_delay_stddev}")
    for p1 in range(pod_count):
        for e1 in range(edge_per_pod_count):
            for p2 in range(pod_count):
                for e2 in range(edge_per_pod_count):
                    writeline(f'edge{p1}{e1} edge{p2}{e2}')

