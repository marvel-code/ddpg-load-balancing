import sys

# Topology
LINK_CAPACITY_Mbps = 100
LINK_DELAY_MS = 0

# Graphics
PADDING = 50
D = 80 # base distance
D_PODS = 1.5*D
D_CORE = 2*D



K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
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
        return f'{down_node}.up++ <--> {{delay={LINK_DELAY_MS}ms; datarate={LINK_CAPACITY_Mbps}.0Mbps;}} <--> {up_node}.down++;'

    def controller_connection(node):
        return f'{node}.controller <--> controller.down++;'

    def submodule(name, module, position='0,0'):
        return f'{name}: {module} {{ @display("p={position}"); }}'


    writeline('network FatTree {')
    
    # Graphics
    centerX = PADDING + ((K/2-1)*D*K + D_PODS*(K - 1)) / 2
    y = PADDING
    
    # submodules
    indent = 1
    writeline('submodules:')
    indent = 2
    writeline('// SDN controller')
    writeline(submodule(f'controller', 'Controller', f'{centerX},{y}'))
    writeline('// Core layer')
    y += 3 * D
    for c in range(core_node_count):
        writeline(submodule(f'core{c}', 'Node', f'{centerX + D * (c - (K/2)**2/2 + 0.5)},{y}'))
    for p in range(pod_count):
        writeline(f'// Pod {p}')
        for a in range(aggr_per_pod_count):
            writeline(submodule(f'aggr{p}{a}', 'Node', f'{PADDING + p*((aggr_per_pod_count - 1) * D + D_PODS) + a*D},{y + 1*D}'))
        for e in range(edge_per_pod_count):
            writeline(submodule(f'edge{p}{e}', 'Node', f'{PADDING + p*((edge_per_pod_count - 1) * D + D_PODS) + e*D},{y + 2*D}'))
    
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

    # Controller connections
    writeline('// Controller connections')
    for p in range(pod_count):
        for e in range(edge_per_pod_count):
            edge = f'edge{p}{e}'
            writeline(controller_connection(edge))
    for p in range(pod_count):
        for a in range(aggr_per_pod_count):
            aggr = f'aggr{p}{a}'
            writeline(controller_connection(aggr))
    for c in range(core_node_count):
        core = f'core{c}'
        writeline(controller_connection(core))


    indent = 2

    indent = 0
    writeline('}')

with open('dist/mynetwork.ini', 'w') as f:
    indent = 0
    def writeline(s):
        tabs = ''.join(['\t'] * indent)
        f.write(f'{tabs}{s}\n')

    writeline('[General]')
    writeline('network = FatTree')
    writeline("FatTree.core*.type = 0")
    writeline("FatTree.aggr*.type = 1")
    writeline("FatTree.edge*.type = 2")

    for c in range(core_node_count):
        writeline(f"FatTree.core{c}.pod = -1")
        writeline(f"FatTree.core{c}.number = {c}")
    for p in range(pod_count):
        for a in range(aggr_per_pod_count):
            writeline(f"FatTree.aggr{p}{a}.pod = {p}")
            writeline(f"FatTree.aggr{p}{a}.number = {a}")
        for e in range(edge_per_pod_count):
            writeline(f"FatTree.edge{p}{e}.pod = {p}")
            writeline(f"FatTree.edge{p}{e}.number = {e}")
