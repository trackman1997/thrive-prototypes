import pygame
import math
import random
from scipy.spatial import Delaunay
import numpy
from operator import itemgetter

#setup

background_colour = (255,255,255)
(WIDTH, HEIGHT) = (1000, 600)
num_cells=15
Hooke_constant = 4
spring_damp = 2
pressure_coefficient = 3
drag_t = 5
drag_n = 5
t=0
FPS=30
deltat=1./FPS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def distance(a,b):
	return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
	
def sign(a):
	#return 1, -1, or 0
	if a>0:
		return 1
	elif a<0:
		return -1
	else:
		return 0

class cell:
	def __init__(self, parent, location):
		self.x = location[0]
		self.y = location[1]
		self.colour = [255,0,0]
		self.forces = [0,0]
		self.v = [0,0]
		self.amplitude = random.uniform(0.5,2)
		self.frequency = random.uniform(1,10)
		self.offset = random.uniform(0,2*math.pi) #0 to 2 pi

	def draw(self):
		pygame.draw.circle(screen, self.colour, [int(self.x), int(self.y)], 10)
			
class edge:
	def __init__(self, a, b):
		self.nodes = [a,b]
		self.x = (a.x + b.x)/2
		self.y = (a.y + b.y)/2
		self.colour = [0,0,0]
		self.rest_length = distance(self.nodes[0],self.nodes[1])

	def draw(self,color):
		pygame.draw.line(screen, color, [self.nodes[0].x,self.nodes[0].y],[self.nodes[1].x,self.nodes[1].y], 3)
			
class chamber:
	def __init__(self, vertices, edges):
		if len(vertices)>len(edges):
			print("Error: Chamber edges < vertices: ", len(edges), " < ", len(vertices))
		elif len(vertices)<len(edges):
			print("Error: Chamber edges > vertices: ", len(edges), " > ", len(vertices))
		self.cells = vertices
		lm = self.find_leftmost_point()
		rm = self.find_rightmost_point()
		line_points = [lm,rm]
		A_array, B_array, C_array = self.sort_array_into_A_B_C(line_points)
		self.sort_and_merge_A_B_C_arrays(A_array, B_array, C_array)
		self.edges = edges
		self.signed_volume = self.compute_volume()
		self.initial_volume = math.fabs(self.signed_volume)
		(self.x,self.y)=self.compute_center()
		
	def compute_volume(self):
		a1=0.0
		a2=0.0
		for i in range(len(self.cells) - 1):
			a1+=self.cells[i].x*self.cells[i+1].y
			a2+=self.cells[i].y*self.cells[i+1].x
		a1+=self.cells[-1].x*self.cells[0].y
		a2+=self.cells[-1].y*self.cells[0].x
		return (a2-a1)/2

	def compute_center(self):
		x = 0.0
		y = 0.0
		for i in range(len(self.cells)-1):
			x += (self.cells[i].x+self.cells[i+1].x)*(self.cells[i].x*self.cells[i+1].y-self.cells[i].y*self.cells[i+1].x)
			y += (self.cells[i].y+self.cells[i+1].y)*(self.cells[i].x*self.cells[i+1].y-self.cells[i].y*self.cells[i+1].x)
		x += (self.cells[-1].x+self.cells[0].x)*(self.cells[-1].x*self.cells[0].y-self.cells[-1].y*self.cells[0].x)
		y += (self.cells[-1].y+self.cells[0].y)*(self.cells[-1].x*self.cells[0].y-self.cells[-1].y*self.cells[0].x)
		x = x/(-6*self.signed_volume)
		y = y/(-6*self.signed_volume)
		return int(x),int(y)
	
	def draw(self,color):
		pygame.draw.circle(screen, color, [self.x, self.y], 10)
	#The functions below here are in place to ensure the cells are in the correct order so as to avoid intersection	
	def find_leftmost_point(self):
		leftmost_point = None
		leftmost_x = None
		for Cell in self.cells:
			x = Cell.x
			if leftmost_x == None or x < leftmost_x:
				leftmost_x = x
				leftmost_point = Cell
		return leftmost_point

	def find_rightmost_point(self):
		rightmost_point = None
		rightmost_x = None
		for Cell in self.cells:
			x = Cell.x
			if rightmost_x == None or x > rightmost_x:
				rightmost_x = x
				rightmost_point = Cell
		return rightmost_point

	def is_point_above_the_line(self, point, line_points):
		slope = (line_points[1].y-line_points[0].y)/(line_points[1].x-line_points[0].x)
		y=slope*point.x+(line_points[0].y-slope*line_points[0].x)
		return point.y-y

	def sort_array_into_A_B_C(self, line_points):
		A_array, B_array, C_array = [], [], []
		for Cell in self.cells:
			xp = self.is_point_above_the_line(Cell, line_points)
			if xp < 0:
				A_array.append(Cell)
			elif xp > 0:
				B_array.append(Cell)
			elif xp == 0:
				C_array.append(Cell)
		return A_array, B_array, C_array

	def sort_and_merge_A_B_C_arrays(self, A_array, B_array, C_array):
		A_C_array = A_array + C_array
		sorted(A_C_array,key=lambda cell: cell.x)
		sorted(B_array,key=lambda cell: cell.x, reverse=True)        
		self.cells = A_C_array + B_array
		
