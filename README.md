# Install Dependencies
Use pipenv to install the dependencies from the pipfile

# Running the server

## Development
```
fastapi dev src/main.py
```

# Routes
| Method | Route                                         | Body                                                       |
|--------|-----------------------------------------------|------------------------------------------------------------|
| POST   | /game/new/                                    |                                                            |
| POST   | /game/{game_id}/player/new/                   | {'display_name': 'game_name'}                              |
| POST   | /game/{game_id}/player/{player_id}/join/      |                                                            |
| POST   | /game/{game_id}/start/                        |                                                            |
| POST   | /game/{game_id}/player/{player_id}/discard/   | {'card': {'color': 'yellow', 'number': 7, 'action': null}} |
| POST   | /game/{game_id}/player/{player_id}/draw/      |                                                            |
| POST   | /game/{game_id}/player/{player_id}/keep/      |                                                            |
| POST   | /game/{game_id}/player/{player_id}/challenge/ |                                                            |
| POST   | /game/{game_id}/player/{player_id}/catch/     |                                                            |


# Playing the Game



## Creating a new game


## Creating players

## Adding players to the game

## Starting the game

## Viewing game information
- whos turn is it
- color in play
- history
- etc

## Player Commands

Possible Colors
- Blue
- Green
- Red
- Yellow
- Any (for Wild and Draw4)

Possible Actions
- Draw2
- Draw4
- Reverse
- Skip
- Wild

### discard

Number Card
```
{
    'color': 'blue',
    'number': 5,
    'action': null
}
```

Action Card
```
{
    'color': 'red',
    'number': null,
    'action': 'skip
}
```

Wild/Draw4 Card
```
{
    'color': 'any',
    'number': null,
    'action': 'draw4',
    'color_chosen': 'yellow'
}
```

Saying UNO!
```
{
    'color': 'green',
    'number': 5,
    'action': null,
    'say_uno': true
}
```


### draw
player will be automatically given the correct number of cards.

### keep
when a player draws a card they can choose to either play the drawn card(if playabled) or keep it.

The `/keep/` route must be called every time a player draws a card to signal that they choose to end their turn.

### Challenge

### Catch
will only work if the last history item is a discard

