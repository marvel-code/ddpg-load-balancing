import sys

K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
LINK_CAPACITY_MB = 8000
LINK_DELAY_MS = 10

PADDING = 50
D = 80 # base distance
D_PODS = 1.5*D
D_CORE = 2*D



core_node_count = int((K / 2) ** 2)
pod_count = K
edge_per_pod_count = int(K / 2)
aggr_per_pod_count = edge_per_pod_count

with open('dist/fat_tree.ned', 'w') as f:
    indent = 0
    def writeline(s):
        tabs = ''.join(['\t'] * indent)
        f.write(f'{tabs}{s}\n')

    def connection(down_node, up_node):
        return f'{down_node}.up++ <--> {up_node}.down++;'

    def submodule(name, module, position='0,0'):
        return f'{name}: {module} {{ @display("p={position}"); }}'


    writeline('network FatTree {')
    
    # Graphics
    centerX = PADDING + ((K/2-1)*D*K + D_PODS*(K - 1)) / 2
    
    # submodules
    indent = 1
    writeline('submodules:')
    indent = 2
    writeline('// Core layer')
    for c in range(core_node_count):
        writeline(submodule(f'core{c}', 'Node', f'{centerX + D * (c - (K/2)**2/2 + 0.5)},{PADDING}'))
    for p in range(pod_count):
        writeline(f'// Pod {p}')
        for a in range(aggr_per_pod_count):
            writeline(submodule(f'aggr{p}{a}', 'Node', f'{PADDING + p*((aggr_per_pod_count - 1) * D + D_PODS) + a*D},{PADDING + 2*D}'))
        for e in range(edge_per_pod_count):
            writeline(submodule(f'edge{p}{e}', 'Node', f'{PADDING + p*((edge_per_pod_count - 1) * D + D_PODS) + e*D},{PADDING + 3*D}'))
    
    # connections
    indent = 1
    writeline('connections:')

    indent = 2
    for p in range(pod_count):
        writeline(f'// Pod {p}')

        # Connect edge and aggr layers
        for e in range(edge_per_pod_count):
            edge = f'edge{p}{e}'
            for a in range(aggr_per_pod_count):
                aggr = f'aggr{p}{a}'
                writeline(connection(edge, aggr))
                
        # Connect aggr and core layers
        for a in range(aggr_per_pod_count):
            aggr = f'aggr{p}{a}'
            for c in range(core_node_count):
                core = f'core{c}'
                writeline(connection(aggr, core))


    indent = 2

    indent = 0
    writeline('}')

