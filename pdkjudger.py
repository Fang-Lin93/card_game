# -*- coding: utf-8 -*-
''' Implement Paodekuai Judger class
'''
import numpy as np
import collections
from itertools import combinations
from bisect import bisect_left
from rules import sort_card_rank
from pdkutils import CARD_RANK_STR, CARD_RANK_STR_INDEX, ACTION_LIST
from pdkutils import cards2str, contains_cards


def sort_card(cards):
    card_order = '3456789TJQKA2'
    res = ''
    candid = list(cards)
    for card in card_order:
        while card in candid:
            res += card
            candid.remove(card)
    return res


FIXED_LIST = []
FLEXIBLE_LIST = []
for card in ACTION_LIST:
    if '*' not in card:
        FIXED_LIST += [card]
    else:
        FLEXIBLE_LIST += [(card, card.replace('*', ''))]


class PaodekuaiJudger(object):
    """ Determine what cards a player can play
    """

    @staticmethod
    def sort_card(cards):
        card_order = '3456789TJQKA2'
        res = ''
        candid = list(cards)
        for card in card_order:
            while card in candid:
                res += card
                candid.remove(card)
        return res

    @staticmethod
    def chain_indexes(indexes_list):
        """ Find chains for solos, pairs and trios by using indexes_list

        Args:
            indexes_list: the indexes of cards those have the same count, the count could be 1, 2, or 3.

        Returns:
            list of tuples: [(start_index1, length1), (start_index1, length1), ...]

        """
        chains = []
        prev_index = -100
        count = 0
        start = None
        for i in indexes_list:
            if (i[0] >= 12):  # no chains for '2BR'
                break
            if (i[0] == prev_index + 1):
                count += 1
            else:
                if (count > 1):
                    chains.append((start, count))
                count = 1
                start = i[0]
            prev_index = i[0]
        if (count > 1):
            chains.append((start, count))
        return chains

    @classmethod
    def solo_attachments(cls, hands, chain_start, chain_length, size):
        ''' Find solo attachments for trio_chain_solo_x and four_two_solo

        Args:
            hands:
            chain_start: the index of start card of the trio_chain or trio or four
            chain_length: the size of the sequence of the chain, 1 for trio_solo or four_two_solo
            size: count of solos for the attachments

        Returns:
            list of tuples: [attachment1, attachment2, ...]
                            Each attachment has two elemnts,
                            the first one contains indexes of attached cards smaller than the index of chain_start,
                            the second one contains indexes of attached cards larger than the index of chain_start
        '''
        attachments = set()
        candidates = []
        prev_card = None
        same_card_count = 0
        for card in hands:
            # dont count those cards in the chain
            if (CARD_RANK_STR_INDEX[card] >= chain_start and CARD_RANK_STR_INDEX[card] < chain_start + chain_length):
                continue
            if (card == prev_card):
                # attachments can not have bomb
                if (same_card_count == 3):
                    continue
                # attachments can not have 3 same cards consecutive with the trio (except 3 cards of '222')
                elif (same_card_count == 2 and (CARD_RANK_STR_INDEX[card] == chain_start - 1 or CARD_RANK_STR_INDEX[
                    card] == chain_start + chain_length) and card != '2'):
                    continue
                else:
                    same_card_count += 1
            else:
                prev_card = card
                same_card_count = 1
            candidates.append(CARD_RANK_STR_INDEX[card])
        for attachment in combinations(candidates, size):
            if (attachment[-1] == 14 and attachment[-2] == 13):
                continue
            i = bisect_left(attachment, chain_start)
            attachments.add((attachment[:i], attachment[i:]))
        return list(attachments)

    @classmethod
    def pair_attachments(cls, cards_count, chain_start, chain_length, size):
        ''' Find pair attachments for trio_chain_pair_x and four_two_pair

        Args:
            cards_count:
            chain_start: the index of start card of the trio_chain or trio or four
            chain_length: the size of the sequence of the chain, 1 for trio_pair or four_two_pair
            size: count of pairs for the attachments

        Returns:
            list of tuples: [attachment1, attachment2, ...]
                            Each attachment has two elemnts,
                            the first one contains indexes of attached cards smaller than the index of chain_start,
                            the first one contains indexes of attached cards larger than the index of chain_start
        '''
        attachments = set()
        candidates = []
        for i, _ in enumerate(cards_count):
            if (i >= chain_start and i < chain_start + chain_length):
                continue
            if (cards_count[i] == 2 or cards_count[i] == 3):
                candidates.append(i)
            elif (cards_count[i] == 4):
                candidates.append(i)
        for attachment in combinations(candidates, size):
            if (attachment[-1] == 14 and attachment[-2] == 13):
                continue
            i = bisect_left(attachment, chain_start)
            attachments.add((attachment[:i], attachment[i:]))
        return list(attachments)

    @staticmethod
    def playable_cards_from_hand(current_hand):
        """ Get playable cards from hand

        current_hand: (str)

        Returns:
            set: set of string of playable cards
        """
        cards_dict = collections.defaultdict(int)
        for card in current_hand:
            cards_dict[card] += 1
        cards_count = np.array([cards_dict[k] for k in CARD_RANK_STR])
        playable_cards = set()

        non_zero_indexes = np.argwhere(cards_count > 0)
        more_than_1_indexes = np.argwhere(cards_count > 1)
        more_than_2_indexes = np.argwhere(cards_count > 2)
        more_than_3_indexes = np.argwhere(cards_count > 3)
        hands_count = len(current_hand)
        # solo
        for i in non_zero_indexes:
            playable_cards.add(CARD_RANK_STR[i[0]])
        # pair
        for i in more_than_1_indexes:
            playable_cards.add(CARD_RANK_STR[i[0]] * 2)
        # bomb
        for i in more_than_3_indexes:
            cards = CARD_RANK_STR[i[0]] * 4
            playable_cards.add(cards)

        if 'AAA' in current_hand:
            playable_cards.add('AAA')
            rest = list(current_hand.replace('AAA', ''))
            others = set(combinations(rest, 3))
            for other in others:
                new = 'AAA'
                for rank in other:
                    new += rank
                playable_cards.add(sort_card_rank(new))

        # solo_chain_5 -- #solo_chain_12 start_index is idx in CARD_RANK_STR, gets rank
        solo_chain_indexes = PaodekuaiJudger.chain_indexes(non_zero_indexes)
        for (start_index, length) in solo_chain_indexes:
            s, l = start_index, length
            while (l >= 5):
                cards = ''
                curr_index = s - 1
                curr_length = 0
                while (curr_length < l and curr_length < 12):
                    curr_index += 1
                    curr_length += 1
                    cards += CARD_RANK_STR[curr_index]
                    if (curr_length >= 5):
                        playable_cards.add(cards)
                l -= 1
                s += 1

        # pair_chain_2 -- #pair_chain_8
        pair_chain_indexes = PaodekuaiJudger.chain_indexes(more_than_1_indexes)
        for (start_index, length) in pair_chain_indexes:
            s, l = start_index, length
            while l >= 2:
                cards = ''
                curr_index = s - 1
                curr_length = 0
                while (curr_length < l and curr_length < 8):
                    curr_index += 1
                    curr_length += 1
                    cards += CARD_RANK_STR[curr_index] * 2
                    if (curr_length >= 2):
                        playable_cards.add(cards)
                l -= 1
                s += 1

        # trio, trio_solo ,only when the player can finish it
        for i in more_than_2_indexes:
            if hands_count == 3:
                playable_cards.add(CARD_RANK_STR[i[0]] * 3)
            if hands_count == 4:
                for j in non_zero_indexes:
                    if (j < i):
                        playable_cards.add(CARD_RANK_STR[j[0]] + CARD_RANK_STR[i[0]] * 3)
                    elif (j > i):
                        playable_cards.add(CARD_RANK_STR[i[0]] * 3 + CARD_RANK_STR[j[0]])

        # trio + solo*2
            for left, right in PaodekuaiJudger.solo_attachments(current_hand, i[0], 1, 2):
                pre_attached = ''
                for j in left:
                    pre_attached += CARD_RANK_STR[j]
                post_attached = ''
                for j in right:
                    post_attached += CARD_RANK_STR[j]
                playable_cards.add(pre_attached + CARD_RANK_STR[i[0]]*3 + post_attached)


        # plane_chain
        trio_chain_indexes = PaodekuaiJudger.chain_indexes(more_than_2_indexes)
        for (start_index, length) in trio_chain_indexes:
            # # if you can finish it
            if length * 5 >= hands_count:
                playable_cards.add(current_hand)

            s, l = start_index, length
            while l >= 2:
                cards = ''
                curr_index = s - 1
                curr_length = 0
                while curr_length < l and curr_length <= 5:
                    curr_index += 1
                    curr_length += 1
                    cards += CARD_RANK_STR[curr_index] * 3

                    # trio_chain_2 to trio_chain_5, only when the player can finish it
                    if curr_length >= 2 and curr_length <= 5:
                        if hands_count == 3*curr_length:
                            playable_cards.add(cards)

                    # trio_solo_chain_2 to trio_solo_chain_4, only when the player can finish it
                    if curr_length >= 2 and curr_length <= 4:
                        if hands_count == 4*curr_length:
                            for left, right in PaodekuaiJudger.solo_attachments(current_hand, s, curr_length,
                                                                                curr_length):
                                pre_attached = ''
                                for j in left:
                                    pre_attached += CARD_RANK_STR[j]
                                post_attached = ''
                                for j in right:
                                    post_attached += CARD_RANK_STR[j]
                                playable_cards.add(pre_attached + cards + post_attached)

                    # trio_2*solo_chain2 -- trio_2*solo_chain_4
                    if curr_length >= 2 and curr_length <= 4:
                        for left, right in PaodekuaiJudger.solo_attachments(current_hand, s, curr_length, curr_length*2):
                            pre_attached = ''
                            for j in left:
                                pre_attached += CARD_RANK_STR[j]
                            post_attached = ''
                            for j in right:
                                post_attached += CARD_RANK_STR[j]
                            playable_cards.add(pre_attached + cards + post_attached)
                l -= 1
                s += 1

        # bomb_solo_chain
        for i in more_than_3_indexes:
            if hands_count <= 7:
                playable_cards.add(current_hand)
            rest = list(current_hand.replace(CARD_RANK_STR[i[0]]*4, ''))
            others = set(combinations(rest, 3))
            for other in others:
                new = CARD_RANK_STR[i[0]]*4
                for rank in other:
                    new += rank
                playable_cards.add(sort_card_rank(new))

        return playable_cards

    def __init__(self, players, np_random):
        ''' Initilize the Judger class for Dou Dizhu
        '''
        self.playable_cards = [set() for _ in range(3)]
        self._recorded_removed_playable_cards = [[] for _ in range(3)]
        for player in players:
            player_id = player.player_id
            current_hand = cards2str(player.current_hand)
            # according to the game rule, generate all legal actions without comparison
            # the true legal actions are given directly by 'get_gt_cards' in pdkutils
            self.playable_cards[player_id] = self.playable_cards_from_hand(current_hand)

    def calc_playable_cards(self, player):
        """ Recalculate all legal cards the player can play according to his
        current hand.

        Args:
            player (PaodekuaiPlayer object): object of PaodekuaiPlayer
            init_flag (boolean): For the first time, set it True to accelerate
              the preocess.

        Returns:
            list: list of string of playable cards
        """

        player_id = player.player_id
        # old playable cards
        playable_cards = self.playable_cards[player_id].copy()

        # this current_hand is updated after action ,so it's different from old_playable_cards
        current_hand = cards2str(player.current_hand)

        current_legal = self.playable_cards_from_hand(current_hand)
        removed_playable_cards = list(playable_cards.difference(current_legal))
        self.playable_cards[player_id] = current_legal
        self._recorded_removed_playable_cards[player_id].append(removed_playable_cards)

        return self.playable_cards[player_id]

        # player_id = player.player_id
        # removed_playable_cards = []
        # missed = None
        # for single in player.singles:
        #     if single not in current_hand:
        #         missed = single
        #         break
        #
        # playable_cards = self.playable_cards[player_id].copy()
        # print("before:")
        # print(playable_cards)
        # if missed is not None:
        #     position = player.singles.find(missed)
        #     player.singles = player.singles[position + 1:]
        #     for cards in playable_cards:
        #         if missed in cards or (not contains_cards(current_hand, cards)):
        #             removed_playable_cards.append(cards)
        #             self.playable_cards[player_id].remove(cards)
        # else:
        #     for cards in playable_cards:
        #         if not contains_cards(current_hand, cards):
        #             # del self.playable_cards[player_id][cards]
        #             removed_playable_cards.append(cards)
        #             self.playable_cards[player_id].remove(cards)
        # self._recorded_removed_playable_cards[player_id].append(removed_playable_cards)
        # print('removed:')
        # print(self._recorded_removed_playable_cards[player_id])
        # print(self.playable_cards[player_id])
        # return self.playable_cards[player_id]

    def restore_playable_cards(self, player_id):
        ''' restore playable_cards for judger for game.step_back().

        Args:
            player_id: The id of the player whose playable_cards need to be restored
        '''
        removed_playable_cards = self._recorded_removed_playable_cards[player_id].pop()
        self.playable_cards[player_id].update(removed_playable_cards)

    def get_playable_cards(self, player):
        ''' Provide all legal cards the player can play according to his
        current hand.

        Args:
            player (PaodekuaiPlayer object): object of PaodekuaiPlayer
            init_flag (boolean): For the first time, set it True to accelerate
              the preocess.

        Returns:
            list: list of string of playable cards
        '''
        return self.playable_cards[player.player_id]

    @staticmethod
    def judge_game(players, player_id):
        ''' Judge whether the game is over

        Args:
            players (list): list of PaodekuaiPlayer objects
            player_id (int): integer of player's id

        Returns:
            (bool): True if the game is over
        '''
        player = players[player_id]
        if not player.current_hand:
            return True
        return False

    @staticmethod
    def judge_payoffs(winner_id):
        payoffs = np.array([0, 0, 0])
        if winner_id != None:
            payoffs[winner_id] = 1
        # if winner_id == landlord_id:
        #     payoffs[landlord_id] = 1
        # else:
        #     for index, _ in enumerate(payoffs):
        #         if index != landlord_id:
        #             payoffs[index] = 1
        return payoffs

# def playable_cards_from_hand(current_hand):
#     playable_cards = set()
#     for cards in FIXED_LIST:
#         if cards in current_hand:
#             playable_cards.add(cards)
#     for abstract_cards, main_part in FLEXIBLE_LIST:
#         if len(abstract_cards) >= len(current_hand):
#             playable_cards.add(current_hand)
#         elif main_part in current_hand:
#             rest = current_hand.replace(main_part, '')
#             uncertain = abstract_cards.count("*")
#             others = set(combinations(rest, uncertain))
#             for other in others:
#                 new = main_part
#                 for card in other:
#                     new += card
#                 playable_cards.add(sort_card(new))
#     return playable_cards


# if __name__ is 'main':
#     import time
#     from tqdm import tqdm
#     current_hand = '444455567888999TTT'
#     start_time = time.time()
#     for i in tqdm(range(10000)):
#         PaodekuaiJudger.playable_cards_from_hand(current_hand)
#
#     end_time = time.time()
#
#     print('Time={}'.format(end_time - start_time))