def merge_chambers(parent,a,b,rem):
	#Something might be off here but I can't put my finger on it
	cells=[]
	edges=[]
	for Cell in a.cells:
		cells.append(Cell)
	for Cell in b.cells:
		if Cell not in cells:
			cells.append(Cell)
	for Edge in a.edges:
		edges.append(Edge)
	for Edge in b.edges:
		if Edge not in edges:
			edges.append(Edge)
	for e in edges:
		if e.nodes[0] in rem.nodes and e.nodes[1] in rem.nodes:
			edges.remove(e)
	print('Number of chambers before merge = ',len(parent.chambers))
	parent.chambers.remove(a)
	parent.chambers.remove(b)
	parent.chambers.append(chamber(cells,edges))
	print('Number of chambers after merge = ',len(parent.chambers))
			
class creature:

	def __init__(self):
		#layout some cells in the creature
		self.location = [WIDTH/2,HEIGHT/2] #location in space of the creature
		self.external_cells = [] #list of cells which are exposed to the environment
		self.cells = [] #list of cells which make up the creature 
		self.points= []
		self.chambers = [] #list of pressure chambers inside the creature, each chamber is formed of edges
		self.edges = [] #list of edges in the creature, each edge connects 2 cells
		self.external_edges=[] #list of edges exposed to the environment
		self.edges2=[]

		for i in range(num_cells):
			self.cells.append(cell(self,(int(self.location[0] + random.randint(-200,200)),int(self.location[1] + random.randint(-200,200)))))

		#if the cells are too close move them a litte
		done = False
		counter = 0
		while not done:
			counter += 1
			found = False
			for Cell in self.cells:
				for Cell2 in self.cells:
					if distance(Cell, Cell2) <= 40 and Cell is not Cell2:
						Cell.x += random.randint(-10,10)
						Cell.y += random.randint(-10,10)
						found = True

			if not found or counter >= 100000:
				done = True
		
		#convert cells to points
		for Cell in self.cells:
			self.points.append([Cell.x,Cell.y])
		
		#build Delaunay Triangulization
		tri = Delaunay(self.points)
		for elm in tri.simplices:
			e1 = edge(self.cells[elm[0]],self.cells[elm[1]])
			e2 = edge(self.cells[elm[2]],self.cells[elm[1]])
			e3 = edge(self.cells[elm[0]],self.cells[elm[2]])
			self.edges.append(e1)
			self.edges.append(e2)
			self.edges.append(e3)
			vertices=(self.cells[elm[0]],self.cells[elm[1]],self.cells[elm[2]])
			self.chambers.append(chamber(vertices,(e1,e2,e3)))
		
		#This is the loop that converts Delaunay Triangulization to Gabriel Graph but the chambers get messed up
		'''
		for Edge in self.edges:
			radius = distance(Edge,Edge.nodes[1])
			removed = False
			for Cell in self.cells:
				if distance(Cell,Edge)<radius and Cell not in Edge.nodes:
					removed = True
					adj_chamb=[]
					for ch in self.chambers:
						if Edge.nodes[0] in ch.cells and Edge.nodes[1] in ch.cells:
							adj_chamb.append(ch)
					print('number of adjacent chambers = ',len(adj_chamb))
					if len(adj_chamb)==2:
						merge_chambers(self,adj_chamb[0],adj_chamb[1],Edge)
					if len(adj_chamb)==1:
						self.chambers.remove(adj_chamb[0])
					break
			if not removed:
				self.edges2.append(Edge)		
		self.edges=self.edges2
		'''
		#sort out external edges
		for Edge in self.edges:
			adj_chamb=0
			for ch in self.chambers:
				if Edge.nodes[0] in ch.cells and Edge.nodes[1] in ch.cells:
					adj_chamb+=1
			if adj_chamb==1:
				self.external_edges.append(Edge)

	def move(self):
		for Cell in self.cells:
			Cell.forces = [0,0]
			
		#Spring forces
		for Edge in self.edges:
			a=Edge.nodes[0]
			b=Edge.nodes[1]
			new_rest_length = ((1 + a.amplitude*math.sin(a.frequency*t + a.offset) 
				+ b.amplitude*math.sin(b.frequency*t + b.offset)))*Edge.rest_length
			#work out it's current length
			current_length = distance(a,b)
			force_magnitude = Hooke_constant*(new_rest_length - current_length)
			force_direction = [(a.x - b.x)/(current_length), (a.y - b.y)/(current_length)]
			#add it onto the forces of each end
			a.forces[0] += force_direction[0]*force_magnitude-spring_damp*a.v[0]
			a.forces[1] += force_direction[1]*force_magnitude-spring_damp*a.v[1]
			b.forces[0] += -force_direction[0]*force_magnitude-spring_damp*b.v[0]
			b.forces[1] += -force_direction[1]*force_magnitude-spring_damp*b.v[1]
		
		#forces from chamber pressure
		for ch in self.chambers:
			ch.signed_volume = ch.compute_volume()
			ch.x,ch.y = ch.compute_center()
			force_magnitude = pressure_coefficient*(1 - math.fabs(ch.signed_volume)/ch.initial_volume)
			for Edge in ch.edges:
				force_direction1=[-(Edge.nodes[1].y-Edge.nodes[0].y),(Edge.nodes[1].x-Edge.nodes[0].x)]
				force_direction2=[-force_direction1[0],-force_direction1[1]]
				d1=(Edge.x+force_direction1[0]-ch.x)**2+(Edge.y+force_direction1[1]-ch.y)**2
				d2=(Edge.x+force_direction2[0]-ch.x)**2+(Edge.y+force_direction2[1]-ch.y)**2
				if d1<d2:
					force_direction=force_direction1
				else:
					force_direction=force_direction2
				Edge.nodes[0].forces[0] -= force_direction[0]*force_magnitude*0.5
				Edge.nodes[0].forces[1] -= force_direction[1]*force_magnitude*0.5
				Edge.nodes[1].forces[0] -= force_direction[0]*force_magnitude*0.5
				Edge.nodes[1].forces[1] -= force_direction[1]*force_magnitude*0.5
		
		#forces from external drag
		for Edge in self.external_edges:
			a=Edge.nodes[0]
			b=Edge.nodes[1]
			dist = distance(a,b)
			normal_dir = [-(a.y-a.y),(b.x-b.x)]
			tangential_dir = [normal_dir[1],-normal_dir[0]]
			v = [(a.v[0]+b.v[0])/2,(a.v[1]+b.v[1])/2]
			normal_v = v[0]*normal_dir[0]+v[1]*normal_dir[1]
			tangential_v = v[0]*tangential_dir[0]+v[1]*tangential_dir[1]
			t_force_mag=drag_t*sign(tangential_v)*tangential_v**2
			n_force_mag=drag_n*sign(normal_v)*normal_v**2
			for Cell in Edge.nodes:
				Cell.forces[0]-=t_force_mag*tangential_dir[0]/(dist*2)
				Cell.forces[1]-=t_force_mag*tangential_dir[1]/(dist*2)
				Cell.forces[0]-=n_force_mag*normal_dir[0]/(dist*2)
				Cell.forces[1]-=n_force_mag*normal_dir[1]/(dist*2)
			
		for Cell in self.cells:
			Cell.v[0]+=Cell.forces[0]*deltat
			Cell.v[1]+=Cell.forces[1]*deltat
			Cell.x += (Cell.forces[0])*.5*deltat**2
			Cell.y += (Cell.forces[1])*.5*deltat**2
		
	def draw(self):
		for Cell in self.cells:
			Cell.draw()
		for Edge in self.edges:
			Edge.draw([0,0,0])
		for Edge in self.external_edges:
			Edge.draw([0,255,0])
		for Chamber in self.chambers:
			Chamber.draw([random.randint(0,200),random.randint(0,200),random.randint(0,200)])

worm = creature()
			
running=True
while running:
	screen.fill(background_colour)
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				running = False
	worm.move()
	worm.draw()
	pygame.display.update()
	t+=deltat
	clock.tick(FPS)
pygame.quit()