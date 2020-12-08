#!/usr/bin/python3

from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))




import time
import numpy as np
from TSPClasses import *
import heapq
import itertools
import random
from copy import deepcopy




class TSPSolver:
	def __init__( self, gui_view ):
		self._scenario = None

	def setupWithScenario( self, scenario ):
		self._scenario = scenario


	''' <summary>
		This is the entry point for the default solver
		which just finds a valid random tour.  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of solution, 
		time spent to find solution, number of permutations tried during search, the 
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''
	
	def defaultRandomTour( self, time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		while not foundTour and time.time()-start_time < time_allowance:
			# create a random permutation
			perm = np.random.permutation( ncities )
			route = []
			# Now build the route using the random permutation
			for i in range( ncities ):
				route.append( cities[ perm[i] ] )
			bssf = TSPSolution(route)
			count += 1
			if bssf.cost < np.inf:
				# Found a valid route
				foundTour = True
		end_time = time.time()
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


	''' <summary>
		This is the entry point for the greedy solver, which you must implement for 
		the group project (but it is probably a good idea to just do it for the branch-and
		bound project as a way to get your feet wet).  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found, the best
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''

	def greedy( self,time_allowance=60.0 ):

		cities = self._scenario.getCities()
		ncities = len(cities)
		best_cost = math.inf
		count = 0
		results = {}
		foundTour = False
		best_route = []
		start_time = time.time()
		
		
		#Run greedy ncities time starting with new city each time and take best 
		#Each iteration is O(n^2)
		for start_city in cities:
			total_cost = 0
			current_city = start_city
			route = []
			remaining_cites = cities.copy()
			remaining_cites.remove(start_city)
			route.append(start_city)


			#Travel from city to city completing a path - O(n)
			while remaining_cites:
				#Initialize least cost to inifinity
				least_cost = math.inf
				least_cost_city = None
				#Check all path options for current city - O(n)
				for option in remaining_cites:
					cost = current_city.costTo(option)
					if cost < least_cost:
						least_cost = cost
						least_cost_city = option
				#Check if route could not be completed and update current city
				if least_cost != math.inf:
					remaining_cites.remove(least_cost_city)
					route.append(least_cost_city)
					total_cost = total_cost + least_cost
					current_city = least_cost_city
				else:
					total_cost = math.inf
					remaining_cites = []
			
			#Check if route could not be completed and update cost
			if total_cost != math.inf:
				total_cost = total_cost + route[ncities-1].costTo(start_city)
			count = count + 1
			#Check for best route so far and update
			if total_cost < best_cost:
				best_cost = total_cost
				best_route = route
		
		#Check if we found a complete route
		if best_cost != math.inf:
			foundTour = True

		end_time = time.time()

		#Create return variables
		bssf = TSPSolution(best_route)
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
			
		return results

	
	
	
	# BEGIN BRANCH AND BOUND CODE

	def printMatrix(self, arr):
		for row in range( len(arr) ):
			for col in range( len(arr[row]) ):
				
				print("{:4.0f}".format(arr[row][col]), end=' ')
			print()
		print()
	
	# Uses the list of cities to generate a 2d matrix of travel costs
	# Iterates over each city,city pair once, creating an N^2 matrix
	# TIME: 2 * N^2 = N^2 (the 2 comes from initializing the array)
	# SPACE: N^2
	def generateMatrix(self, cityList, cNum):
		cities = [[float('inf') for i in range(cNum)] for j in range(cNum)]

		for row in range(cNum):
			for col in range(cNum):
				if row == col: continue
				cities[row][col] = cityList[row].costTo(cityList[col])

		# self.printMatrix(cities)
		return cities

	# Takes in a city matrix and calculates the lower bound value
	# Returns the lower bound cost and the update city matrix
	# Iterates over each row of the grid twice, then each col twice
	# TIME: 4 * N^2 = N^2
	# SPACE: Works in place, uses the pre-existing N^2 matrix
	def calcLowerBound(self, mat):
		minCost = 0
		for row in range( len(mat) ):
			low = float('inf')
			for col in range( len(mat[row]) ):
				low = min(low, mat[row][col])
			
			if low == float('inf'): continue
			
			minCost += low
			for col in range( len(mat[row]) ):
				mat[row][col] -= low
		
		for col in range( len(mat) ):
			low = float('inf')
			for row in range( len(mat[row]) ):
				low = min(low, mat[row][col])
			
			if low == float('inf'): continue

			minCost += low
			for row in range( len(mat[row]) ):
				mat[row][col] -= low

		return minCost, mat

	# Calculates the additional costs related to travelling
	# from the source city to destination city in given matrix
	# Iterates across N long row, then down N long column
	# Calls the N^2 time lower bound update
	# TIME: N^2 because of bound update
	# SPACE: Works in place
	def calcChild(self, cities, source, dest):
		# print("calcChild", source, "->", dest)
		if cities[source][dest] == float('inf'): return float('inf'), None

		travelCost = cities[source][dest]
		for row in range( len(cities) ):
			cities[row][dest] = float('inf')
		for col in range( len(cities) ):
			cities[source][col] = float('inf')

		cities[dest][source] = float('inf')
		bound, cities = self.calcLowerBound(cities) # N^2 time

		return travelCost + bound, cities
	
	''' <summary>
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints: 
		max queue size, total number of states created, and number of pruned states.</returns> 
	'''
		
	def branchAndBound( self, time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		bssf = None
		start_time = time.time()

		_statesGenerated = 0
		_statesPruned = 0
		_bssfUpdates = 0
		_queueMaxLength = 0

		# Worst Case N^N if it tries every random shape
		# Realistic: ~N time to populate a list
		# Space: N long array is discarded
		bssfCost = self.defaultRandomTour()['cost']
		# print("Random Cost:", bssfCost)

		# Generates a N^2 matrix using in N^2 time
		cityMat = self.generateMatrix(cities, ncities)
		minCost, cityMat = self.calcLowerBound(cityMat)

		q = []
		route = [cities[0]]
		# self.printMatrix(cityMat)

		# According to slides, heap push is O(Log N)
		heapq.heappush(q, bbState(route, 0, cityMat, minCost))

		while q and (time.time() - start_time < time_allowance):
			_queueMaxLength = max(_queueMaxLength, len(q))

			# According to slides, heap pop is O(Log N)
			state = heapq.heappop(q)

			if state.lowerBound > bssfCost: 
				_statesPruned += 1
				continue

			if len(state.route) == ncities:
				bssf = TSPSolution(state.route)
				bssfCost = state.lowerBound
				_bssfUpdates += 1
				continue

			# Worst Case: N-1 Cities to expand, Log N average
			# Worse Case: N-1 Matricies to generate, Log N average
			# Overall Log N * N^2 operations in time and space
			# In practice, value will be smaller due to timeout and pruning
			for destination in cities:
				if destination not in state.route:
					dest = destination._index
					_statesGenerated += 1
					# print("Generate Child:", dest)
					childRoute = state.route.copy() # N time and space
					childRoute.append(cities[dest]) 
					childCities = deepcopy(state.cityMatrix) # N^2 Time and Space

					# calcChild is an N^2 Time, 1 Space function
					additionalCost, childCities = self.calcChild(childCities, childRoute[-2]._index, dest)
					childCost = state.lowerBound + additionalCost
					if childCost < bssfCost:
						# print("Inject Child:", dest)
						#Push is O(Log N)
						heapq.heappush(q, bbState(childRoute, state.depth+1, childCities, childCost))
					else:
						_statesPruned += 1

		_statesPruned += len(q)

		end_time = time.time()
		results['time'] = end_time - start_time
		results['soln'] = bssf
		results['cost'] = bssfCost
		results['count'] = _bssfUpdates
		results['max'] = _queueMaxLength
		results['total'] = _statesGenerated
		results['pruned'] = _statesPruned
		# print("Done")
		return results



	''' <summary>
		This is the entry point for the algorithm you'll write for your group project.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found during search, the 
		best solution found.  You may use the other three field however you like.
		algorithm</returns> 
	'''
	
	def fancy( self,time_allowance=60.0 ):
		# Use greedy algorithm to find a initial tour
		greedy_solution = self.greedy(time_allowance)
		self.bssf = greedy_solution['soln']

		results = {}
		self.num_cities = len(self._scenario.getCities())
		self.start_time = time.time()
		self.new_solutions_found = 0
		self.time_allowance = time_allowance

		# Define number of cities to swap in a route
		# As k increases, the solution optimality and time complexity both increase
		if self.num_cities <= 9 and self.num_cities >= 5:
			k = self.num_cities - 3
		elif self.num_cities <= 15:
			k = 5
		elif self.num_cities <= 25:
			k = 4
		elif self.num_cities <= 75:
			k = 3
		else:
			k = 2

		self.improved = True
		while self.improved:
			self.improved = False
			for i in range(self.num_cities):
				# Check all combinations of k cities swaped to see if route has improved
				self.kOptSwap(self.bssf.route, k, i)

						
		end_time = time.time()
		results['cost'] = self.bssf.cost
		results['time'] = end_time - self.start_time
		results['count'] = self.new_solutions_found
		results['soln'] = self.bssf
		results['max'] = 0
		results['total'] = 0
		results['pruned'] = 0
		return results



	def kOptSwap(self, route, k, i):
		# Check time allowance
		if time.time() - self.start_time > self.time_allowance:
			return

		if k > 1:
			# Make new routes by swapping different combinations 2 cities
			for j in range(self.num_cities):
				new_route = self.twoOptSwap(route, i, j)
				# Keep swaping cities in route until k cities have been swaped 
				self.kOptSwap(new_route, k - 1, j)

		else :
			# Check if solution is better than best solution so far, if so update
			new_solution = TSPSolution(route)
			if new_solution.cost < self.bssf.cost:
				self.improved = True
				self.bssf = new_solution
				self.new_solutions_found += 1
				print('Updated BSSF: ' + str(self.bssf.cost))
			
	
	# Swap 2 cities in a route
	def twoOptSwap(self, route, i, k):
		a = route[0:i]
		b = route[i:k+1]
		b.reverse()
		c = route[k+1:]
		new_route = a + b + c
		return new_route
