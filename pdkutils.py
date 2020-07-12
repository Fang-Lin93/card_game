''' Paodekuai utils
'''

import os
import json
import numpy as np
from collections import OrderedDict
import threading
import collections
from pdkcore import Card

# Read required docs
ROOT_PATH = os.getcwd()

# a map of action to abstract action
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_specific_map.json'), 'r') as file:
    SPECIFIC_MAP = json.load(file, object_pairs_hook=OrderedDict)

# a map of abstract action to its index and a list of abstract action
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_action_space.json'), 'r') as file:
    ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
    ACTION_LIST = list(ACTION_SPACE.keys())

# a map of card to its type. Also return both dict and list to accelerate
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_card_type.json'), 'r') as file:
    data = json.load(file, object_pairs_hook=OrderedDict)
    CARD_TYPE = (data, list(data), set(data))

# a map of type to its cards
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_type_card.json'), 'r') as file:
    TYPE_CARD = json.load(file, object_pairs_hook=OrderedDict)

# rank list of solo character of cards
CARD_RANK_STR = ['3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K',
                 'A', '2']  # , 'B', 'R']
CARD_RANK_STR_INDEX = {'3': 0, '4': 1, '5': 2, '6': 3, '7': 4,
                       '8': 5, '9': 6, 'T': 7, 'J': 8, 'Q': 9,
                       'K': 10, 'A': 11, '2': 12}  # , 'B': 13, 'R': 14}
# rank list
CARD_RANK = ['3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K',
             'A', '2']  # , 'B', 'R']

INDEX = {'3': 0, '4': 1, '5': 2, '6': 3, '7': 4,
         '8': 5, '9': 6, 'T': 7, 'J': 8, 'Q': 9,
         'K': 10, 'A': 11, '2': 12}  # , 'B': 13, 'R': 14}
INDEX = OrderedDict(sorted(INDEX.items(), key=lambda t: t[1]))


def init_54_deck():
    ''' Initialize a standard deck of 52 cards, BJ and RJ

    Returns:
        (list): Alist of Card object
    '''
    suit_list = ['S', 'H', 'D', 'C']
    rank_list = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    res = [Card(suit, rank) for suit in suit_list for rank in rank_list]
    res.append(Card('BJ', ''))
    res.append(Card('RJ', ''))
    return res


def init_48_deck():
    """Initialize 48 cards for Paodekuai
    :return:
    """
    suit_list = ['S', 'H', 'D', 'C']
    rank_list = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    valid_cards = [suit + rank for suit in suit_list for rank in rank_list]
    del_set = ['H2', 'C2', 'D2', 'SA']
    for card in del_set:
        valid_cards.remove(card)
    res = [Card(card[0], card[1]) for card in valid_cards]
    return res


def get_upstream_player_id(player, players):
    ''' Obtain the upsteam player's player_id

    Args:
        player (Player): The current player
        players (list): A list of players

    Note: This function assumes player_id(s) in 'players' list starts from 0, and are consequent.
    '''
    return (player.player_id - 1) % len(players)


def get_downstream_player_id(player, players):
    ''' Obtain the downsteam player's player_id

    Args:
        player (Player): The current player
        players (list): A list of players

    Note: This function assumes player_id(s) in 'players' list start from 0, and are consequent.
    '''

    return (player.player_id + 1) % len(players)


def doudizhu_sort_str(card_1, card_2):
    ''' Compare the rank of two cards of str representation

    Args:
        card_1 (str): str representation of solo card
        card_2 (str): str representation of solo card

    Returns:
        int: 1(card_1 > card_2) / 0(card_1 = card2) / -1(card_1 < card_2)
    '''
    key_1 = CARD_RANK_STR.index(card_1)
    key_2 = CARD_RANK_STR.index(card_2)
    if key_1 > key_2:
        return 1
    if key_1 < key_2:
        return -1
    return 0


def paodekuai_sort_card(card_1, card_2):
    ''' Compare the rank of two cards of Card object

    Args:
        card_1 (object): object of Card
        card_2 (object): object of card
    '''
    key = []
    for card in [card_1, card_2]:
        # if card.rank == '':
        #     key.append(CARD_RANK.index(card.suit)) # if it's BJ or RJ
        # else:
        key.append(CARD_RANK.index(card.rank))
    if key[0] > key[1]:
        return 1
    if key[0] < key[1]:
        return -1
    return 0

