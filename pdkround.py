# -*- coding: utf-8 -*-
''' Implement Paodekuai Round class
'''

import functools
import numpy as np

from pdkdealer import PaodekuaiDealer as Dealer
from pdkutils import cards2str, sort_card
from pdkutils import CARD_RANK_STR, CARD_RANK_STR_INDEX


class PaodekuaiRound(object):
    ''' Round can call other Classes' functions to keep the game running
    '''

    def __init__(self, np_random):
        self.np_random = np_random
        self.trace = []
        self.played_cards = '' #np.zeros((len(CARD_RANK_STR), ), dtype=np.int)

        self.greater_player = None
        self.dealer = Dealer(self.np_random)
        self.deck_str = cards2str(self.dealer.deck)

    def initiate(self, players):
        ''' Call dealer to deal cards and bid landlord.

        Args:
            players (list): list of PaodekuaiPlayer objects
        '''
        self.dealer.shuffle()
        self.dealer.deal_cards(players)

        self.current_player = self.dealer.determine_first(players)

        remains = {'remain_{}'.format(player.player_id) : len(player.current_hand) for player in players}
        self.public = {'deck': self.deck_str, 'trace': self.trace,
                       'played_cards': '', **remains}

    @staticmethod
    def cards_ndarray_to_list(ndarray_cards):
        result = []
        for i, _ in enumerate(ndarray_cards):
            if ndarray_cards[i] != 0:
                result.extend([CARD_RANK_STR[i]] * ndarray_cards[i])
        return result

    def update_public(self, player, action):
        ''' Update public trace and played cards

        Args:
            action(str): string of legal specific action
        '''
        self.trace.append((self.current_player, action))
        if action != 'pass':
            self.played_cards += action
            self.played_cards = sort_card(self.played_cards)
            # for c in action:
            #     self.played_cards[CARD_RANK_STR_INDEX[c]] += 1
            self.public['played_cards'] = self.played_cards#self.cards_ndarray_to_list(self.played_cards)
            self.public['remain_{}'.format(player.player_id)] = len(player.current_hand) - len(action)
            # self.played_cards.extend(list(action))
            # self.played_cards.sort(key=functools.cmp_to_key(paodekuai_sort_str))

    def proceed_round(self, player, action):
        # this is how player update their cards
        ''' Call other Classes's functions to keep one round running

        Args:
            player (object): object of PaodekuaiPlayer
            action (str): string of legal specific action

        Returns:
            object of PaodekuaiPlayer: player who played current biggest cards.
        '''
        # First update public information, then update the hands of the player
        self.update_public(player, action)
        self.greater_player = player.play(action, self.greater_player)
        return self.greater_player

    def step_back(self, players):
        ''' Reverse the last action

        Args:
            players (list): list of PaodekuaiPlayer objects
        Returns:
            The last player id and the cards played
        '''
        player_id, cards = self.trace.pop()
        self.current_player = player_id
        if (cards != 'pass'):
            for card in cards:
                self.played_cards = self.played_cards.replace(card, '')
                # self.played_cards.remove(card)
                #self.played_cards[CARD_RANK_STR_INDEX[card]] -= 1
            self.public['played_cards'] = self.played_cards# self.cards_ndarray_to_list(self.played_cards)
        greater_player_id = self.find_last_greater_player_id_in_trace()
        if (greater_player_id is not None):
            self.greater_player = players[greater_player_id]
        else:
            self.greater_player = None
        return player_id, cards

    def find_last_greater_player_id_in_trace(self):
        ''' Find the last greater_player's id in trace

        Returns:
            The last greater_player's id in trace
        '''
        for i in range(len(self.trace) - 1, -1, -1):
            _id, action = self.trace[i]
            if (action != 'pass'):
                return _id
        return None

    def find_last_played_cards_in_trace(self, player_id):
        ''' Find the player_id's last played_cards in trace

        Returns:
            The player_id's last played_cards in trace
        '''
        for i in range(len(self.trace) - 1, -1, -1):
            _id, action = self.trace[i]
            if (_id == player_id and action != 'pass'):
                return action
        return None
