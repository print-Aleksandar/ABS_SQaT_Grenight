from pathlib import Path
import torch
from agent.grenight_agent import GrenightAgent


def load_checkpoint(agent: GrenightAgent,
                    code: str,
                    ep: int,
                    is_for_training: bool|None=False):

    current_dir = Path(__file__).resolve().parent
    checkpoint_path = current_dir / f"../implementations/{code}/curr_impl_ep{ep}.pt"

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cuda" if torch.cuda.is_available() else "cpu",
        weights_only=False
    )

    agent.policy_net.load_state_dict(checkpoint["policy_state_dict"])
    if agent.is_double_net:
        agent.target_net.load_state_dict(checkpoint["target_state_dict"])

    if is_for_training:
        agent.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        agent.train_steps = checkpoint["train_steps"]

        episode = checkpoint["episode"]
        agent_step = checkpoint["agent_step"]

        return episode, agent_step

    return None
