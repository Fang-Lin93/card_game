import pandas as pd
import numpy as np
import json
import joblib
from tqdm import tqdm
from pdkutils import visual_cards, CARD_RANK_STR, CARD_TYPE, CARD_RANK_STR_INDEX, TYPE_CARD
from collections import OrderedDict

DATA_PATH = '/Users/fanglinjiajie/locals/datasets/CardData/'
ORDER = '3456789TJQKA2'
CLASSES = list(TYPE_CARD.keys())

DATA = pd.read_csv(DATA_PATH + 'clean_pdk.csv', dtype=str).fillna('')


# ======================== Data processing ========================
# data cleaning

def clean_data():
    # only consider three-people game
    with open(DATA_PATH + 'three.csv', 'r') as file:
        three_game = json.load(file)
    data = pd.read_csv(DATA_PATH + 'paodekuai.csv', dtype=str).fillna('')
    data['table_turn_id'] = data['tableid'] + '_' + data['turn']
    data = data[['table_turn_id', 'userid', 'play', 'remains']]
    data['play'] = data['play'].apply(numbers2cards)
    data['remains'] = data['remains'].apply(numbers2cards)
    data = data[data['table_turn_id'].isin(three_game)]
    data.to_csv(DATA_PATH + 'clean_pdk.csv', index=False)


def data_play_record():
    # select winners
    with open(DATA_PATH + 'winner.csv', 'r') as file:
        game_winner = json.load(file)
    winners = {}
    for table, winner in game_winner:
        winners[table] = winner

    # select pro players
    # rank_player = pd.read_csv(DATA_PATH + 'rank.csv', dtype=str)
    # rank_player = rank_player.loc[:200, :]
    # rank_player = list(rank_player[rank_player['累计赢率'] > '0.4']['用户'])

    # read game data
    data = DATA.copy()
    data_play = OrderedDict()
    game_idx = None

    for i in tqdm(data.index):

        # New game, reset memories
        if game_idx != data['table_turn_id'][i]:
            game_idx = data['table_turn_id'][i]
            memory_play = [''] * 3
            memory_hands = {}
            played_cards = ''


        usr_id = data['userid'][i]
        remains = data['remains'][i]
        action = data['play'][i]

        #
        if usr_id in memory_hands:
            memory_hands.pop(usr_id)

        # Record only pro player
        # if usr_id in rank_player:

        # Select winning games
        if winners[game_idx] == usr_id:

            if usr_id not in data_play:
                data_play[usr_id] = []

            # if action is not pass, record the [obs,action] pair
            if action:
                others_hand = ''
                for cards in memory_hands.values():
                    others_hand += cards

                current_hand = sort_card(remains + action)
                others_hand = sort_card(others_hand)
                obs = [current_hand, others_hand] + memory_play + [played_cards]
                data_play[usr_id] += [[obs, action]]

                # check data
                if set(current_hand + others_hand + played_cards) != set(
                        '3333444455556666777788889999TTTTJJJJQQQQKKKKAAA2'):
                    print(usr_id)
                    raise ValueError('Cards are not coincident')

        # update memories, left is new, right is old
        memory_play.pop()
        memory_play = [action] + memory_play
        memory_hands[usr_id] = remains
        played_cards += action

    with open(DATA_PATH + 'data_play_record_win.csv', 'w') as file:
        json.dump(data_play, file)


def sl_data_str_tensor():
    with open(DATA_PATH + 'data_play_record_win.csv', 'r') as file:
        data = json.load(file)

    behaviors = []
    # each record correspoonds to one player
    for record in data.values():
        behaviors += record

    data_x = []
    data_y = []
    for state, action in tqdm(behaviors):
        state_tensor = []
        for obs in state:
            state_tensor.append(cards_encode_tensor(obs))
        data_x.append(np.array(state_tensor))
        data_y.append(cards_encode_tensor(action))

    np.save(DATA_PATH + 'card_tensor_data_x_win', np.array(data_x))
    np.save(DATA_PATH + 'card_tensor_data_y_win', np.array(data_y))