def get_landlord_score(current_hand):
    ''' Roughly judge the quality of the hand, and provide a score as basis to
    bid landlord.

    Args:
        current_hand (str): string of cards. Eg: '56888TTQKKKAA222R'

    Returns:
        int: score
    '''
    score_map = {'A': 1, '2': 2, 'B': 3, 'R': 4}
    score = 0
    # rocket
    if current_hand[-2:] == 'BR':
        score += 8
        current_hand = current_hand[:-2]
    length = len(current_hand)
    i = 0
    while i < length:
        # bomb
        if i <= (length - 4) and current_hand[i] == current_hand[i + 3]:
            score += 6
            i += 4
            continue
        # 2, Black Joker, Red Joker
        if current_hand[i] in score_map:
            score += score_map[current_hand[i]]
        i += 1
    return score


def get_optimal_action(probs, legal_actions, np_random):
    ''' Determine the optimal action from legal actions
    according to the probabilities of abstract actions.

    Args:
        probs (list): list of probabilities of abstract actions
        legal_actions (list): list of legal actions

    Returns:
        str: optimal legal action
    '''
    abstract_actions = [SPECIFIC_MAP[action] for action in legal_actions]
    action_probs = []
    for actions in abstract_actions:
        max_prob = -1
        for action in actions:
            prob = probs[ACTION_SPACE[action]]
            if prob > max_prob:
                max_prob = prob
        action_probs.append(max_prob)
    optimal_prob = max(action_probs)
    optimal_actions = [legal_actions[index] for index,
                                                prob in enumerate(action_probs) if prob == optimal_prob]
    if len(optimal_actions) > 1:
        return np_random.choice(optimal_actions)
    return optimal_actions[0]


def cards2str_with_suit(cards):
    ''' Get the corresponding string representation of cards with suit

    Args:
        cards (list): list of Card objects

    Returns:
        string: string representation of cards
    '''
    return ' '.join([card.suit + card.rank for card in cards])


def cards2str(cards):
    ''' Get the corresponding string representation of cards

    Args:
        cards (list): list of Card objects

    Returns:
        string: string representation of cards
    '''
    response = ''
    for card in cards:
        if card.rank == '':
            response += card.suit[0]
        else:
            response += card.rank
    return response


class LocalObjs(threading.local):
    def __init__(self):
        self.cached_candidate_cards = None


_local_objs = LocalObjs()


def contains_cards(candidate, target):
    ''' Check if cards of candidate contains cards of target.

    Args:
        candidate (string): A string representing the cards of candidate
        target (string): A string representing the number of cards of target

    Returns:
        boolean
    '''
    # In normal cases, most continuous calls of this function
    #   will test different targets against the same candidate.
    # So the cached counts of each card in candidate can speed up
    #   the comparison for following tests if candidate keeps the same.
    if not _local_objs.cached_candidate_cards or _local_objs.cached_candidate_cards != candidate:
        _local_objs.cached_candidate_cards = candidate
        cards_dict = collections.defaultdict(int)
        for card in candidate:
            cards_dict[card] += 1
        _local_objs.cached_candidate_cards_dict = cards_dict
    cards_dict = _local_objs.cached_candidate_cards_dict
    if (target == ''):
        return True
    curr_card = target[0]
    curr_count = 1
    for card in target[1:]:
        if (card != curr_card):
            if (cards_dict[curr_card] < curr_count):
                return False
            curr_card = card
            curr_count = 1
        else:
            curr_count += 1
    if (cards_dict[curr_card] < curr_count):
        return False
    return True


def encode_cards(plane, cards):
    ''' Encode cards and represerve it into plane.

    Args:
        plane(2dim np.arrary with shape 4*13 for Paodekuai)
        cards (list or str): list or str of cards, every entry is a
    character of solo representation of card
    '''
    if not cards:
        return None
    cards_pool = list(cards)
    layer = 0
    while cards_pool:
        set_cards = set(cards_pool)
        for card in set_cards:
            idx = CARD_RANK_STR.index(card)
            plane[layer][idx] = 1
            cards_pool.remove(card)
        layer += 1

    #
    # layer = 1
    # if len(cards) == 1:
    #     rank = CARD_RANK_STR.index(cards[0])
    #     plane[layer][rank] = 1
    #     plane[0][rank] = 0
    # else:
    #     for index, card in enumerate(cards):
    #         if index == 0:
    #             continue
    #         if card == cards[index - 1]:
    #             layer += 1
    #         else:
    #             rank = CARD_RANK_STR.index(cards[index - 1])
    #             plane[layer][rank] = 1
    #             layer = 1
    #             plane[0][rank] = 0
    #     rank = CARD_RANK_STR.index(cards[-1])
    #     plane[layer][rank] = 1
    #     plane[0][rank] = 0


