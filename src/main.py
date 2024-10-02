from fastapi import Body, FastAPI
from pydantic import BaseModel

from enum import Enum
from typing import Optional

from .uno import Card, Color, Action, GameController, Player, settings


app = FastAPI()


games = []
players = []


class PlayerModel(BaseModel):
    display_name: str


class CardColor(str, Enum):
    ANY = 'any'
    BLUE = 'blue'
    GREEN = 'green'
    RED = 'red'
    YELLOW = 'yellow'


class CardAction(str, Enum):
    DRAW2 = 'draw2'
    DRAW4 = 'draw4'
    REVERSE = 'reverse'
    SKIP = 'skip'
    WILD = 'wild'


class CardModel(BaseModel):
    color: CardColor
    number: int | None = None
    action: CardAction | None = None


class DiscardOption(BaseModel):
    card: CardModel
    color_chosen: CardColor | None = None
    say_uno: Optional[bool]



# ---------- Game management ----------

@app.post('/game/new', tags=['Game'])
def new_game():
    gc = GameController(settings)
    games.append(gc)

    payload = {
        'success': True,
        'message': 'Game created successfully',
        'game_id': gc.game_id,
    }

    return payload


@app.get('/game/list', tags=['Game'])
def list_games():
    games_list = [g.game_id for g in games]
    return games_list


@app.post('/game/{game_id}/player/new', tags=['Game'])
def new_player(game_id: int, player: PlayerModel):
    p = Player(player.display_name)
    players.append(p)

    payload = {
        'success': True,
        'message': 'Player created successfully',
        'player': {
            'display_name': p.display_name,
            'player_id': p.player_id
        }
    }

    return payload


@app.post('/game/{game_id}/player/{player_id}/join', tags=['Game'])
def join_game(game_id: int, player_id: int):
    g = get_game_by_id(game_id)
    p = get_player_by_id(player_id)
    p.join_game(g)

    payload = {
        'success': True,
        'message': 'Player joined game successfully',
    }

    return payload



@app.post('/game/{game_id}/start', tags=['Game'])
def start_game(game_id: int):
    g = get_game_by_id(game_id)
    g.start()

    payload = {
        'success': True,
        'message': f'Game {game_id} started',
    }

    return payload


@app.get('/game/{game_id}/state', tags=['Game'])
def game_state(game_id: int):
    g = get_game_by_id(game_id)
    gs = g.get_game_state()

    if gs.get('current_turn_player'):
        gs['current_turn_player'] = get_short_player(gs['current_turn_player'])

    if gs.get('players_all'):
        players = [get_short_player(p) for p in gs['players_all']]
        gs['players_all'] = players

    if gs.get('players_in_game'):
        players = [get_short_player(p) for p in gs['players_in_game']]
        gs['players_in_game'] = players

    payload = {
        'success': True,
        'message': f'current game state for game id {game_id}',
        'game_state': gs,
    }

    return payload



# ---------- Player Interaction ----------

@app.post('/game/{game_id}/player/{player_id}/discard', tags=['Player'])
def player_command_discard(game_id: int, player_id: int, discard_options: DiscardOption):
    card_color = Color[discard_options.card.color.upper()] if discard_options.card.color else None
    card_action = Action[discard_options.card.action.upper()] if discard_options.card.action else None
    card = Card(card_color, discard_options.card.number, card_action)

    command_details = {
        'card': card,
        'color_chosen': discard_options.color_chosen,
        'say_uno': discard_options.say_uno,
    }

    p = get_player_by_id(player_id)
    result = p.discard(command_details)

    payload = {
        'success': result,
        'message': 'discarded card successfully',
    }

    return payload


@app.post('/game/{game_id}/player/{player_id}/draw', tags=['Player'])
def player_command_draw(game_id: int, player_id: int):
    p = get_player_by_id(player_id)
    drawn_cards = p.draw()

    payload = {
        'success': len(drawn_cards) > 0,
        'message': f'Picked up {len(drawn_cards)} cards',
        'drawn_cards': drawn_cards,
    }

    return payload


@app.post('/game/{game_id}/player/{player_id}/keep', tags=['Player'])
def player_command_keep(game_id: int, player_id: int):
    p = get_player_by_id(player_id)
    result = p.keep()

    payload = {
        'success': result,
        'message': f'Command: KEEP, Result: {result}',
    }

    return payload


@app.post('/game/{game_id}/player/{player_id}/challenge', tags=['Player'])
def player_command_challenge(game_id: int, player_id: int):
    p = get_player_by_id(player_id)
    result = p.challenge()

    payload = {
        'success': result,
        'message': f'Challenge succeeded: {result}',
    }

    return payload


@app.post('/game/{game_id}/player/{player_id}/catch', tags=['Player'])
def player_command_catch(game_id: int, player_id: int):
    p = get_player_by_id(player_id)
    result = p.catch()

    payload = {
        'success': result,
        'message': f'Player caught successfully: {result}',
    }

    return payload


def get_game_by_id(game_id):
    for g in games:
        if g.game_id == game_id:
            return g
    return False


def get_player_by_id(player_id):
    for p in players:
        if p.player_id == player_id:
            return p
    return False


def get_short_player(player):
    p = {
        'display_name': player.display_name,
        'player_id': player.player_id,
        'hand': player.hand,
        'game': player.game_controller.game_id,
    }

    return p
