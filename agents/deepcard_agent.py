import numpy as np
import torch
from torch import nn
import bottleneck
from Deepcard import DeepCard, loss_function
from pdkutils import gt_greater_cards_from_hands, classify_actions, hands_islands
from pdkjudger import PaodekuaiJudger

import joblib
from SL_card import cards_encode_tensor

DATA_PATH = '/Users/fanglinjiajie/locals/datasets/CardData/'

# model = DeepCard()
# model.load_state_dict(torch.load(DATA_PATH + 'deepcard_model_win', map_location=torch.device('cpu')))
#


class SL_Agent(object):
    ''' A model based agent.
    '''

    def __init__(self, model_file, generate_data=False, entropy=False):
        ''' Initilize the agent

        Args:
            action_num (int): The size of the ouput action space
        '''
        self.use_raw = True
        self.generate_data = generate_data
        self.entropy = entropy
        self.model = DeepCard()
        self.model.load_state_dict(torch.load(DATA_PATH + model_file, map_location=torch.device('cpu')))

    def step(self, state):
        ''' Predict the action given the curent state in gerenerating training data.

        Args:
            state (dict): An dictionary that represents the current state

        Returns:
            action (int): The action predicted (randomly chosen) by the random agent
        '''

        current_hand = state['raw_obs']['current_hand']
        legal_actions = state['legal_actions']

        # # check
        # if len(state['raw_obs']['trace']) >= 2:
        #     if state['raw_obs']['trace'][-1][1] == 'pass' and state['raw_obs']['trace'][-2][1] == 'pass':
        #         if set(legal_actions) != PaodekuaiJudger.playable_cards_from_hand(current_hand):
        #             print(legal_actions)
        #             print(current_hand)
        #             raise ValueError('Error')

        # Win the game if possible
        if current_hand in legal_actions:
            return current_hand

        # If no choice, e.g. ['pass']
        if len(legal_actions) == 1:
            return legal_actions[0]

        # set the model to evaluation mode, otherwise the output would be wrong
        with torch.no_grad():
            self.model.eval()
            obs = torch.FloatTensor(state['obs']).reshape(-1, 6, 4, 13)
            prediction = self.model(obs).view(-1, 1, 4, 13)

            if self.generate_data:
                # return choices by prob
                softmax = nn.Softmax(dim=0)
                tensor_cards = torch.FloatTensor([cards_encode_tensor(cards) for cards in legal_actions]).view(-1, 1, 4, 13)
                inner_product = torch.FloatTensor([(prediction * cards).sum() for cards in tensor_cards])
                #
                similarity = softmax(inner_product).numpy()
                top_cards_idx = bottleneck.argpartition(-similarity, 1)[:2]
                top_cards_prob = -bottleneck.partition(-similarity, 1)[:2]
                top_cards_prob = top_cards_prob/sum(top_cards_prob)
                return np.random.choice(np.array(legal_actions)[top_cards_idx], p=top_cards_prob)

            elif not self.entropy:
                # SL card： select the nearest card to the predicted tensor
                # use similarity = inner product
                choice = ''
                similarity = -1
                for cards in legal_actions:
                    tensor_card = torch.FloatTensor(cards_encode_tensor(cards)).reshape(-1, 1, 4, 13)
                    new_sim = (prediction * tensor_card).sum()
                    if new_sim > similarity:
                        choice = cards
                        similarity = new_sim
                return choice
            else:
                choice = ''
                loss = 100000
                for cards in legal_actions:
                    tensor_card = torch.FloatTensor(cards_encode_tensor(cards)).reshape(-1, 1, 4, 13)
                    new_loss = loss_function(prediction, tensor_card)
                    if new_loss < loss:
                        choice = cards
                        loss = new_loss
                return choice



    def eval_step(self, state):
        ''' Predict the action given the current state for evaluation.
            Since the random agents are not trained. This function is equivalent to step function

        Args:
            state (dict): An dictionary that represents the current state

        Returns:
            action (int): The action predicted (randomly chosen) by the random agent
            probs (list): The list of action probabilities
        '''
        return self.step(state), []
