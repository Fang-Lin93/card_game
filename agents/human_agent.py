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
        self.use_raw = True  # this allows state['raw_legal_actions'] = game.state['actions']

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

    print('\n=============   Your Hand   ===============')
    my_hands = state['obs'][0]
    visual_cards(my_hands)

    print('\n=============   Legal Actions   ===============')
    print(state['legal_actions'])

    # _action_list = []
    # for i in range(1, len(action_record)+1):
    #     _action_list.insert(0, action_record[-i])
    # for pair in _action_list:
    #     print('>> Player', pair[0], 'chooses', pair[1])
    #
    # print('\n=============   Dealer Hand   ===============')
    # print_card(state['dealer hand'])
    #
    # num_player = len(state) - 3
    #
    # for i in range(num_player):
    #     print('===============   Player {} Hand   ==============='.format(i))
    #     print_card(state['player' + str(i) + ' hand'])
    #
    # print('\n=========== Actions You Can Choose ===========')
    # print(', '.join([str(index) + ': ' + action for index, action in enumerate(raw_legal_actions)]))
    # print('')
