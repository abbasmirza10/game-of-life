Conway's Game of Life
Conway's Game of Life is a cellular automaton devised by mathematician John Conway. It is a zero-player game, meaning that its evolution is determined by its initial state, with no further input from humans. The game is played on a grid of cells, where each cell can either be alive or dead, and the state of each cell evolves based on a few simple rules.

Rules of the Game
Any live cell with fewer than two live neighbors dies (underpopulation).
Any live cell with two or three live neighbors lives on to the next generation (survival).
Any live cell with more than three live neighbors dies (overpopulation).
Any dead cell with exactly three live neighbors becomes a live cell (reproduction).
Features
Visual representation of the Game of Life grid.
Ability to start, pause, and reset the simulation.
Adjustable speed for the simulation.
Interactive grid where users can manually set initial live cells.
Installation
To run the project locally:

Clone the repository:
bash
Copy code
git clone https://github.com/abbasmirza10/game-of-life.git
Navigate to the project directory:
bash
Copy code
cd game-of-life
Install the necessary dependencies:
bash
Copy code
pip install -r requirements.txt
Run the Game of Life:
bash
Copy code
python life_game.py
Usage
Start: Begin the simulation.
Pause: Pause the simulation.
Reset: Reset the grid to its initial state.
Grid: Click on cells to toggle between alive or dead.
Contributing
Feel free to fork the repository and submit pull requests with improvements or bug fixes.

License
This project is licensed under the MIT License.

