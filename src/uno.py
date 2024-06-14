from enum import Enum
import random


class Color(Enum):
    RED = 'RED'
    GREEN = 'GREEN'
    BLUE = 'BLUE'
    YELLOW = 'YELLOW'
    ANY = 'ANY'


class Action(Enum):
    REVERSE = 'REVERSE'
    SKIP = 'SKIP'
    DRAW2 = 'DRAW2'
    WILD = 'WILD'
    DRAW4 = 'DRAW4'


class PlayerCommand(Enum):
    DISCARD = 1
    DRAW = 2
    CHALLENGE = 3
    UNO = 4
    CATCH = 5
    END_TURN = 6

class TurnDirection(Enum):
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


settings = {
    'deck_size': 1,
    'default_deck': [
        {
            'times': 1,
            'numbers': [0],
            'actions': [],
            'exclude_color': [Color.ANY],
        },
        {
            'times': 2,
            'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'actions': [Action.SKIP, Action.REVERSE, Action.DRAW2],
            'exclude_color': [Color.ANY],
        },
        {
            'times': 4,
            'numbers': [],
            'actions': [Action.WILD, Action.DRAW4],
            'include_color': [Color.ANY],
        },
    ],
    'default_hand_size': 7,
}


class UnoOutOfCardsError(Exception):
    pass

class UnoInvalidTurnException(Exception):
    pass

class UnoInvalidCardPlayed(Exception):
    pass

class UnoPlayerNotFoundException(Exception):
    pass

class UnoInvalidCardException(Exception):
    pass

class UnoWildColorNotChosen(Exception):
    pass


class Card:
    '''Represents an UNO card'''

    def __init__(self, color, number, action):
        self.color = color
        self.number = number
        self.action = action
        self.can_choose_card_color = (self.action == Action.WILD)\
            or (self.action == Action.DRAW4)

    def is_action_card(self):
        return self.action is not None

    def is_number_card(self):
        return self.number is not None

    def is_wild_draw_four(self):
        return self.action in [Action.WILD, Action.DRAW4]


    def __str__(self):
        if self.color and self.number is not None:
            return f'{self.color.value}_{self.number}'
        elif self.color and self.color == Color.ANY:
            return f'{self.action.value}'
        elif self.color and not self.number:
            return f'{self.color.value}_{self.action.value}'


class Deck:

    def __init__(self, num=1, ordered=True):
        # TODO: implement number of decks - with many players 2 decks would be needed to play etc
        self.cards = self.add_cards_to_deck()

        if not ordered:
            self.shuffle()


    def add_cards_to_deck(self):
        cf = CardFactory(settings['default_deck'])
        cf.make_cards()
        return cf.get_cards()


    def shuffle(self):
        random.shuffle(self.cards)
        return self.cards


class CardFactory:

    def __init__(self, config):
        self.config = config
        self.cards = []

    def make_cards(self):
        for conf in self.config:
            quantity = conf.get('times')

            if not quantity:
                continue

            exclude_colors = conf.get('exclude_color', []) # dont exclude any colors by default
            include_colors = conf.get('include_color', [c for c in Color]) # all colors by  default
            colors = [c for c in include_colors if c not in exclude_colors]

            for _ in range(quantity):
                numbers = conf.get('numbers')
                if numbers:
                    self.make_number_cards(colors, numbers)

                actions = conf.get('actions')
                if actions:
                    self.make_action_cards(colors, actions)


    def make_number_cards(self, colors, numbers):
        for color in colors:
            for number in numbers:
                self.cards.append(Card(color, number, None))

    def make_action_cards(self, colors, actions):
        for color in colors:
            for action in actions:
                self.cards.append(Card(color, None, action))

    def get_cards(self):
        return self.cards


class DrawPile:

    cards = []

    def __init__(self, cards):
        self.cards = cards

    def draw(self, quantity):
        for _ in range(quantity):
            return self.drawOne()

    def drawOne(self):
        try:
            return self.cards.pop(0)
        except IndexError:
            # No more cards to pop
            raise UnoOutOfCardsError(
                'Draw pile empty, add more cards'
            )

    def add_card(self, card):
        '''If draw pile is depleted use cards from discard pile'''
        self.cards.append(card)


    def add_cards(self, card_list):
        for card in card_list:
            self.add_card(card)