# ============================== utils functions ==============================


def sort_card(cards):
    """
    i.e. '43592TAK' -> return '3459TKA2'
    :param cards: (str) of cards
    :return:
    """
    order = '3456789TJQKA2'
    res = ''
    candid = list(cards)
    for card in order:
        while card in candid:
            res += card
            candid.remove(card)
    return res


def type_one_hot(card_type):
    res = np.zeros(len(CLASSES))
    res[CLASSES.index(card_type)] = 1
    return res


# numbers in data to cards
def numbers2cards(numbers):
    res = ''
    if numbers:
        numbers = numbers.split(sep=',')
        for number in numbers:
            if number[1:] == '10':
                res += 'T'
            elif number[1:] == '11':
                res += 'J'
            elif number[1:] == '12':
                res += 'Q'
            elif number[1:] == '13':
                res += 'K'
            elif number[1:] == '14':
                res += 'A'
            elif number[1:] == '16':
                res += '2'
            else:
                res += number[-1]
    return sort_card(res)


# cards to 4*13 matrix
def cards_encode_tensor(cards):
    plane = np.zeros((4, 13))
    if not cards:
        return plane
    cards_pool = list(cards)
    layer = 0
    while cards_pool:
        set_cards = set(cards_pool)
        for card in set_cards:
            idx = CARD_RANK_STR.index(card)
            plane[layer][idx] = 1
            cards_pool.remove(card)
        layer += 1
    return plane


# cards to 13-dim vector
def cards_encode_vector(cards_str):
    cards = list(cards_str)
    vec = np.zeros(13)
    for card in CARD_RANK_STR:
        if card in cards:
            vec[CARD_RANK_STR_INDEX[card]] = cards.count(card)
    return vec


# def check_data_play(data_play):
#     errors = []
#     for x, y in data_play:
#         if isinstance(y, str):
#             cards = y.split(sep=',')
#             for card in cards:
#                 if card not in x:
#                     print(x)
#                     print(y)
#                     errors += 1
#         else:
#             errors += [[x, y]]
#     print(f'Errors: {len(errors)}')
#     return errors

#
# def get_initial_data():
#     data_play = data_play_record()
#     if not check_data_play(data_play):
#         clean_data = []
#         for x, y in data_play:
#             clean_data += [[numbers2cards(x), numbers2cards(y)]]
#         with open('initial_play.csv', 'w') as file:
#             json.dump(clean_data, file)
#     else:
#         print('Data Error')
#     return data_play
#
#
# def prepare_data_type():
#     with open('initial_play.csv', 'r') as file:
#         pre_data = json.load(file)
#         data_X, data_Y = [], []
#         for x, y in tqdm(pre_data):
#             if y in CARD_TYPE[0].keys():
#                 card_type = CARD_TYPE[0][y][0][0]
#                 data_X += [cards_encode_vector(x)]
#                 data_Y += [type_one_hot(card_type)]
#             # else:
#             #     print(y)
#     return np.array(data_X), np.array(data_Y)
#
#
# def prepare_data_cards():
#     with open('initial_play.csv', 'r') as file:
#         pre_data = json.load(file)
#         data_X, data_Y = [], []
#         for x, y in tqdm(pre_data):
#             data_X += [cards_encode_vector(x)]
#             data_Y += [cards_encode_tensor(y).reshape(13*4)]
#     return np.array(data_X), np.array(data_Y)
#

# if __name__ is 'main':
    # clean_X, clean_y = prepare_data_cards()
    #
    # X_train, X_test, y_train, y_test = train_test_split(clean_X, clean_y, test_size=0.33, random_state=0)
    #
    # clf = RandomForestRegressor(max_depth=10, random_state=0)
    # clf.fit(X_train, y_train)
    # clf.score(X_train, y_train)
    # clf.score(X_test, y_test)
    #
    # clf.fit(clean_X, clean_y)
    # joblib.dump(clf, 'randomforest.pkl')
    # get_clf = joblib.load('randomforest.pkl')
