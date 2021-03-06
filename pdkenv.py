import numpy as np
# from rlcard.utils import *
from utils import *
from pdkutils import CARD_TYPE
import seeding

DEFAULT_CONFIG = {
    'allow_step_back': False,
    'allow_raw_data': True,
    'single_agent_mode': False,
    'active_player': 0,  # the player that is human or training agent
    'record_action': True,
    'seed': None,
    'env_num': 1,
}
BOMB = ['3' * 4, '4' * 4, '5'* 4, '6'* 4, '7'* 4, '8'* 4, '9'* 4, 'T'* 4, 'J'* 4, 'Q'* 4, 'K'* 4, 'A'* 3]


class Env(object):
    """
    The base Env class. For all the environments in RLCard,
    we should base on this class and implement as many functions
    as we can.
    """

    def __init__(self, config):
        ''' Initialize the environment

        Args:
            config (dict): A config dictionary. All the fields are
                optional. Currently, the dictionary includes:
                'seed' (int) - A environment local random seed.
                'env_num' (int) - If env_num>1, the environemnt wil be run
                  with multiple processes. Note the implementatino is
                  in `vec_env.py`.
                'allow_step_back' (boolean) - True if allowing
                 step_back.
                'allow_raw_data' (boolean) - True if allow
                 raw obs in state['raw_obs'] and raw legal actions in
                 state['raw_legal_actions'].
                'single_agent_mode' (boolean) - True if single agent mode,
                 i.e., the other players are pretrained models.
                'active_player' (int) - If 'singe_agent_mode' is True,
                 'active_player' specifies the player that does not use
                  pretrained models.
                There can be some game specific configurations, e.g., the
                number of players in the game. These fields should start with
                'game_', e.g., 'game_player_num' we specify the number of
                players in the game. Since these configurations may be game-specific,
                The default settings shpuld be put in the Env class. For example,
                the default game configurations for Blackjack should be in
                'rlcard/envs/blackjack.py'
                TODO: Support more game configurations in the future.
        '''
        self.allow_step_back = self.game.allow_step_back = config['allow_step_back']
        self.allow_raw_data = config['allow_raw_data']
        self.record_action = config['record_action']
        self.trajectories = None
        if self.record_action:
            self.action_recorder = []


        # Game specific configurations
        # Currently only support blackjack
        # TODO support game configurations for all the games
        # supported_envs = ['paodekuai']
        # if self.name in supported_envs:
        #     _game_config = self.default_game_config.copy()
        #     for key in config:
        #         if key in _game_config:
        #             _game_config[key] = config[key]
        #     self.game.configure(_game_config)

        # Get the number of players/actions in this game
        self.player_num = self.game.get_player_num()
        self.action_num = self.game.get_action_num()

        # initialize reward and cumulative reward
        self.reward_recoder = None
        self.cum_reward = {}
        for i in range(self.player_num):
            self.cum_reward[i] = 0


        # A counter for the timesteps
        self.timestep = 0

        # Modes
        self.single_agent_mode = config['single_agent_mode']
        self.active_player = config['active_player']

        # Load pre-trained models if single_agent_mode=True
        if self.single_agent_mode:
            self.model = self._load_model()
            # If at least one pre-trained agent needs raw data, we set self.allow_raw_data = True
            for agent in self.model.agents:
                if agent.use_raw:
                    self.allow_raw_data = True
                    break

        # Set random seed, default is None
        self._seed(config['seed'])

    def reset(self):
        '''
        Reset environment in single-agent mode
        Call `_init_game` if not in single agent mode
        '''
        if not self.single_agent_mode:
            return self._init_game()

        while True:
            state, player_id = self.game.init_game()
            while not player_id == self.active_player:
                self.timestep += 1
                action, _ = self.model.agents[player_id].eval_step(self._extract_state(state))
                # if not self.model.agents[player_id].use_raw:
                #     action = self._decode_action(action)
                state, player_id = self.game.step(action)

            if not self.game.is_over():
                break

        return self._extract_state(state)

    def step(self, action, raw_action=False):
        ''' Step forward

        Args:
            action : The action taken by the current player, check game cls!!
            raw_action (boolean): True if the action is a raw action

        Returns:
            (tuple): Tuple containing:

                (dict): The next state
                (int): The ID of the next player
        '''
        # if not raw_action:
        #     action = self._decode_action(action)
        if self.single_agent_mode:
            return self._single_agent_step(action)

        self.timestep += 1
        # Record the action for human interface
        if self.record_action:
            self.action_recorder.append([self.get_player_id(), action])
        next_state, player_id = self.game.step(action)

        # return the extracted state, not the raw state
        return self._extract_state(next_state), player_id

    def step_back(self):
        """ Take one step backward.

        Returns:
            (tuple): Tuple containing:

                (dict): The previous state
                (int): The ID of the previous player

        Note: Error will be raised if step back from the root node.
        """
        if not self.allow_step_back:
            raise Exception('Step back is off. To use step_back, please set allow_step_back=True')

        if not self.game.step_back():
            return False

        player_id = self.get_player_id()
        state = self.get_state(player_id)

        return state, player_id

    def set_agents(self, agents):
        """
        Set the agents that will interact with the environment.
        This function must be called before `run`.

        Args:
            agents (list): List of Agent classes
        """
        if self.single_agent_mode:
            raise ValueError('Setting agent in single agent mode or human mode is not allowed.')

        self.agents = agents
        # If at least one agent needs raw data, we set self.allow_raw_data = True
        for agent in self.agents:
            if agent.use_raw:
                self.allow_raw_data = True
                break

    def run(self, is_training=False):
        '''
        Run a complete game, either for evaluation or training RL agent.

        Args:
            is_training (boolean): True if for training purpose.

        Returns:
            (tuple) Tuple containing:

                (list): A list of trajectories generated from the environment.
                (list): A list payoffs. Each entry corresponds to one player.

        Note: The trajectories are 3-dimension list. The first dimension is for different players.
              The second dimension is for different transitions. The third dimension is for the contents of each transition
              The n-th transition means the n-th turn of such player
        '''
        # The initial defined trajectories
        if self.single_agent_mode:
            raise ValueError('Run in single agent not allowed.')

        # The initial state
        trajectories = [[] for _ in range(self.player_num)]
        state, player_id = self.reset()

        # Loop to play the game
        # Here trajectories[player_id] = self: state-action-state-action-...(or, if you get reward?)
        trajectories[player_id].append(state)
        reward_seq = []
        recorder = [[] for _ in range(self.player_num)]
        while not self.is_over():
            # Agent plays
            if not is_training:
                action, _ = self.agents[player_id].eval_step(state)
            else:
                action = self.agents[player_id].step(state)

            # Save action
            trajectories[player_id].append(action)

            # record this action and state for future reward calculation
            recorder[player_id] = [state, action]

            # Environment steps
            next_state, next_player_id = self.step(action, self.agents[player_id].use_raw)

            # Set the state and player
            state = next_state
            player_id = next_player_id

            # Save state.
            if not self.game.is_over(): # reward R(t+1) and state S(t+1) are jointly determined

                # Save immediate reward, which is not the reward in RL sense(since env hasn't been done!)
                if recorder[player_id]:
                    old_state, old_action = recorder[player_id]
                    reward = self.transition_reward(old_state, old_action, state, player_id)
                    reward_seq += [[player_id, reward]]
                    trajectories[player_id].append(reward)
                # Save state.
                trajectories[player_id].append(state)

            winner = player_id
        # Add a final state to all the players, so all players get finals!
        for i in range(self.player_num):
            player_id = (winner + i) % self.player_num
            state = self.get_state(player_id)

            if recorder[player_id]:
                old_state, old_action = recorder[player_id]
                reward = self.transition_reward(old_state, old_action, state, player_id)
                reward_seq += [[player_id, reward]]
                trajectories[player_id].append(reward)

            trajectories[player_id].append(state)

        # Final Payoffs
        #    reward_seq += [self.get_payoffs()]

        # Reorganize the trajectories
        #  trajectories = reorganize(trajectories, reward_seq)
        # reorganized to transitions
        trajectories = paodekuai_reorganize(trajectories)
        self.reward_recoder = reward_seq
        self.trajectories = trajectories
        return trajectories, reward_seq

    def is_over(self):
        ''' Check whether the curent game is over

        Returns:
            (boolean): True if current game is over
        '''
        return self.game.is_over()

    def get_player_id(self):
        ''' Get the current player id

        Returns:
            (int): The id of the current player
        '''
        return self.game.get_player_id()

    def get_state(self, player_id):
        ''' Get the state given player id

        Args:
            player_id (int): The player id

        Returns:
            (numpy.array): The observed state of the player
        '''
        return self._extract_state(self.game.get_state(player_id))

    def get_payoffs(self):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            (list): A list of payoffs for each player.

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError

    def transition_reward(self, state, action, next_state, player_id):
        ''' Get the reward of players. Must be implemented in the child class.

        Returns:
            (number)

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        self.game.np_random = self.np_random
        return seed

    def _init_game(self):
        ''' Start a new game

        Returns:
            (tuple): Tuple containing:

                (numpy.array): The begining state of the game
                (int): The begining player
        '''
        state, player_id = self.game.init_game()
        if self.record_action:
            self.action_recorder = []
        return self._extract_state(state), player_id

    def _load_model(self):
        ''' Load pretrained/rule model

        Returns:
            model (Model): A Model object
        '''
        raise NotImplementedError

    def _extract_state(self, state):
        ''' Extract useful information from state for RL. Must be implemented in the child class.

        Args:
            state (dict): The raw state

        Returns:
            (numpy.array): The extracted state
        '''
        raise NotImplementedError

    def _decode_action(self, action_id):
        """ Decode Action id to the action in the game.

        Args:
            action_id (int): The id of the action

        Returns:
            (string): The action that will be passed to the game engine.

        Note: Must be implemented in the child class.
        """
        raise NotImplementedError

    def _get_legal_actions(self):
        ''' Get all legal actions for current state.

        Returns:
            (list): A list of legal actions' id.

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError

    def _single_agent_step(self, action):
        ''' Step forward for human/single agent

        Args:
            action (int): The action takem by the current player

        Returns:
            next_state (numpy.array): The next state
        '''
        reward = 0.
        done = False
        self.timestep += 1
        state, player_id = self.game.step(action)
        while not self.game.is_over() and not player_id == self.active_player:
            self.timestep += 1
            action, _ = self.model.agents[player_id].eval_step(self._extract_state(state))
            # if not self.model.agents[player_id].use_raw:
            #     action = self._decode_action(action)
            state, player_id = self.game.step(action)

        if self.game.is_over():
            reward = self.get_payoffs()[self.active_player]
            done = True
            state = self.reset()
            return state, reward, done

        return self._extract_state(state), reward, done

    @staticmethod
    def init_game():
        ''' (This function has been replaced by `reset()`)
        '''
        raise ValueError('init_game is removed. Please use env.reset()')