class DiscardPile:

    cards = []


    def  __init__(self, card=None):
        if card:
            self.cards.append(card)

    def discard(self, card):
        self.cards.append(card)

    def get_last_card(self):
        return self.cards[-1]

    def clear_discard_pile(self, clear_all=False):
        '''Empties and returns all but the 'top' card'''
        if clear_all:
            cards = self.cards
            self.cards.clear()
            return cards
        else:
            cards = self.cards[:-1]
            last_but_one = self.cards[:-1]

            self.cards.clear()
            self.cards.append(last_but_one)

            return cards


class Player:

    def __init__(self, display_name):
        self.display_name = display_name
        self.player_id = id(self)
        self.hand = []
        self.game_controller = None

    def draw(self):
        command_details = {'action': PlayerCommand.DRAW}
        drawn_cards = self.game_controller.process_player_command(self.player_id, command_details)
        self.hand.extend(drawn_cards)

        return True


    def discard(self, command_details):
        # Discarding a wild/draw4
        # {'action': PlayerCommand.DISCARD, 'card': c1, 'color_chosen': Color.RED, say_uno: True}

        # TODO: check if the card is available in hand and throw error if not
        card = command_details.get('card')

        if not self.card_in_hand(card):
            raise UnoInvalidCardException

        result = self.game_controller.process_player_command(self.player_id, command_details)

        return True

    def keep(self):
        command_details = {'action': PlayerCommand.END_TURN}
        result = self.game_controller.process_player_command(self.player_id, command_details)
        return result

    def challenge(self):
        command_details = {'action': PlayerCommand.CHALLENGE}
        result = self.game_controller.process_player_command(self.player_id, command_details)
        return result

    def catch(self):
        command_details = {'action': PlayerCommand.CATCH}
        result = self.game_controller.process_player_command(self.player_id, command_details)
        return result

    def join_game(self, game_controller):
        self.game_controller = game_controller
        self.game_controller.add_player(self)

    def add_cards_to_hand(self, cards):
        for card in cards:
            self.add_card_to_hand(card)

    def add_card_to_hand(self, card):
        self.hand.append(card)

    def card_in_hand(self, card):
        for c in self.hand:
            if c.color == card.color and c.number == card.number and c.action == card.action:
                return True

        return False

    def get_card_index(self, card):
        for idx, c in enumerate(self.hand):
            if c.color == card.color and c.number == card.number and c.action == card.action:
                return idx
        return False


    def remove_card_from_hand(self, card):
        idx = self.get_card_index(card)
        self.hand.pop(idx)


    def __str__(self):
        return f'Player Id: {self.player_id}, Name: {self.display_name}'



class TurnTracker:
    '''Keep track of player turn and directions'''

    def __init__(self, player_list):
        # clockwise is forward, counter-clockwise is backward
        self.turn_direction = TurnDirection.CLOCKWISE
        self.tracked_players = []
        self.current_turn_player = None
        self.previous_turn_player = None

    def get_current_turn_player(self):
        if not self.tracked_players:
            # No players to track, raise exception
            return False

        if self.current_turn_player is None:
            self.current_turn_player = self.tracked_players[0]

        return self.current_turn_player

    def get_current_turn_player_index(self):

        for idx, value in enumerate(self.tracked_players):
            if value.player_id == self.get_current_turn_player().player_id:
                return idx

        return False # or raise Exception

    def calculate_next_turn_player(self, card=None):

        # XXX: Need a better way to implement no-card checking
        if card is None:
            card = Card(Color.ANY, 999, 999)

        current_turn_player_index = self.get_current_turn_player_index()

        if card.action == Action.REVERSE:
            self.toggle_turn_direction()

        if card.action == Action.SKIP:
            next_relative_index = 2 # (+) or (-) two steps away from the current turn players index
        elif card.action == Action.REVERSE and len(self.tracked_players) == 2:
            next_relative_index = 2 # (+) or (-) two steps away from the current turn players index
        else:
            next_relative_index = 1 # default

        if self.turn_direction == TurnDirection.CLOCKWISE:
            next_turn_player_index = current_turn_player_index + next_relative_index
        if self.turn_direction == TurnDirection.COUNTER_CLOCKWISE:
            next_turn_player_index = current_turn_player_index - next_relative_index

        next_turn_player_index = next_turn_player_index % len(self.tracked_players)

        self.previous_turn_player = self.tracked_players[current_turn_player_index]
        self.current_turn_player = self.tracked_players[next_turn_player_index]


    def toggle_turn_direction(self):
        if self.turn_direction == TurnDirection.CLOCKWISE:
            self.turn_direction = TurnDirection.COUNTER_CLOCKWISE

        if self.turn_direction == TurnDirection.COUNTER_CLOCKWISE:
            self.turn_direction = TurnDirection.CLOCKWISE

    def get_previous_turn_player(self):
        return self.previous_turn_player

    def set_previous_turn_player(self, player):
        self.previous_turn_player = player

    def start_tracking_player(self, player):
        if not self.tracked_players:
            self.current_turn_player = player
        self.tracked_players.append(player)

    def stop_tracking_player(self, player):
        player_index = None

        for idx, value in enumerate(self.tracked_players):
            if value.player_id == player.player_id:
                player_index = idx
                break

        if player_index is not None:
            self.tracked_players.pop(player_index)
            return True

        return False


