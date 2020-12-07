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
		num_cities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()

		while not foundTour and time.time() - start_time < time_allowance:

			# Try to find a greedy tour starting from each city O(n)
			for i in range(num_cities):
				route = []
				cities_left = self._scenario.getCities().copy()
				route.append(cities_left[i])
				cities_left.remove(cities_left[i])
				no_solution = False
				
				# Find and add the closest city to the route for each city O(n)
				while len(cities_left) > 0 and not no_solution: 
					shortest_dist = math.inf
					closest_city = None
					# Find the closest city O(n)
					for city in cities_left:
						if route[-1].costTo(city) < shortest_dist:
							shortest_dist = route[-1].costTo(city)
							closest_city = city
					
					# Add closest city to the tour if there is one available
					if closest_city is not None:
						route.append(closest_city)
						cities_left.remove(closest_city)
					else:
						no_solution = True

				# Make sure it found a complete soution back to the start
				if not no_solution and route[-1].costTo(route[0]) < math.inf:
					foundTour = True
					bssf = TSPSolution(route)
					count += 1
					break
				
		end_time = time.time()
		results = {}
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results
	
	
	
	''' <summary>
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints: 
		max queue size, total number of states created, and number of pruned states.</returns> 
	'''
		
	def branchAndBound( self, time_allowance=60.0 ):
		pass



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