class PaodekuaiEnv(Env):
    """ Paodekuai Environment
    """

    def __init__(self, config):
        from pdkutils import SPECIFIC_MAP, CARD_RANK_STR
        from pdkutils import ACTION_LIST, ACTION_SPACE
        from pdkutils import encode_cards, visual_cards
        from pdkutils import cards2str, cards2str_with_suit
        from pdkgame import PaodekuaiGame as Game

        _config = DEFAULT_CONFIG.copy()
        for key in config:
            _config[key] = config[key]

        self._encode_cards = encode_cards
        self._cards2str = cards2str
        self._cards2str_with_suit = cards2str_with_suit
        self._SPECIFIC_MAP = SPECIFIC_MAP
        self._CARD_RANK_STR = CARD_RANK_STR
        self._ACTION_LIST = ACTION_LIST
        self._ACTION_SPACE = ACTION_SPACE

        self.name = 'paodekuai'
        self.game = Game()
        super(PaodekuaiEnv, self).__init__(_config)
        self.state_shape = [6, 4, 13]

    def _extract_state(self, state):
        ''' Encode state

        Args:
            state (dict): dict of original state

        Returns:
            numpy array: 6*4*13 array
                         6 : current hand
                             the union of the other two players' hand
                             the recent three actions
                             the union of all played cards
        '''
        obs = np.zeros((6, 4, 13), dtype=int)
        # for index in range(6):
        #     obs[index][0] = np.ones(13, dtype=int)
        self._encode_cards(obs[0], state['current_hand'])
        self._encode_cards(obs[1], state['others_hand'])
        # trace: from old to new, so the old is put in the bottom layer
        for i, action in enumerate(state['trace'][-3:]):
            if action[1] != 'pass':
                self._encode_cards(obs[4 - i], action[1])
        if state['played_cards'] is not None:
            self._encode_cards(obs[5], state['played_cards'])

        extracted_state = {'obs': obs, 'legal_actions': self.game.state['actions']}  # self._get_legal_actions_id()
        if self.allow_raw_data:
            extracted_state['raw_obs'] = state
            # TODO: state['actions'] can be None, may have bugs
            # if state['actions'] == None:
            #     extracted_state['raw_legal_actions'] = []
            # else:
            #     extracted_state['raw_legal_actions'] = [a for a in state['actions']]
        if self.record_action:
            extracted_state['action_record'] = self.action_recorder
        return extracted_state

    def get_payoffs(self):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            payoffs (list): a list of payoffs for each player
        '''
        return self.game.judger.judge_payoffs(self.game.winner_id)

    def transition_reward(self, state, action, next_state, player_id):
        ''' Get the reward of players. Must be implemented in the child class.

        state:  extracted RL state
        Returns:
            payoffs (list): a list of payoffs for each player
        '''
        reward = 0
        # be careful of the initial win!
        if len(next_state['raw_obs']['trace']) >= 2:
            if next_state['raw_obs']['trace'][-1][1] in BOMB:
                reward -= 10
            if len(next_state['raw_obs']['trace']) >= 3:
                if next_state['raw_obs']['trace'][-2][1] in BOMB:
                    reward -= 10

        if action != 'pass' and action in BOMB:
                reward += 20

        if self.game.is_over():
            if self.game.winner_id == player_id:
                reward += len(next_state['raw_obs']['others_hand'])
            else:
                current_count = len(next_state['raw_obs']['current_hand'])
                if current_count != 1:
                    reward -= current_count

        self.cum_reward[player_id] += reward
        return reward
        # return int(self.game.winner_id == player_id)

    def _decode_action(self, action_id):
        ''' Action id -> the action in the game. Must be implemented in the child class.

        Args:
            action_id (int): the id of the action

        Returns:
            action (string): the action that will be passed to the game engine.
        '''
        return action_id

    def get_summary(self):

        from pdkutils import visual_cards

        for player in self.game.players:
            print('==========Initial Hands: Player_{}==========='.format(player.player_id))
            visual_cards(player.initial_hand)

        print('========== Winner ==========')
        print('Player_{}'.format(self.game.winner_id))

        print('==========Actions Trace===========')
        time_step = 1
        for action, reward in zip(self.game.state['trace'], self.reward_recoder):
            print(f'Step_{time_step}')
            print('     ' + 'Player_{}:'.format(action[0]))
            print('     ' + 'Action: ' + action[1])
            print('     ' + 'Reward: ' + str(reward[1]))
            time_step += 1

        # abstract_action = self._ACTION_LIST[action_id]
        # # without kicker
        # if '*' not in abstract_action:
        #     return abstract_action
        # # with kicker
        # legal_actions_id = self.game.state['actions']
        # specific_actions = []
        # kickers = []
        # for legal_action in legal_actions_id:
        #     for abstract in self._SPECIFIC_MAP[legal_action]:
        #         main = abstract.strip('*')
        #         if abstract == abstract_action:
        #             specific_actions.append(legal_action)
        #             kickers.append(legal_action.replace(main, '', 1))
        #             break
        # # choose kicker with minimum score
        # player_id = self.game.get_player_id()
        # kicker_scores = []
        # for kicker in kickers:
        #     score = 0
        #     for action in self.game.judger.playable_cards[player_id]:
        #         if kicker in action:
        #             score += 1
        #     kicker_scores.append(score + self._CARD_RANK_STR.index(kicker[0]))
        # min_index = 0
        # min_score = kicker_scores[0]
        # for index, score in enumerate(kicker_scores):
        #     if score < min_score:
        #         min_score = score
        #         min_index = index
        # return specific_actions[min_index]

    def _get_legal_actions_id(self):
        ''' Get all legal actions for current state

        Returns:
            legal_actions_id (list): a list of legal actions' id
        '''
        legal_action_id = []
        legal_actions = self.game.state['actions']
        if legal_actions:
            for action in legal_actions:
                for abstract in self._SPECIFIC_MAP[action]:
                    action_id = self._ACTION_SPACE[abstract]
                    if action_id not in legal_action_id:
                        legal_action_id.append(action_id)

        return legal_action_id

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        state = {}
        state['hand_cards_with_suit'] = [self._cards2str_with_suit(player.current_hand) for player in self.game.players]
        state['hand_cards'] = [self._cards2str(player.current_hand) for player in self.game.players]
        # state['landlord'] = self.game.state['landlord']
        state['trace'] = self.game.state['trace']
        state['current_player'] = self.game.round.current_player
        state['legal_actions'] = self.game.state['actions']
        return state


if __name__ == '__main__':
    from agents.random_agent import RandomAgent
    from agents.human_agent import HumanAgent

    env = PaodekuaiEnv(config={'record_action': True})
    random_agent = RandomAgent(env.action_num)
    human_agent = HumanAgent()
    env.set_agents([random_agent, random_agent, random_agent])

    trajectories, payoffs = env.run(is_training=False)
