import numpy as np


class Transition:
    __slots__ = ["state", "legal_mask", "action", "reward", "next_state", "done", "next_legal_mask"]

    def __init__(self, state, legal_mask, action, reward, next_state, done, next_legal_mask):
        self.state = state
        self.legal_mask = legal_mask
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done
        self.next_legal_mask = next_legal_mask


class PrioritizedReplayBuffer:

    def __init__(self, capacity: int,
                 alpha: float = 0.6,
                 beta: float = 0.4,
                 beta_increment: float = 0.00001,
                 epsilon: float = 1e-5) -> None:

        self.capacity = capacity

        self.buffer: list[Transition] = []
        self.priorities = np.zeros(capacity, dtype=np.float32)

        self._pos = 0

        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.epsilon = epsilon

    def push(self, *args) -> None:
        transition = Transition(*args)

        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self._pos] = transition

        if len(self.buffer) == 1:
            max_priority = 1.0
        else:
            max_priority = self.priorities[:len(self.buffer)].max()

        self.priorities[self._pos] = max_priority

        self._pos = (self._pos + 1) % self.capacity

    def sample(self, batch_size: int) -> tuple[list[Transition], np.ndarray, np.ndarray]:
        size = len(self.buffer)

        priorities = self.priorities[:size]

        scaled_priorities = priorities ** self.alpha

        probs = scaled_priorities / scaled_priorities.sum()

        indices = np.random.choice(
            size,
            batch_size,
            replace=True,
            p=probs
        )

        batch = [self.buffer[i] for i in indices]

        self.beta = min(1.0, self.beta + self.beta_increment)

        weights = (size * probs[indices]) ** (-self.beta)

        weights /= weights.max()

        return batch, indices, weights.astype(np.float32)

    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray) -> None:
        priorities = np.asarray(priorities, dtype=np.float32)
        priorities = np.clip(priorities + self.epsilon, a_min=1e-5, a_max=100.0)
        self.priorities[indices] = priorities

    def __len__(self):
        return len(self.buffer)
    