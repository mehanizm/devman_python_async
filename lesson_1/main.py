import time
import asyncio
import curses
import random
from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1
STARS_SYMBOLS = '+*.:'


async def blink(canvas, row, column, symbol='*'):
	"""Blink functiton for the sky animations"""

	# random pause before start
	ticks_before_start = random.randint(0, 10)
	# 2 seconds DIM
	ticks_with_dim = 20
	# 0.3 second original 1
	ticks_with_original_1 = 3
	# 0.3 second bold
	ticks_with_bold = 3
	# 0.5 second original 2
	ticks_with_original_2 = 5

	while True:
	  for _ in range(ticks_before_start):
	    await asyncio.sleep(0)

	  canvas.addstr(row, column, symbol, curses.A_DIM)
	  for _ in range(ticks_with_dim):
	    await asyncio.sleep(0)

	  canvas.addstr(row, column, symbol)
	  for _ in range(ticks_with_original_1):
	    await asyncio.sleep(0)
		
	  canvas.addstr(row, column, symbol, curses.A_BOLD)
	  for _ in range(ticks_with_bold):
	    await asyncio.sleep(0)

	  canvas.addstr(row, column, symbol)
	  for _ in range(ticks_with_original_2):
	    await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column, frames):
	"""Spaceship animation with keyboard control and limitts"""

	# get max size of the canvas
	rows, columns = canvas.getmaxyx()
	max_row, max_column = rows - 1, columns - 1

	while True:
		for frame in frames:

			# calculatte max coordinates for ship
			frame_row, frame_column = get_frame_size(frame)
			row = min(row, max_row - frame_row)
			row = max(1, row)
			column = min(column, max_column -frame_column)
			column = max(1, column)

			# draw frame for 0.2 second
			draw_frame(canvas, row, column, frame, negative=False)
			for _ in range(2):
				await asyncio.sleep(0)

			# erase frame
			draw_frame(canvas, row, column, frame, negative=True)

			# read keyboard and move ship
			rows_direction, columns_direction, space = read_controls(canvas, 2)
			row += rows_direction
			column += columns_direction


def draw(canvas):
	"""Main fraw functions"""

	# canvas settings
	canvas.border()
	curses.curs_set(False)
	canvas.nodelay(True)
	canvas.refresh()

	# read frames for the ship
	frames = []
	with open("animations/rocket_frame_1.txt", "r") as f:
	  	frames.append(f.read())
	with open("animations/rocket_frame_2.txt", "r") as f:
	  	frames.append(f.read())	

	# canvas sizes
	max_row, max_column = canvas.getmaxyx()
	midle_row = round(max_row/2)
	midle_column = round(max_column/2)	

	# collect coroutines
	coroutines = []
	
	# start for the sky
	for _ in range(100):
	  	row = random.randint(1, max_row-1)
	  	column = random.randint(1, max_column-1)
	  	star_symbol = random.choice(STARS_SYMBOLS)
	  	coroutines.append(blink(canvas, row, column,symbol=star_symbol))

	# gun fire	  
	coroutines.append(fire(canvas, midle_row, midle_column))	

	# spaceship
	coroutines.append(animate_spaceship(canvas, midle_row, midle_column, frames))	

	# eventloop
	while True:
		for blinker in coroutines:
			try:
				blinker.send(None)
			except StopIteration:
				coroutines.remove(blinker)
		canvas.refresh()
		time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
	curses.update_lines_cols()
	curses.wrapper(draw)
    