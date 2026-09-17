import random

class OpponentPool:
    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self.snapshots = []

    def add(self, policy_net) -> None:
        snap = policy_net.state_dict()
        self.snapshots.append(snap)
        if len(self.snapshots) > self.max_size:
            self.snapshots.pop(random.randint(0, len(self.snapshots) - 1))

    def sample_opponent_net(self, network_ctor, device):
        if not self.snapshots:
            return None

        state_dict = random.choice(self.snapshots)
        net = network_ctor().to(device)
        net.load_state_dict(state_dict)
        net.eval()
        return net