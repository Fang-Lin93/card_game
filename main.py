""" A toy example of self playing for Paodekuai
    Maybe it is used to play against multiple trained agents if someone can rebuild a game code :)
"""

import seaborn as sns
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt
from SL_card import cards_encode_tensor

from pdkenv import PaodekuaiEnv
from agents.random_agent import RandomAgent
from agents.human_agent import HumanAgent
from agents.deepcard_agent import SL_Agent as Deepcard
#from agents.deepcard_compare import SL_Agent as Deepcard_compare
from agents.rule_agent import RuleAgent
# from rlcard.agents.dqn_agent_pytorch import DQNAgent

DATA_PATH = '/Users/fanglinjiajie/locals/datasets/CardData/'



# agent = DQNAgent('pytor',  state_shape=env.state_shape,mlp_layers=[10,10])
random_agent = RandomAgent()
human_agent = HumanAgent()
rule_agent = RuleAgent()

# deepcard_rand = Deepcard(generate_data=True)
deepcard_0 = Deepcard('deepcard_model_weak')
deepcard_1 = Deepcard('deepcard_model_win', entropy=True)
deepcard_2 = Deepcard('deepcard_model_win')
deepcard_3 = Deepcard('deepcard_model_gen', entropy=True)
deepcard_4 = Deepcard('deepcard_model_gen')

env = PaodekuaiEnv(config={'record_action': True})
env.set_agents([deepcard_4, deepcard_0, deepcard_0])

# trajectories, payoffs = env.run(is_training=False)


episode_num = 1000
winner = []
scores = [[0], [0], [0]]
for epoc in tqdm(range(episode_num)):
    trajectories, payoffs = env.run(is_training=False)
    winner += [env.game.winner_id]
    scores[0] += [env.cum_reward[0]]
    scores[1] += [env.cum_reward[1]]
    scores[2] += [env.cum_reward[2]]

final_score = [env.cum_reward[0], env.cum_reward[1], env.cum_reward[2]]

# plots
x = [0, 1, 2]
win = [winner.count(0) / len(winner), winner.count(1) / len(winner), winner.count(2) / len(winner)]
fig, axes = plt.subplots(2, 2, figsize=(10, 10))
# plot the win rate
sns.barplot(x, win, ax=axes[0][0],)
for i, j in zip(x, win):
    axes[0][0].annotate(j, xy=(i, j))
axes[0][0].set_title('Win Rate')
# plot the score
sns.barplot(x, final_score, ax=axes[0][1])
for i, j in zip(x, final_score):
    axes[0][1].annotate(j, xy=(i, j))
axes[0][1].set_title('Score')
# score curve
curve_axes = plt.subplot(2, 1, 2)
sns.lineplot(np.arange(episode_num+1), scores[0], color='blue', label='player_0', ax=curve_axes)
sns.lineplot(np.arange(episode_num+1), scores[1], color='orange', label='player_1', ax=curve_axes)
sns.lineplot(np.arange(episode_num+1), scores[2], color='green', label='player_2', ax=curve_axes)
curve_axes.set_title('Score_Curve')
fig.show()
fig.savefig('results/agents_fight.png')


# generating data
def generate_data(new=True):
    if new:
        generated_data_x = np.array([]).reshape(-1, 6, 4, 13)
        generated_data_y = np.array([]).reshape(-1, 4, 13)
    else:
        generated_data_x = np.load(DATA_PATH + 'card_tensor_data_x_' + 'gen' + '.npy')
        generated_data_y = np.load(DATA_PATH + 'card_tensor_data_y_' + 'gen' + '.npy')
    episode_num = 5000
    for epoc in tqdm(range(episode_num)):
        trajectories, payoffs = env.run(is_training=False)
        # if env.game.winner_id == 0:
        winner_id = env.game.winner_id
        # record winner behaviors
        for markov_action in trajectories[winner_id]:
            # if action is not 'pass'
            if markov_action[1] != 'pass':
                generated_data_x = np.concatenate([generated_data_x, [markov_action[0]['obs']]])
                generated_data_y = np.concatenate([generated_data_y, [cards_encode_tensor(markov_action[1])]])

            # generated_data_x.append(markov_action[0]['obs'])
         # generated_data_y.append(cards_encode_tensor(markov_action[1]))

    np.save(DATA_PATH + 'card_tensor_data_x_gen', np.array(generated_data_x))
    np.save(DATA_PATH + 'card_tensor_data_y_gen', np.array(generated_data_y))


# np.array(data_X.tolist()) == data_X, b = np.concate([a,b])
data_X, data_Y = np.load(DATA_PATH + 'card_tensor_data_x_' + 'gen' + '.npy'), \
                 np.load(DATA_PATH + 'card_tensor_data_y_' + 'gen' + '.npy')
