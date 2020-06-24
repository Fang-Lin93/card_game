""" A toy example of self playing for Blackjack
    Maybe it is used to play against multiple trained agents if someone can rebuild a game code :)
"""

from pdkenv import PaodekuaiEnv
from agents.random_agent import RandomAgent
from agents.human_agent import HumanAgent

env = PaodekuaiEnv(config={'record_action': True})
random_agent = RandomAgent(env.action_num)
human_agent = HumanAgent()
env.set_agents([random_agent, human_agent, random_agent])

trajectories, payoffs = env.run(is_training=False)