class GameController:

    deck = None # the deck used to play a game
    discard_pile = None
    draw_pile = None
    players = []

    last_player_turn = None
    history = []
    turn_direction = 'forward' # can be forward or backward

    color_chosen = None
    draw_stack_quantity = 0


    current_player_index = 0

    challenge_succeeded = "To be implemented"
    color_in_play = None
    winners = []

    def __init__(self, settings):
        self.settings = settings

        self.starting_hand_qty = self.settings['default_hand_size']

        # create a new deck of cards
        self.make_game_deck()
        self.deck.shuffle()

        # populate draw pile
        self.draw_pile = DrawPile(self.deck.cards)
        # self.draw_pile.add_cards(self.deck.cards)

        # discard pile
        self.discard_pile = DiscardPile()

        # turn tracker
        self.turn_tracker = TurnTracker(self.players)

        self.history = []

    def add_player(self, player):
        self.turn_tracker.start_tracking_player(player)
        return self.players.append(player)


    def make_game_deck(self):
        deck_size = self.settings['deck_size']
        self.deck = Deck(num=deck_size)

    def start(self):
        self.deal_starting_hand()
        self.start_discard_pile()


    def deal_starting_hand(self):

        for _ in range(self.starting_hand_qty):
            for player in self.players:
                card = self.draw_pile.drawOne()
                player.add_card_to_hand(card)

    def start_discard_pile(self):

        for idx, card in enumerate(self.draw_pile.cards):
            if card.is_number_card():
                starter_card = self.draw_pile.cards.pop(idx)
                break

        self.color_in_play = starter_card.color
        self.discard_pile.discard(starter_card)


    def process_player_command(self, player_id, command_details):
        player = self.get_player_by_id(player_id)
        current_turn_player = self.turn_tracker.get_current_turn_player()
        command = command_details.get('action')
        card = command_details.get('card')
        color_chosen = command_details.get('color_chosen')
        say_uno = command_details.get('say_uno')

        turn_based_commands = [
            PlayerCommand.DISCARD,
            PlayerCommand.DRAW,
            PlayerCommand.CHALLENGE,
        ]

        if (command in turn_based_commands) and current_turn_player != player:
            raise UnoInvalidTurnException


        if command == PlayerCommand.DISCARD:
            if not self.is_valid_card_to_play(card):
                raise UnoInvalidCardPlayed

            if card.can_choose_card_color and not color_chosen:
                raise UnoWildColorNotChosen

            if card.can_choose_card_color:
                self.color_chosen = color_chosen
                self.color_in_play = color_chosen
            else:
                self.color_chosen = None
                self.color_in_play = card.color

            # discard
            self.discard_pile.discard(card)
            self.refresh_draw_stack_quantity(card)
            player.remove_card_from_hand(card)

            if self.has_player_turn_ended(player, command_details):
                self.turn_tracker.calculate_next_turn_player(card)
                # TODO: check if player finished all cards and completed the game!!!
                if len(player.hand) == 0:
                    self.winners.append(player)
                    self.turn_tracker.stop_tracking_player(player)

            # Add history detail
            command_details['player_id'] = player_id
            self.history.append(command_details)

            return True


        if command == PlayerCommand.DRAW:

            drawn_cards = []

            if self.draw_stack_quantity > 0:
                for i in range(self.draw_stack_quantity):
                    try:
                        drawn_cards.append(self.draw_pile.drawOne())
                    except UnoOutOfCardsError:
                        discarded_cards = self.discard_pile.clear_discard_pile()
                        random.shuffle(discarded_cards)
                        self.draw_pile.add_cards(discarded_cards)
                        drawn_cards.append(self.draw_pile.drawOne())

                # reset draw stack quantity
                self.refresh_draw_stack_quantity()
                self.turn_tracker.calculate_next_turn_player()
            else:
                try:
                    dc = self.draw_pile.drawOne()
                    drawn_cards.append(dc)
                except UnoOutOfCardsError:
                    discarded_cards = self.discard_pile.clear_discard_pile()
                    random.shuffle(discarded_cards)
                    self.draw_pile.add_cards(discarded_cards)
                    dc = self.draw_pile.drawOne()
                    drawn_cards.append(dc)


            command_details['player_id'] = player_id
            self.history.append(command_details)

            return drawn_cards

        if command == PlayerCommand.CHALLENGE:
            challenge_succeeded = False
            challenge_success_penalty = 4
            challenge_failure_penalty = 6
            penalty_cards = []

            previous_turn_player = self.turn_tracker.get_previous_turn_player()
            last_history_item = self.history[-1]

            last_played_card = self.discard_pile.get_last_card()

            if last_history_item.get('action') == PlayerCommand.DISCARD \
               and last_played_card.action == Action.DRAW4:
                last_top_card = self.discard_pile.cards[-2]

                for card in previous_turn_player.hand:
                    if card.action != Action.DRAW4 and self.can_place_on_top(card, last_top_card):
                        challenge_succeeded = True
                        break

            if challenge_succeeded:
                for _ in range(challenge_success_penalty):
                    try:
                        penalty_cards.append(self.draw_pile.drawOne())
                    except UnoOutOfCardsError:
                        discarded_cards = self.discard_pile.clear_discard_pile()
                        random.shuffle(discarded_cards)
                        self.draw_pile.add_cards(discarded_cards)
                        penalty_cards.append(self.draw_pile.drawOne())
                previous_turn_player.add_cards_to_hand(penalty_cards)
            else:
                for _ in range(challenge_failure_penalty):
                    try:
                        penalty_cards.append(self.draw_pile.drawOne())
                    except UnoOutOfCardsError:
                        discarded_cards = self.discard_pile.clear_discard_pile()
                        random.shuffle(discarded_cards)
                        self.draw_pile.add_cards(discarded_cards)
                        penalty_cards.append(self.draw_pile.drawOne())
                current_turn_player.add_cards_to_hand(penalty_cards)
                self.turn_tracker.calculate_next_turn_player()


            self.refresh_draw_stack_quantity()

            command_details['player_id'] = player_id
            command_details['challenge_succeeded'] = challenge_succeeded
            self.history.append(command_details)
            return challenge_succeeded


        if command == PlayerCommand.CATCH:
            success = False
            uno_penalty = 2
            previous_turn_player = self.turn_tracker.get_previous_turn_player()

            last_history_item = self.history[-1]
            penalty_cards = []

            if len(previous_turn_player.hand) == 1 \
               and last_history_item.get('action') == PlayerCommand.DISCARD \
               and not last_history_item.get('say_uno'):

                success = True


                for _ in range(uno_penalty):
                    try:
                        penalty_cards.append(self.draw_pile.drawOne())
                    except UnoOutOfCardsError:
                        discarded_cards = self.discard_pile.clear_discard_pile()
                        random.shuffle(discarded_cards)
                        self.draw_pile.add_cards(discarded_cards)
                        penalty_cards.append(self.draw_pile.drawOne())

            command_details['player_id'] = player_id
            command_details['success'] = success
            self.history.append(command_details)

            previous_turn_player.add_cards_to_hand(penalty_cards)

            return success

        if command == PlayerCommand.END_TURN:
            self.turn_tracker.calculate_next_turn_player()
            return True


    def get_player_by_id(self, player_id):
        player = [p for p in self.players if p.player_id == player_id]

        if not player:
            raise UnoPlayerNotFoundException

        return player[0]


    def is_valid_card_to_play(self, card):
        '''
        A card is valid to play if the color, number or action is the same as the last played card
        '''

        # TODO: refactor to use self.color_in_play
        last_played_card = self.discard_pile.get_last_card()

        # if draw stack quantity is non-zero, card has to be stacked with action and color does not matter
        if self.draw_stack_quantity > 0 and last_played_card.action != card.action:
            return False

        # if last played card is number card then color or number should match
        if last_played_card.is_number_card():
            return last_played_card.color == card.color \
                or last_played_card.number == card.number \
                or card.color == Color.ANY

        # if last played card is SKIP, REVERSE then color or action should match
        if last_played_card.action in [Action.SKIP, Action.REVERSE]:
            return last_played_card.color == card.color \
                or last_played_card.action == card.action \
                or card.color == Color.ANY


        # if last played card is DRAW2, DRAW4 and someone already picked up then color or action should match
        if last_played_card.action in [Action.DRAW2, Action.DRAW4]:
            return last_played_card.color == card.color \
                or self.color_in_play == card.color \
                or card.color == Color.ANY \
                or last_played_card.action == card.action

        # if last played card is WILD then color should match
        if last_played_card.action == Action.WILD:
            return card.color == self.color_in_play or card.color == Color.ANY

    def refresh_draw_stack_quantity(self, card=None):
        '''
        If card is a draw 2 then add to the draw stack quant
        if card is a draw 4 then add to the draw stack quant and set color

        '''

        if card and card.is_action_card and card.action == Action.DRAW2:
            self.draw_stack_quantity += 2
        elif card and card.is_action_card and card.action == Action.DRAW4:
            self.draw_stack_quantity += 4
        else:
            self.draw_stack_quantity = 0


    def has_player_turn_ended(self, player, command_details):

        action = command_details.get('action')
        card = command_details.get('card')
        forced_draw = command_details.get('forced_draw') # T or F

        # if action is discard and card is symbol card and player has no cards in hand then false
        if action == PlayerCommand.DISCARD and card.is_action_card() and len(player.hand) == 0:
            return False

        # if action is draw and draw is not forced and card is valid playable card then false
        # if action == PlayerCommand.DRAW and not forced_draw and self.is_valid_card_to_play(card):
        #     return False

        # if action is challenge and player was successfull in the challenge then false
        # if action == PlayerCommand.CHALLENGE and self.is_challenge_succeeded():
        #     return False

        # if command details has "END TURN" then true i guess
        return True


    def can_place_on_top(self, new_card, old_card):
        # FIXME: rename this method - this is supposed to be for checking if no other card was playable when challenged

        last_played_card = old_card

        if last_played_card.color == Color.ANY:
            current_color = self.color_chosen
        else:
            current_color = last_played_card.color

        is_valid_color = (current_color == new_card.color) or (new_card.color == Color.ANY)
        is_valid_number= (last_played_card.number == new_card.number)
        is_valid_action = (last_played_card.action == new_card.action)

        return (
            is_valid_color
            or is_valid_number
            or is_valid_action
        )


    def is_challenge_succeeded(self):
        return self.challenge_succeeded

    def get_game_state(self):
        game_state = {
            'last_played_card': self.discard_pile.get_last_card(),
            'current_turn_player': self.turn_tracker.get_current_turn_player(),
            'turn_direction': self.turn_tracker.turn_direction,
            'color_in_play': self.color_in_play,
            'history': self.history,
            'players_all': self.players,
            'players_in_game': self.turn_tracker.tracked_players,
            'winners': self.winners,
        }

        return game_state


def show_game_state(gc):
    gs  = gc.get_game_state()


    print(f'------------------------- ALL PLAYERS -------------------------')
    for p in gs['players_all']:
        print(p)

    print(f'------------------------- WINNERS  -------------------------')
    for p in gs['winners']:
        print(p)

    print(f'------------------------- GAME PLAYERS -------------------------')
    for p in gs['players_in_game']:
        print(p)

    print(f'------------------------- HISTORY -------------------------')
    for p in gs['history']:
        print(p)

    print(f'------------------------- GAME INFO -------------------------')

    print(f'CURRENT PLAYER TURN: {gs["current_turn_player"]}')
    print(f'TURN DIRECTION: {gs["turn_direction"]}')
    print(f'LAST PLAYED CARD: {gs["last_played_card"]}')
    print(f'COLOR IN PLAY: {gs["color_in_play"]}')
