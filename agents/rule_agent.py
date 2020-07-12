import numpy as np
from pdkutils import gt_greater_cards_from_hands, classify_actions, hands_islands
from pdkjudger import PaodekuaiJudger


class RuleAgent(object):
    ''' A random agent. Random agents is for running toy examples on the card games
    '''

    def __init__(self):
        ''' Initilize the random agent

        Args:
            action_num (int): The size of the ouput action space
        '''
        self.use_raw = True

    @staticmethod
    def step(state):
        ''' Predict the action given the curent state in gerenerating training data.

        Args:
            state (dict): An dictionary that represents the current state

        Returns:
            action (int): The action predicted (randomly chosen) by the random agent
        '''

        priorities = ['plane_chain', 'pair_chain', 'solo_chain', 'plane', 'pair', 'solo']

        current_hand = state['raw_obs']['current_hand']
        legal_actions = state['legal_actions']  # == state['raw_obs']['actions']
        others_hands = state['raw_obs']['others_hand']

        # Win the game if possible
        if current_hand in legal_actions:
            return current_hand

        # If no choice, e.g. ['pass']
        if len(legal_actions) == 1:
            return legal_actions[0]
        # Kick out others greater hands if possible
        # if self.kick:
        #     if len(others_hands) < 15:
        #         for action in legal_actions:
        #             others_react = gt_greater_cards_from_hands(others_hands, action)
        #             if len(others_react) in [1, 2]:
        #                 return action

        # Try to play long cards
        sorted_my_actions = classify_actions(legal_actions)
        for card_pri in priorities:
            for key in sorted_my_actions.keys():
                if card_pri in key:
                    for card, _ in sorted_my_actions[key]:
                        return card

        return np.random.choice(legal_actions)

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
