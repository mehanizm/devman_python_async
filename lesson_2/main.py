import time
import asyncio
import curses
import random
import uuid
from dataclasses import dataclass
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from collisions import has_collision
from explosion import explode
from game_scenario import get_garbage_delay_tics

TIC_TIMEOUT = 0.1
STARS_DENSITY = 100
STARS_SYMBOLS = '+*.:'
YEAR = 1969

coroutines = []
obstacles = {}
obstacles_coroutines = {}
YEAR = 1957

@dataclass 
class Obstacle:
	row: float
	column: float
	frame_row: float
	frame_column: float

	def coordinates(self):
		return (self.row, self.column)
	
	def size(self):
		return (self.frame_row, self.frame_column)


async def year_increment():
	while True:
		YEAR += 1
		await asyncio.sleep(15)


async def fly_garbage(canvas, column, garbage_frame, obs_id, speed=0.5):
	# Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start.
	
	rows_number, columns_number = canvas.getmaxyx()
	column = max(column, 0)
	column = min(column, columns_number - 1)

	row = 1

	frame_row, frame_column = get_frame_size(garbage_frame)

	obs = Obstacle(row, column, frame_row, frame_column)
	obstacles[obs_id] = obs

	try:
		while row < rows_number:
			#canvas.addstr(round(obs.row-1), round(obs.column), '({})'.format(obs.coordinates))
			draw_frame(canvas, obs.row, obs.column, garbage_frame)
			await asyncio.sleep(0)
			#canvas.addstr(round(obs.row-1), round(obs.column), '              ')
			draw_frame(canvas, obs.row, obs.column, garbage_frame, negative=True)
			obs.row += speed
		else:
			obstacles.pop(obs_id)
	except asyncio.CancelledError:
		draw_frame(canvas, obs.row, obs.column, garbage_frame, negative=True)
		coroutines.append(
			explode(canvas, 
			obs.row + round(frame_row / 2), 
			obs.column + round(frame_column / 2))
		)
		obstacles.pop(obs_id)
		return
	


async def run_asteroid_field(canvas, max_column):
	"""Add random garbage"""
	# frames
	trashes = []
	# random pause before start
	ticks_before_start = random.randint(0, 10)
	with open('animations/trash_large.txt', "r") as f:
  		trashes.append(f.read())
	with open('animations/trash_small.txt', "r") as f:
  		trashes.append(f.read())
	
	while True:
		# if get_garbage_delay_tics(YEAR) == None:
		# 	await sleep(0)
		# else:
		# 	await sleep(get_garbage_delay_tics(YEAR))

		await sleep(ticks_before_start)
		trash = random.choice(trashes)
		column = random.randint(1, max_column-1)
		obs_id = str(uuid.uuid4())
		obstacles_coroutines[obs_id] = fly_garbage(canvas, column, trash, obs_id)
		coroutines.append(obstacles_coroutines[obs_id])


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

		for obs_id, obs in obstacles.items():
			if has_collision(obs.coordinates(), obs.size(), (row, column)):
				try:
					obstacles_coroutines[obs_id].throw(asyncio.CancelledError())
				except:
					coroutines.remove(obstacles_coroutines[obs_id])
					return


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
	  	await sleep(ticks_before_start)

	  	canvas.addstr(row, column, symbol, curses.A_DIM)
	  	await sleep(ticks_with_dim)

	  	canvas.addstr(row, column, symbol)
	  	await sleep(ticks_with_original_1)

	  	canvas.addstr(row, column, symbol, curses.A_BOLD)
	  	await sleep(ticks_with_bold)

	  	canvas.addstr(row, column, symbol)
	  	await sleep(ticks_with_original_2)


async def animate_spaceship(canvas, row, column, frames):
	"""Spaceship animation with keyboard control and limitts"""

	# get max size of the canvas
	rows, columns = canvas.getmaxyx()
	max_row, max_column = rows - 1, columns - 1
	row_speed = column_speed = 0

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
			rows_direction, columns_direction, space = read_controls(canvas, 1)
			row_speed, column_speed = update_speed(row_speed, column_speed,
												   rows_direction, columns_direction)
			row += row_speed
			column += column_speed

			if space:
				coroutines.append(fire(canvas, row, column + round(frame_column/2)))
			
			for obs_id, obs in obstacles.items():
				if has_collision(obs.coordinates(), obs.size(), (row, column)):
					try:
						obstacles_coroutines[obs_id].throw(asyncio.CancelledError())
					except:
						coroutines.append(show_gameover(canvas))
						coroutines.remove(obstacles_coroutines[obs_id])
						return


async def show_gameover(canvas):

	with open('animations/game_over.txt', "r") as f:
  		game_over_label = f.read()
	
	# canvas sizes
	max_row, max_column = canvas.getmaxyx()
	midle_row = round(max_row/2)
	midle_column = round(max_column/2)	

	rows, columns = get_frame_size(game_over_label)
	corner_row = midle_row - rows / 2
	corner_column = midle_column - columns / 2

	while True:
		draw_frame(canvas, corner_row, corner_column, game_over_label)
		await asyncio.sleep(0)


async def sleep(tics=1):
	for _ in range(tics):
		await asyncio.sleep(0)


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
	
	# start for the sky
	for _ in range(STARS_DENSITY):
	  	row = random.randint(1, max_row-1)
	  	column = random.randint(1, max_column-1)
	  	star_symbol = random.choice(STARS_SYMBOLS)
	  	coroutines.append(blink(canvas, row, column,symbol=star_symbol))

	# spaceship
	coroutines.append(animate_spaceship(canvas, midle_row, midle_column, frames))	

	# add random garbage
	coroutines.append(run_asteroid_field(canvas, max_column))

	# year increment
	# coroutines.append(year_increment())

	# eventloop
	while True:
		for coroutine in coroutines:
			try:
				coroutine.send(None)
			except StopIteration:
				coroutines.remove(coroutine)
		canvas.refresh()
		time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':

	curses.update_lines_cols()
	curses.wrapper(draw)