def visual_cards(plane):
    if plane is not None:
        if isinstance(plane, str):
            plane_new = np.zeros((4, 13), dtype=int)
            encode_cards(plane_new, plane)
            plane = plane_new

        if plane.shape != (4, 13):
            raise ValueError('Cards should be shape (4,13), other shapes detected')

        lines = [[] for _ in range(5)]
        for col in range(13):
            lines[0].append(' ' + CARD_RANK_STR[col])
            for row in range(4):
                if plane[row][col] == 0:
                    lines[row + 1].append(' ' + ' ')
                if plane[row][col] == 1:
                    lines[row + 1].append(' ' + '░')

        for line in lines:
            print('   '.join(line))


def gt_greater_cards_from_hands(current_hand, target_cards):
    """
    :param hands: (str) gives the candidate string hands
    :param others: (str) the hands to be compared, must be legal cards in the game
    :return:
    """
    from pdkjudger import PaodekuaiJudger
    gt_cards = []
    contains_legal = PaodekuaiJudger.playable_cards_from_hand(current_hand)
    target_types = CARD_TYPE[0][target_cards]
    type_dict = {}  # type_dict stores the target types which the player is trying to beat with
    # if cards can be multiply explained, choose the largest one
    for card_type, weight in target_types:  # e.g. [['plane_chain_3', '0'], ['plane_chain_3', '1'],...]
        if card_type in type_dict:
            if int(type_dict[card_type]) < int(weight):
                type_dict[card_type] = weight
        else:
            type_dict[card_type] = weight

    # if 'rocket' in type_dict:
    #     return gt_cards
    # type_dict['rocket'] = -1
    if 'bomb' not in type_dict:
        type_dict['bomb'] = -1
    for card_type, weight in type_dict.items():
        candidate = TYPE_CARD[card_type]
        for can_weight, cards_list in candidate.items():
            if int(can_weight) > int(weight):
                for cards in cards_list:
                    # TODO: improve efficiency
                    if cards not in gt_cards and cards in contains_legal:
                        # if self.contains_cards(current_hand, cards): \\\contains_cards(current_hand, cards)
                        gt_cards.append(cards)
    # add 'pass' to legal actions, if no bigger cards
    if not gt_cards:
        gt_cards += ['pass']
    return gt_cards


def get_gt_cards(player, greater_player):
    ''' Provide player's cards which are greater than the ones played by
    previous player in one round

    Args:
        player (PaodekuaiPlayer object): the player waiting to play cards
        greater_player (PaodekuaiPlayer object): the player who played current biggest cards.

    Returns:
        list: list of string of greater cards

    Note:
        1. return value contains 'pass' iff the player has no greater cards
    '''

    current_hand = cards2str(player.current_hand)
    target_cards = greater_player.played_cards

    return gt_greater_cards_from_hands(current_hand, target_cards)


def classify_actions(legal_actions):
    """
    :param legal_actions: list of strings: ['A', '33345',...]
    :return: a dict
    """
    classified_dic = OrderedDict()
    for action in legal_actions:
        for card_type, card_power in CARD_TYPE[0][action]:
            if card_type not in classified_dic:
                classified_dic[card_type] = [(action, card_power)]
            else:
                classified_dic[card_type] += [(action, card_power)]
    # sort the values by the card power
    for key in classified_dic.keys():
        classified_dic[key] = sorted(classified_dic[key], key=lambda x: int(x[1]))
    return classified_dic


def hands_islands(plane):
    """
    :param plane: given the card plane, return the number of the parts of the hands
    :return:
    """
    front_path = np.concatenate([[0], plane[0]])
    back_path = np.concatenate([plane[0], [0]])

    return sum(front_path > back_path)


def sort_card(cards):
    """
    i.e. '43592TAK' -> return '3459TKA2'
    :param cards: (str) of cards
    :return:
    """
    ORDER = '3456789TJQKA2'
    res = ''
    candid = list(cards)
    for card in ORDER:
        while card in candid:
            res += card
            candid.remove(card)
    return res


# Test json order
# if __name__ == '__main__':
#    for action, index in ACTION_SPACE.items():
#        if action != ACTION_LIST[index]:
#            ('order error')
