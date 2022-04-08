
from typing_extensions import TypedDict
from typing import Dict
from log import Log

l = Log('dtcl')

LinkState = TypedDict("LinkState", {
    'utilization': int,
})

class DataCollector:

    def __init__(self):
        self.reset()

    def reset(self):
        l.log("Reset state")
        self.link_states = {} # (node1,node2) -> LinkState

    # Updates network state by concrete node (target node)
    def update(self, target_node_name: str, link_states: Dict[str, LinkState]):
        """
        @param target_node_name: Node name like `edge01`, that calculates link states
        @param link_states: Source node name -> Link states
        """
        for source_node_name, linkState in link_states.items():
            self.link_states[(source_node_name, target_node_name)] = linkState
        print(self.link_states)

    # Returns network state
    def get_network_state(self):
        # Sort for stability
        items = sorted(self.link_states.items(), key=lambda item: ''.join(item[0]))
        utilizations = list(map(lambda item: item[1]['utilization'], items))
        return utilizations
