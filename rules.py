"""
This file create and save the rules given by Paodekuai,
The base actions are given by Paodekuai, we modify some actions
"""
import os
import json
import itertools
from collections import OrderedDict

ROOT_PATH = os.getcwd()

# a map of action to abstract action, '33345' is legal in Paodekuai, but illegal in Doudizhu
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_specific_map.json'), 'r') as file:
    SPECIFIC_MAP = json.load(file, object_pairs_hook=OrderedDict)

# a map of abstract action to its index and a list of abstract action
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_action_space.json'), 'r') as file:
    ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
    ACTION_LIST = list(ACTION_SPACE.keys())

# a map of card to its type. Also return both dict and list to accelerate
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_card_type.json'), 'r') as file:
    data_card_type = json.load(file, object_pairs_hook=OrderedDict)
    CARD_TYPE = (data_card_type, list(data_card_type), set(data_card_type))

# a map of type to its cards
with open(os.path.join(ROOT_PATH, 'jsondata/pdk_type_card.json'), 'r') as file:
    TYPE_CARD = json.load(file, object_pairs_hook=OrderedDict)

CARD_RANK_STR = ['3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K',
                 'A', '2']

CARD_RANK_STR_INDEX = {'3': 0, '4': 1, '5': 2, '6': 3, '7': 4,
                       '8': 5, '9': 6, 'T': 7, 'J': 8, 'Q': 9,
                       'K': 10, 'A': 11, '2': 12}


# create: ACTION_LIST -> ACTION_SPACE -> TYPE_CARD


def solo():
    res = OrderedDict()
    type_sets = OrderedDict()
    for i in range(len(CARD_RANK_STR)):
        type_sets[str(i)] = CARD_RANK_STR[i]
    res['solo'] = type_sets
    return res


def pair():
    res = OrderedDict()
    type_sets = OrderedDict()
    for i in range(len(CARD_RANK_STR[:-1])):
        type_sets[str(i)] = CARD_RANK_STR[i] * 2
    res['pair'] = type_sets
    return res


def pair_chain():
    deck = '3456789TJQKA'
    res = OrderedDict()
    for length in list(range(2, 9)):
        type_name = 'pair_chain_{}'.format(length)
        type_sets = OrderedDict()
        for i in range(0, len(deck) - length + 1):
            pairs = ''
            for card in deck[i: i + length]:
                pairs += card * 2
            type_sets[str(i)] = pairs
        res[type_name] = type_sets
    return res


def plane():
    res = OrderedDict()

    # plane_chain_1
    type_name = 'plane_chain_1'
    type_sets = OrderedDict()
    for card in CARD_RANK_STR[:-1]:
        orders = CARD_RANK_STR_INDEX[card]
        type_sets[str(orders)] = card * 3 + '**'
    res[type_name] = type_sets

    # plane_chain_2
    type_name = 'plane_chain_2'
    type_sets = OrderedDict()
    for cards in zip(CARD_RANK_STR, CARD_RANK_STR[1:]):
        if cards[-1] != '2':
            orders = CARD_RANK_STR_INDEX[cards[0]]
            type_sets[str(orders)] = cards[0] * 3 + cards[1] * 3 + '****'
    res[type_name] = type_sets

    # plane_chain_3
    type_name = 'plane_chain_3'
    type_sets = OrderedDict()
    for cards in zip(CARD_RANK_STR, CARD_RANK_STR[1:], CARD_RANK_STR[2:]):
        if cards[-1] != '2':
            orders = CARD_RANK_STR_INDEX[cards[0]]
            type_sets[str(orders)] = cards[0] * 3 + cards[1] * 3 + cards[2] * 3 + '******'
    res[type_name] = type_sets

    # plane_chain_4
    type_name = 'plane_chain_4'
    type_sets = OrderedDict()
    for cards in zip(CARD_RANK_STR, CARD_RANK_STR[1:], CARD_RANK_STR[2:], CARD_RANK_STR[3:]):
        if cards[-1] != '2':
            orders = CARD_RANK_STR_INDEX[cards[0]]
            type_sets[str(orders)] = cards[0] * 3 + cards[1] * 3 + cards[2] * 3 + cards[3] * 3 + '****'
    res[type_name] = type_sets

    # plane_chain_5
    type_name = 'plane_chain_5'
    type_sets = OrderedDict()
    for cards in zip(CARD_RANK_STR, CARD_RANK_STR[1:], CARD_RANK_STR[2:], CARD_RANK_STR[3:], CARD_RANK_STR[4:]):
        if cards[-1] != '2':
            orders = CARD_RANK_STR_INDEX[cards[0]]
            type_sets[str(orders)] = cards[0] * 3 + cards[1] * 3 + cards[2] * 3 + cards[3] * 3 + cards[4] * 3
    res[type_name] = type_sets

    return res


