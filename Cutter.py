import sys, platform
import serial
from SVG2PLT import SVG2PLT
from PLT import PLT
from Coord import Coord
import json

class Cutter:

	# PLT and SVG
	plt = None
	svg = None

	# CONSTANTS
	MAX_X = 10000		# maximum distance on the X axis
	MAX_Y = 10000		# maximum distance on the Y axis
	BAUDRATE = 57600	# baudrate for the serial port comms

	# The current location of the head on the x, y axis
	current_x = 0
	current_y = 0

	step_size = 100		# the number of positions to move with user control

	passes = 1		# the number of times to cut the shape
	scale = 1.0

	# Up speed - speed that the machine moves while up
	# us <1-40>
	up_speed = 40

	# Down speed - speed that the machine moves while down
	# ds <1-40>
	down_speed = 40

	# Plunge speed - speed at which the tool is lowered
	# ps <1-40>
	plunge_speed = 40

	# Lift speed - speed at which the tool is raised
	# ls <1-40>
	lift_speed = 40

	# Depth - default tool depth while down
	# dp <1-670>
	cutting_depth = 300

	# Up lift - Lift tool by an extra amount while up (for special cases)
	# ul <0-300>
	up_lift = 0

	# Up/down state - Value is 1 if up, 0 if down
	# returned: up=<0/1>;
	up = None

	# Tool - Value is 0 for left tool or 1 for right tool
	# tool <0/1>
	# returned: tool=<0/1>;
	current_tool = 0

	serial = None

	# CONSTRUCTOR
	def __init__(self):
		if(platform.system() == 'Linux'):
			self.serial = False
			#self.serial = serial.Serial ("/dev/ttyAMA0", self.BAUDRATE, timeout=1)	# open the serial "/dev/ttyAMA0"

		self.svg2plt = SVG2PLT()
		self.plt = PLT()

		self.home()

	def __del__(self):
		if(platform.system() == 'Linux' and self.serial != False):
			self.serial.close()

	# home the cutter location
	def home(self):
		self.current_x = 0
		self.current_y = 0
		self.move(self.current_x, self.current_y)

	# change a setting variable
	def change_setting(self, setting, value):
		setattr(self, setting, float(value))
		print(setting+":"+value)

	# load a file
	def load_file(self, filename='./static/svg/pattern.svg'):
		self.svg2plt.load_file(filename)
		self.svg2plt.parse()

		self.plt = self.svg2plt.plt		# TODO: i'm not completely happy with this idea
		self.plt.reset_settings()

		output = self.display_dimensions()
		return(json.dumps(output))

	# send the PLT to the cutter
	def cut(self):
		self.plt.scale = self.scale
		output = self.plt.build()
		print(output)

		for line in output:
			response = self.send(line)

	def move_direction(self, direction):
		if(direction=='N'):
			self.move((self.step_size*-1), 0)
		elif(direction=='S'):
			self.move(self.step_size, 0)
		elif(direction=='E'):
			self.move(0, (self.step_size*-1))
		elif(direction=='W'):
			self.move(0, self.step_size)

	def move(self, x, y):
		next_x = self.current_x + x
		next_y = self.current_y + y

		if(next_x<0):
			next_x = 0
		elif(next_x>self.MAX_X):
			next_x = self.MAX_X

		if(next_y<0):
			next_y = 0
		elif(next_y>self.MAX_Y):
			next_y = self.MAX_Y

		command = Coord('U', next_x, next_y)
		response = self.send(str(command))
		if(response):
			self.current_x = next_x;
			self.current_y = next_y;

			self.plt.x_offset = self.current_x		# TODO: I'm not sure this is the right place to do this.
			self.plt.y_offset = self.current_y

	# send a string to the serial port and read the response
	def send(self, command):
		if(platform.system() == 'Linux' and self.serial != False):
			response = self.serial.write(command.encode('utf-8'))
		else:
			response = 1
		return(response)

	def display_dimensions(self):
		if(self.plt.display_units == "mm"):
			output = {"width":format(self.plt.display_width*25.4, '.1f'),"height":format(self.plt.display_height*25.4, '.1f'),"units":self.plt.display_units}
		else:
			output = {"width":self.plt.display_width,"height":self.plt.display_height,"units":self.plt.display_units}
		return(json.dumps(output))
