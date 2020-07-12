import numpy as np
from pdkutils import visual_cards


class HumanAgent(object):
    ''' A random agent. Random agents is for running toy examples on the card games
    '''

    def __init__(self):
        ''' Initilize the random agent

        Args:
            action_num (int): The size of the ouput action space
        '''
        self.use_raw = True  # this allows state['raw_obs'] = game.state

    @staticmethod
    def step(state):
        ''' Predict the action given the curent state in gerenerating training data.

        Args:
            state (dict): An dictionary that represents the current state
            it's num_state, not raw_state

        Returns:
            action (int): The action predicted (randomly chosen) by the random agent
        '''
        _print_state(state)
        action = str(input('>> You choose action (str): '))
        while action not in state['legal_actions']:
            print('Action illegel...')
            action = str(input('>> Re-choose action (str): '))
        return action

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


def _print_state(state):
    ''' Print out the state

    Args:
        state (dict): A dictionary of the raw state
        action_record (list): A list of the each player's historical actions
    '''
    print('\n=============   Played Cards   ===============')
    for player, card in state['action_record']:
        print(f'Player_{player}: ' + card)

    print('\n======   Remaining Number of Hands   ========')
    for key in state['raw_obs']:
        if 'remain' in key:
            print(key + ':', state['raw_obs'][key])

    print('\n=============   Others Hands   ===============')
    others_hands = state['obs'][1]
    visual_cards(others_hands)


    print('\n=============   Your Hands(player_{})   ==============='.format(state['raw_obs']['self']))
    my_hands = state['obs'][0]
    visual_cards(my_hands)

    print('\n=============   Legal Actions   ===============')
    print(state['legal_actions'])

