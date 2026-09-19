from environment.grenight_environment import GrenightEnvironment

env = GrenightEnvironment(is_canonical_version=True)
env.reset()
print(env.get_state())