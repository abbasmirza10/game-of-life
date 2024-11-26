from flask import Flask, request, jsonify
import requests
import random
from life_parts import combined_life

MY_PORT = 5000 # to simplify single-server testing
# MY_PORT = random.randrange(1<<12, 1<<15) # if you want to run several servers on the same machine

MY_URL = "http://localhost:"+str(MY_PORT) # local testing
# MY_URL = "http://sp24-cs340-###.cs.illinois.edu:"+str(MY_PORT) # project deployment (change ### to your VM number)

app = Flask(__name__)

state = 'Waiting'
board = []
board_width = 0
board_height = 0


@app.get('/')
def index():
  """Display the UI (this function is finished and ready to go)"""
  return open('tile_ui.html', 'r').read()


@app.route('/ping', methods=['GET'])
def ping():
    global state, board
    if state == 'Waiting':
        return jsonify({'state': state})
    else:
        # Constructing the board with newlines after each row, including the last row
        board_representation = '\n'.join(board) + '\n'
        return jsonify({'state': state, 'tile': board_representation})


@app.route('/inform', methods=['POST'])
def inform():
    if state != 'Waiting':
        return jsonify({'error': 'Server must be in Waiting state'}, 409)
    data = request.json
    try:
        response = requests.put(data['url'], json={'author': 'your_netid', 'url': MY_URL})
        response.raise_for_status()  # Ensures we raise an exception for bad requests
        return jsonify({'result': 'registered'})
    except (requests.RequestException, KeyError) as e:
        return jsonify({'error': str(e)}), 500


@app.route('/config', methods=['POST'])
def config():
    global state, board, board_width, board_height
    if state != 'Waiting':
        return jsonify({'error': 'Config not allowed in current state'}), 409
    try:
        data = request.json
        board_width = int(data['width'])
        board_height = int(data['height'])
        board = [' ' * board_width for _ in range(board_height)]
        state = 'User Edit'
        return jsonify({'result': 'configuration set'})
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400




@app.route('/change/<x>/<y>/<c>/', methods=['GET'])
def change(x, y, c):
    global state, board, board_width, board_height
    if state != 'User Edit':
        return jsonify({'error': 'Not in User Edit state'}), 409

    try:
        x, y = int(x), int(y)
        if x < 0 or x >= board_width or y < 0 or y >= board_height:
            return jsonify({'error': 'Coordinates out of bounds'}), 403
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    c = c[0] if c else ' '
    valid_chars = {' ', '#'} | set(chr(i) for i in range(ord('0'), ord('o')+1))
    if c not in valid_chars:
        return jsonify({'error': 'Invalid character'}), 403

    row = list(board[y])
    row[x] = c
    board[y] = ''.join(row)

    return jsonify({'result': 'change successful'}), 200



@app.route('/stop', methods=['GET'])
def stop():
    """Stop the simulation and reset the state."""
    global state
    if state not in ['User Edit', 'Simulating']:
        return jsonify({'error': 'Invalid state for operation'}, 409)
    state = 'Waiting'
    return jsonify({'result': 'stopped'})


# Adjusting the /pause endpoint to correctly handle states
@app.route('/pause', methods=['GET'])
def pause():
    global state
    if state != 'Simulating':
        return jsonify({'error': 'Pause operation not allowed in current state'}), 409
    state = 'User Edit'
    return jsonify({'result': 'Simulation paused, state switched to User Edit.'}), 200



@app.route('/tick', methods=['POST'])
def tick():
    global state, board
    if state not in ['User Edit', 'Simulating']:
        return jsonify({'error': 'Invalid state for operation'}), 409

    border = request.data.decode('utf-8')  # Ensure border is decoded correctly from request data

    try:
        updated_board = combined_life(board, border)
        board = updated_board  # Update the global board state directly with the list of strings
        state = 'Simulating'
        # Directly return the board as plain text
        return '\n'.join(board) + '\n', 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=MY_PORT, debug=True)