def solo_chain():
    deck = '3456789TJQKA'
    res = OrderedDict()
    for length in list(range(5, 13)):
        type_name = 'solo_chain_{}'.format(length)
        type_sets = OrderedDict()
        for i in range(0, len(deck) - length + 1):
            type_sets[str(i)] = deck[i: i + length]
        res[type_name] = type_sets
    return res


def bomb_solo_chain():
    res = OrderedDict()
    type_sets = OrderedDict()
    for i in range(len(CARD_RANK_STR[:-2])):
        type_sets[str(i)] = CARD_RANK_STR[i] * 4 + '***'
    type_sets[str(i+1)] = 'AAA***'
    res['bomb_solo_chain'] = type_sets
    return res


def bomb():
    res = OrderedDict()
    type_sets = OrderedDict()
    for i in range(len(CARD_RANK_STR[:-2])):
        type_sets[str(i)] = CARD_RANK_STR[i] * 4
    type_sets[str(i+1)] = 'AAA'
    res['bomb'] = type_sets
    return res


def sort_card_rank(cards):
    if isinstance(cards[0], int):
        return cards.sort()
    if isinstance(cards[0], str):
        cards_idx = [CARD_RANK_STR_INDEX[c] for c in cards]
        cards_idx.sort()
        res = ''
        for idx in cards_idx:
            res += CARD_RANK_STR[idx]
    return res


def abstract2cards(abstract):
    # e.g. '333**' to ['33334','33345',...]
    bombs = bomb()['bomb'].values()
    deck = '3333444455556666777788889999TTTTJJJJQQQQKKKKAAA2'
    stars = abstract.count('*')
    main_part = abstract.replace('*', '')
    res = []
    if stars != 0:
        # 0 permits 'JJJ', 1 permits '4JJJ', 2 permits '45JJJ'
        uncertains = list(range(stars+1))
        # if len(main_part) != 4:
        #     uncertains = {0, int(len(main_part) / 3), stars}
        # else:
        #     uncertains = {stars}
        for uncertain in uncertains:
            rest = deck.replace(main_part, '')
            others = set(itertools.combinations(rest, uncertain))
            for other in others:
                new = main_part
                for rank in other:
                    new += rank
                new = sort_card_rank(new)
                if new not in bombs:
                    res += [new]
        return res
    else:
        return [abstract]


def action_space():
    action_solo = list(solo()['solo'].values())
    action_pair = list(pair()['pair'].values())
    action_pair_chain = []
    action_plane = []
    action_solo_chain = []
    action_bomb_chain = []
    for type_name in pair_chain().values():
        action_pair_chain += list(type_name.values())
    for type_name in plane().values():
        action_plane += list(type_name.values())
    for type_name in solo_chain().values():
        action_solo_chain += list(type_name.values())
    for type_name in bomb_solo_chain().values():
        action_bomb_chain += list(type_name.values())

    action_bomb = list(bomb()['bomb'].values())
    total_actions = action_solo + action_pair + action_pair_chain + action_plane + action_solo_chain +\
                    action_bomb_chain + action_bomb + ['pass']
    actions = OrderedDict()
    for i, name in enumerate(total_actions):
        actions[name] = i
    return actions


def type_card():
    total_abstract = OrderedDict(**solo(), **pair(), **pair_chain(), **plane(),
                                 **solo_chain(), **bomb_solo_chain(), **bomb())
    for type_name in total_abstract.keys():
        for card_order in total_abstract[type_name].keys():
            total_abstract[type_name][card_order] = abstract2cards(total_abstract[type_name][card_order])

    return total_abstract


def card_type():
    type_order_card = type_card()
    res = OrderedDict()

    for type_name, type_dict in type_order_card.items():
        for card_order, cards in type_dict.items():
            for card in cards:
                if card in res.keys():
                    res[card] += [[type_name, card_order]]
                else:
                    res[card] = [[type_name, card_order]]
    return res


def create_jsons():
    ACTION_SPACE = action_space()
    ACTION_LIST = list(ACTION_SPACE.keys())
    with open(os.path.join(ROOT_PATH, 'jsondata/pdk_action_space.json'), 'w') as file:
        json.dump(ACTION_SPACE, file)

    abstract_cards = OrderedDict()
    for i in ACTION_LIST:
        abstract_cards[i] = abstract2cards(i)

    SPECIFIC_MAP = OrderedDict()
    for abstract, cards in abstract_cards.items():
        for card in cards:
            SPECIFIC_MAP[card] = [abstract]

    with open(os.path.join(ROOT_PATH, 'jsondata/pdk_specific_map.json'), 'w') as file:
        json.dump(SPECIFIC_MAP, file)

    CARD_TYPE = card_type()

    with open(os.path.join(ROOT_PATH, 'jsondata/pdk_card_type.json'), 'w') as file:
        json.dump(CARD_TYPE, file)

    TYPE_CARD = type_card()

    with open(os.path.join(ROOT_PATH, 'jsondata/pdk_type_card.json'), 'w') as file:
        json.dump(TYPE_CARD, file)



