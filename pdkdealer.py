# -*- coding: utf-8 -*-
''' Implement Paodekuai Dealer class
'''

import functools
import random
from pdkutils import init_48_deck
from pdkutils import cards2str, cards2str_with_suit, paodekuai_sort_card


class PaodekuaiDealer(object):
    ''' Dealer will shuffle, deal cards, and determine players' roles
    '''
    num_split = 3

    def __init__(self, np_random):
        '''Give dealer the deck

        Notes:
            1. deck with 54 cards including black joker and red joker
        '''
        self.np_random = np_random
        self.deck = init_48_deck()
        self.deck.sort(key=functools.cmp_to_key(paodekuai_sort_card))
        # sorted to '3333444455556666777788889999TTTTJJJJQQQQKKKKAAA2'

    def shuffle(self):
        ''' Randomly shuffle the deck
        '''
        self.np_random.shuffle(self.deck)

    def deal_cards(self, players):
        ''' Deal cards to players

        Args:
            players (list): list of PaodekuaiPlayer objects
        '''
        hand_num = len(self.deck) // self.num_split
        #check

        for index, player in enumerate(players):
            current_hand = self.deck[index * hand_num:(index + 1) * hand_num]
            current_hand.sort(key=functools.cmp_to_key(paodekuai_sort_card))
            player.set_current_hand(current_hand)
            player.initial_hand = cards2str(player.current_hand)

    # The player who got 'S3' will go first
    def determine_first(self, players, game_rule=False, random_deal=True):
        if game_rule:
            sign = 'S3'
            for player in players:
                if sign in cards2str_with_suit(player.current_hand):
                    return player.player_id
        if random_deal:
            return random.randint(0, len(players)-1)
        else:
            return 0

    # def determine_role(self, players):
    #     ''' Determine landlord and peasants according to players' hand
    #
    #     Args:
    #         players (list): list of PaodekuaiPlayer objects
    #
    #     Returns:
    #         int: landlord's player_id
    #     '''
    #     # deal cards
    #     self.shuffle()
    #     self.deal_cards(players)
    #     players[0].role = 'landlord'
    #     self.landlord = players[0]
    #     players[1].role = 'peasant'
    #     players[2].role = 'peasant'
    #     #players[0].role = 'peasant'
    #     #self.landlord = players[0]
    #
    #     ## determine 'landlord'
    #     #max_score = get_landlord_score(
    #     #    cards2str(self.landlord.current_hand))
    #     #for player in players[1:]:
    #     #    player.role = 'peasant'
    #     #    score = get_landlord_score(
    #     #        cards2str(player.current_hand))
    #     #    if score > max_score:
    #     #        max_score = score
    #     #        self.landlord = player
    #     #self.landlord.role = 'landlord'
    #
    #     # # give the 'landlord' the  three cards
    #     # self.landlord.current_hand.extend(self.deck[-3:])
    #     # self.landlord.current_hand.sort(key=functools.cmp_to_key(doudizhu_sort_card))
    #     # self.landlord.initial_hand = cards2str(self.landlord.current_hand)
    #     return self.landlord.player_id
