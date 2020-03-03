from Agent import Agent
import random

# Space object has these attributes:
# int xcoord, ycoord, breeze, stench, probOfP, probOfW, h
# breeze and stench are 0 or 1 based on percept
# probOfP and probOfW are probability that space has pit or wumpus
# h is optimistic number of steps from that space to the exit
# All spaces are unexplored until moved to. This boolean prevents space reassessment if revisited.
class Space(object):
    breeze = stench = probOfP = probOfW = h = g = f = 0
    unexplored = True

    def __init__(self, xc, yc):
        self.xcoord = xc
        self.ycoord = yc

    def __str__(self):
        return "xcoord: " + str(self.xcoord) + "\nycoord: " + str(self.ycoord) + "\nprobOfDeath: " + str(self.probOfW + self.probOfP) + "\nf,h,g: " + str(self.f) + "," + str(self.h) + "," + str(self.g) + "\n"

    def __repr__(self):
        return "xcoord: " + str(self.xcoord) + "\nycoord: " + str(self.ycoord) + "\nprobOfDeath: " + str(self.probOfW + self.probOfP) + "\nf,h,g: " + str(self.f) + "," + str(self.h) + "," + str(self.g) + "\n"

    def __eq__(self, other):
        return self.xcoord == other.xcoord and self.ycoord == other.ycoord


def isFacingSpace(x, y, xpos, ypos, dir):
    if (x == (xpos + 1) ): # Space is to the right
        return (dir == 0)
    elif (x == (xpos - 1) ): # Space is to the left
        return (dir == 2)
    elif (y == (ypos + 1) ): # Space is above
        return (dir == 3)
    else: # Space is below
        return (dir == 1)

def calculateDirection(current, dir):
    #calculate the number of turns to direction
    #used for calculating f(n)
    if (current == dir):
        #already in the correct direction
        return 0
    elif ((current == 1 and dir == 3) or (current == 3 and dir == 1) or (current == 0 and dir == 2) or (current == 2 and dir == 0)):
        #need to do a 180
        return 2
    else:
        #otherwise just turn once
        return 1

def updateDirection(turn, dir):
    if (turn == Agent.Action.TURN_LEFT):
        dir -= 1
        if (dir < 0):
            dir = 3
    else:
        dir += 1
        if dir > 3:
            dir = 0
    return dir


def updatePos(direction, xpos, ypos):
    if ( direction == 0):	# Facing right
        xpos += 1
    elif ( direction == 1):	# Facing down
        ypos -= 1
    elif ( direction == 2):	# Facing left
        xpos -= 1
    else:					# Facing up
        ypos += 1
    return xpos, ypos

def getDirection(xpos, ypos, x, y):
    if (x == (xpos + 1) ): # Space is to the right
        return 0
    elif (x == (xpos - 1) ): # Space is to the left
        return 2
    elif (y == (ypos + 1) ): # Space is above
        return 3
    else: # Space is below
        return 1

class MyAI ( Agent ):

    def __init__ ( self ):
        self.MAX_POINTS_SPENT = 50# Prevent endless wandering
        self.points_spent = 0

        # Create 7x7 grid of Space objects
        self.grid = [[ Space(row, col) for col in range(7)] for row in range(7)]

        # Initialize coordinates for Space objects
        # for i in range(7):
        #     for j in range(7):
        #         self.grid[i][j].xcoord = i
        #         self.grid[i][j].ycoord = j

        # Initialize heuristic for Space objects
        for i in range(7):
            for j in range(7):
                self.grid[i][j].h = self.grid[i][j].xcoord + self.grid[i][j].ycoord

        self.max_xpos = self.max_ypos = 6	# Assume 7x7
        self.xpos = self.ypos = 0			# Current x,y position
        self.current_dir = 0				# Let direction 0 be "right", 1 "down", 2 "left", 3 "up"
        self.has_arrow = True
        self.time_to_leave = False
        self.route = []						# LIFO queue for "breadcrumb trail" back to start
        self.first_F_found = False
        self.dead = False					# Is Wumpus dead?
        self.moving = False					# If moving == True, a new space has been chosen and agent is in the process of getting there.
        self.movingToQ = []					# Queue of turning instructions for facing chosen space before moving forward
        self.possible_wumpus = []           # List of possible wumpus coordinate locations
        self.possible_pits = []             # List of possible pit coordinate locations
        self.checked_pits = []              # List of checked pit spaces - include visited spaces and the neighbors
        self.checked_wumpus = []
        self.safe = set()                     # List of safe spaces that can be included in the A* search
        self.blocked_spaces = []            # spaces that are safe, but are currently blocked according to a current state space
        self.visited = []                  # used for the case when all the visited spaces are the safe spaces then just leave


    def getAction( self, stench, breeze, glitter, bump, scream ):
        self.points_spent += 1
        self.MAX_POINTS_SPENT = self.max_xpos*self.max_ypos
        self.grid[self.xpos][self.ypos].g = self.points_spent
        self.grid[self.xpos][self.ypos].f = (self.grid[self.xpos][self.ypos].g + self.grid[self.xpos][self.ypos].h)
        #self.checked.append((self.xpos, self.ypos))
        self.safe.add((self.xpos, self.ypos))
        self.visited.append((self.xpos, self.ypos))

        if (self.points_spent >= self.MAX_POINTS_SPENT):
            self.time_to_leave = True

        if (scream):
            self.dead = True
            # Remove threat of wumpus
            for i in range(7):
                for j in range(7):
                    self.grid[i][j].probOfW = 0

        if (bump):
            if (dir == 0):		# Facing right
                self.max_xpos = self.xpos
                print("Bump! Max x coord: " + str(self.max_xpos) )
            elif (dir == 3):	# Facing up
                self.max_ypos = self.ypos
                print("Bump! Max y coord: " + str(self.max_ypos) )
            # TODO: After discovering a boundary, there may be spaces marked with probOfP or probOfW that we now know must be 0. Update ALL associated probabilities in this change.

        # If this is a previously unvisited space, update the observations
        # and probabilities for current and neighboring Spaces
        # if((self.grid[0][1].breeze or self.grid[0][1].stench) and (self.grid[1][0].breeze or self.grid[1][0].stench)):
        #     print("here")
        #     return Agent.Action.CLIMB

        if (self.grid[self.xpos][self.ypos].unexplored):
            self.grid[self.xpos][self.ypos].unexplored = False

            if (stench):
                if (self.dead):
                    pass
                elif(self.xpos == 0 and self.ypos == 0):
                    #stench at first space then leave
                    return Agent.Action.CLIMB
                elif (len(self.possible_wumpus) == 1):
                    #only one possible location then shoot it
                    #update position and update direction
                    coordinate = self.possible_wumpus.pop(0)
                    updatePos(self.current_dir, coordinate[0], coordinate[1])
                    #shoot
                else:
                    self.grid[self.xpos][self.ypos].stench = 1

                    # Update probOfW for neighbors. Exclude: explored spaces, known out of bound spaces.
                    # TODO: This algorithm is fine for the first encounter of stench, but subsequent encounters may prove spaces that were given some probability as actually Safe.
                    #       It would be nice if we could recognize when this occurs and update those spaces.
                    neighbors = self.getNeighbors()

                    above = below = right = left = 0
                    possibleNumOfSpaces = 0

                    for neighbor in neighbors:
                        if ((neighbor[1].xcoord, neighbor[1].ycoord) not in self.checked_wumpus):
                            possibleNumOfSpaces += 1
                            self.possible_wumpus.append((neighbor[1].xcoord, neighbor[1].ycoord))
                            # right0, left1, below2, above3
                            if (neighbor[0] == 0):
                                right = 1
                            elif (neighbor[0] == 1):
                                left = 1
                            elif (neighbor[0] == 2):
                                below = 1
                            else:  # neighbor[0] == 3
                                above = 1

                    # if ( (self.xpos + 1) <= self.max_xpos and self.grid[self.xpos + 1][self.ypos].unexplored ):
                    #     right = 1
                    #     self.possible_wumpus.append((self.xpos+1, self.ypos))
                    # if ( (self.ypos + 1) <= self.max_ypos and self.grid[self.xpos][self.ypos + 1].unexplored ):
                    #     above = 1
                    #     self.possible_wumpus.append((self.xpos, self.ypos+1))
                    # if ( (self.xpos - 1) >= 0 and self.grid[self.xpos - 1][self.ypos].unexplored ):
                    #     left = 1
                    #     self.possible_wumpus.append((self.xpos - 1, self.ypos))
                    # if ( (self.ypos - 1) >= 0 and self.grid[self.xpos][self.ypos - 1].unexplored ):
                    #     below = 1
                    #     self.possible_wumpus.append((self.xpos, self.ypos - 1))
                    #
                    # possibleNumOfSpaces = right + above + left + below

                    if (possibleNumOfSpaces != 0):
                        if (right == 1):
                            self.grid[self.xpos + 1][self.ypos].probOfW += (1 / possibleNumOfSpaces)
                        if (above == 1):
                            self.grid[self.xpos][self.ypos + 1].probOfW += (1 / possibleNumOfSpaces)
                        if (left == 1):
                            self.grid[self.xpos - 1][self.ypos].probOfW += (1 / possibleNumOfSpaces)
                        if (below == 1):
                            self.grid[self.xpos][self.ypos - 1].probOfW += (1 / possibleNumOfSpaces)
            else:
                #ASK HERE
                #there is no stench so make the propbability of W zero for the neighbors and the current space
                if ((self.xpos, self.ypos) in self.possible_wumpus):
                    self.possible_wumpus.remove((self.xpos, self.ypos))
                    self.checked_wumpus.append((self.xpos, self.ypos))

                neighbors = self.getNeighbors()

                for neighbor in neighbors:
                    neighbor[1].probOfW = 0
                    self.checked_wumpus.append((neighbor[1].xcoord, neighbor[1].ycoord))
                    if(neighbor[1].probOfP == 0):
                        self.safe.add((neighbor[1].xcoord, neighbor[1].ycoord))
                    if((neighbor[1].xcoord, neighbor[1].ycoord) in self.possible_wumpus):
                        self.possible_wumpus.remove((neighbor[1].xcoord, neighbor[1].ycoord))

            if (breeze):
                self.grid[self.xpos][self.ypos].breeze = 1
                if (self.xpos == 0 and self.ypos == 0):
                    # breeze at first space then leave
                    return Agent.Action.CLIMB

                # Update probOfP for neighbors. Exclude: explored spaces, known out of bound spaces.
                # TODO: This is probably not going to generate the most accurate probabilities...
                # As with the probOfW code, there is currently nothing in place that can REDUCE probability when given more information
                neighbors = self.getNeighbors()
                # there is a breeze so the neighbors have a probability of being a pit
                # however, if the neighbor has been checked and that means it has a probability of 0 for W or P then it is safe to enter
                # checked can also be the safe spaces since they are added when they are entered and if their probability is low
                possibleNumOfSpaces = 0
                above = below = right = left = 0

                for neighbor in neighbors:
                    if ( (neighbor[1].xcoord, neighbor[1].ycoord) not in self.checked_pits):
                        possibleNumOfSpaces += 1
                        self.possible_pits.append((neighbor[1].xcoord, neighbor[1].ycoord))
                        # right0, left1, below2, above3
                        if(neighbor[0] == 0):
                            right = 1
                        elif(neighbor[0] == 1):
                            left = 1
                        elif(neighbor[0] == 2):
                            below = 1
                        else: # neighbor[0] == 3
                            above = 1


               #
               #  if ( (self.xpos + 1) <= self.max_xpos and self.grid[self.xpos + 1][self.ypos].unexplored ):
               #      right = 1
               #  if ( (self.ypos + 1) <= self.max_ypos and self.grid[self.xpos][self.ypos + 1].unexplored ):
               #      above = 1
               #  if ( (self.xpos - 1) >= 0 and self.grid[self.xpos - 1][self.ypos].unexplored ):
               #      left = 1
               #  if ( (self.ypos - 1) >= 0 and self.grid[self.xpos][self.ypos - 1].unexplored ):
               #      below = 1
               #
               #  possibleNumOfSpaces = right + above + left + below
               #
               #
                if (possibleNumOfSpaces == 1):
                    if (right == 1):
                        self.grid[self.xpos + 1][self.ypos].probOfP = 1
                    elif (above == 1):
                        self.grid[self.xpos][self.ypos + 1].probOfP = 1
                    elif (left == 1):
                        self.grid[self.xpos - 1][self.ypos].probOfP = 1
                    else:
                        self.grid[self.xpos][self.ypos - 1].probOfP = 1
                elif ( possibleNumOfSpaces == 2):
                    if (right == 1):
                        self.grid[self.xpos + 1][self.ypos].probOfP += 0.5556
                    elif (above == 1):
                        self.grid[self.xpos][self.ypos + 1].probOfP += 0.5556
                    elif (left == 1):
                        self.grid[self.xpos - 1][self.ypos].probOfP += 0.5556
                    else:
                        self.grid[self.xpos][self.ypos - 1].probOfP += 0.5556
                else:
                    if (right == 1):
                        self.grid[self.xpos + 1][self.ypos].probOfP += 0.4098
                    elif (above == 1):
                        self.grid[self.xpos][self.ypos + 1].probOfP += 0.4098
                    elif (left == 1):
                        self.grid[self.xpos - 1][self.ypos].probOfP += 0.4098
                    else:
                        self.grid[self.xpos][self.ypos - 1].probOfP += 0.4098
            #ASK HERE
            else:
                #there is no breeze in the square then adjacent cannot be a pit
                if((self.xpos, self.ypos) in self.possible_pits):
                    self.possible_pits.remove((self.xpos, self.ypos))
                    self.checked_pits.append((self.xpos, self.ypos))

                neighbors = self.getNeighbors()
                for neighbor in neighbors:
                    neighbor[1].probOfP = 0 # cannot be a pit
                    self.checked_pits.append((neighbor[1].xcoord, neighbor[1].ycoord))
                    if(neighbor[1].probOfW == 0):
                        self.safe.add((neighbor[1].xcoord, neighbor[1].ycoord))
                    if ((neighbor[1].xcoord, neighbor[1].ycoord) in self.possible_pits):
                        self.possible_pits.remove((neighbor[1].xcoord, neighbor[1].ycoord))

        if glitter:
            self.time_to_leave = True
            return Agent.Action.GRAB

        if self.time_to_leave:	# Got the gold or ran out of time

            return self.returnFunction()

        else:
            self.blockedUpdate()
            if (self.moving == False): # Choose a new space
                # Assemble list of unvisited neighbors in ascending order of threat

                candidates = []

                if(breeze):
                    #there was a stench here better to go back and take a different route
                    if ((self.xpos + 1) <= self.max_xpos and (self.grid[self.xpos + 1][self.ypos].breeze == 0)):
                        candidates.append(self.grid[self.xpos + 1][self.ypos])
                    if ((self.ypos + 1) <= self.max_ypos and (self.grid[self.xpos][self.ypos + 1].breeze == 0)):
                        candidates.append(self.grid[self.xpos][self.ypos + 1])
                    if ((self.xpos - 1) >= 0 and (self.grid[self.xpos - 1][self.ypos].breeze == 0)):
                        candidates.append(self.grid[self.xpos - 1][self.ypos])
                    if ((self.ypos - 1) >= 0 and (self.grid[self.xpos][self.ypos - 1].breeze == 0)):
                        candidates.append(self.grid[self.xpos][self.ypos - 1])
                elif(stench):
                    # there was a stench here better to go back and take a different route
                    if ((self.xpos + 1) <= self.max_xpos and (self.grid[self.xpos + 1][self.ypos].stench == 0)):
                        candidates.append(self.grid[self.xpos + 1][self.ypos])
                    if ((self.ypos + 1) <= self.max_ypos and (self.grid[self.xpos][self.ypos + 1].stench == 0)):
                        candidates.append(self.grid[self.xpos][self.ypos + 1])
                    if ((self.xpos - 1) >= 0 and (self.grid[self.xpos - 1][self.ypos].stench == 0)):
                        candidates.append(self.grid[self.xpos - 1][self.ypos])
                    if ((self.ypos - 1) >= 0 and (self.grid[self.xpos][self.ypos - 1].stench == 0)):
                        candidates.append(self.grid[self.xpos][self.ypos - 1])

                else:
                    # choose a space that is unexplored and "safe"
                    if ( (self.xpos + 1) <= self.max_xpos and self.grid[self.xpos + 1][self.ypos].unexplored ):
                        candidates.append(self.grid[self.xpos + 1][self.ypos])
                    if ( (self.ypos + 1) <= self.max_ypos and self.grid[self.xpos][self.ypos + 1].unexplored ):
                        candidates.append(self.grid[self.xpos][self.ypos + 1])
                    if ( (self.xpos - 1) >= 0 and self.grid[self.xpos - 1][self.ypos].unexplored ):
                        candidates.append(self.grid[self.xpos - 1][self.ypos])
                    if ( (self.ypos - 1) >= 0 and self.grid[self.xpos][self.ypos - 1].unexplored ):
                        candidates.append(self.grid[self.xpos][self.ypos - 1])

                # if not candidates: # No new space to go to. Revisit a random neighbor (TODO: change this to back up to earlier branch in path)
                #     if ( (self.xpos + 1) <= self.max_xpos ):
                #         candidates.append(self.grid[self.xpos + 1][self.ypos])
                #     if ( (self.ypos + 1) <= self.max_ypos ):
                #         candidates.append(self.grid[self.xpos][self.ypos + 1])
                #     if ( (self.xpos - 1) >= 0 ):
                #         candidates.append(self.grid[self.xpos - 1][self.ypos])
                #     if ( (self.ypos - 1) >= 0 ):
                #         candidates.append(self.grid[self.xpos][self.ypos - 1])
                #
                #     random.shuffle(candidates)
                # else:
                candidates = sorted(candidates, key=lambda space: space.probOfP + space.probOfW)

                safe_candidates = [c for c in candidates if ( ((c.xcoord, c.ycoord) not in self.possible_pits) and ((c.xcoord, c.ycoord) not in self.possible_wumpus) and ((c.xcoord, c.ycoord) not in self.blocked_spaces) )]
                cnt = 0
                for c in safe_candidates:
                    if((c.xcoord, c.ycoord) in self.visited):
                        cnt += 1
                if(cnt == len(self.visited)):
                    return self.returnFunction()

                # for candidate in candidates:
                #     if(((candidate.xcoord, candidate.ycoord) in self.possible_pits) or ((candidate.xcoord, candidate.ycoord) in self.possible_wumpus)):
                #         candidates.remove(candidate)

                # print(candidates)
                # print(safe_candidates)
                # print("Pits: ", self.possible_pits)
                # print("Wumpus: ", self.possible_wumpus)
                if (len(safe_candidates) == 0):
                    # none safe then choose from candidates
                    #movingTo = candidates.pop(0)
                    # self.time_to_leave = True
                    # return self.returnFunction()
                    for c in candidates:
                        self.blocked_spaces.append((c.xcoord, c.ycoord))
                    candidates = self.exploredNeighbors()
                    candidates = sorted(candidates, key=lambda space: space.probOfP + space.probOfW)
                    movingTo = candidates.pop(0)
                else:
                    movingTo = safe_candidates.pop(0)
                # movingTo = safe_candidates.pop()
                # print(movingTo)

                if ( isFacingSpace(movingTo.xcoord, movingTo.ycoord, self.xpos, self.ypos, self.current_dir) ):
                    self.xpos, self.ypos = updatePos(self.current_dir, self.xpos, self.ypos)
                    self.route.append(Agent.Action.FORWARD) # TODO: Remove this when better return route is implemented
                    return Agent.Action.FORWARD
                else: # Initiate moving phase
                    self.moving = True
                    if (movingTo.xcoord == (self.xpos + 1) ): # Space is to the right
                        if (self.current_dir == 1):
                            self.current_dir = updateDirection(Agent.Action.TURN_LEFT, self.current_dir)
                            self.route.append(Agent.Action.TURN_RIGHT)
                            return Agent.Action.TURN_LEFT
                        elif (self.current_dir == 2):
                            self.movingToQ.append(Agent.Action.TURN_RIGHT)
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                        else: # current_dir == 3
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                    elif (movingTo.xcoord == (self.xpos - 1) ): # Space is to the left
                        if (self.current_dir == 0):
                            self.movingToQ.append(Agent.Action.TURN_RIGHT)
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                        elif (self.current_dir == 1):
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                        else: # current_dir == 3
                            self.current_dir = updateDirection(Agent.Action.TURN_LEFT, self.current_dir)
                            self.route.append(Agent.Action.TURN_RIGHT)
                            return Agent.Action.TURN_LEFT
                    elif (movingTo.ycoord == (self.ypos + 1) ): # Space is above
                        if (self.current_dir == 0):
                            self.current_dir = updateDirection(Agent.Action.TURN_LEFT, self.current_dir)
                            self.route.append(Agent.Action.TURN_RIGHT)
                            return Agent.Action.TURN_LEFT
                        elif (self.current_dir == 1):
                            self.movingToQ.append(Agent.Action.TURN_RIGHT)
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                        else: # current_dir == 2
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                    else: 										# Space is below
                        if (self.current_dir == 0):
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
                        elif (self.current_dir == 2):
                            self.current_dir = updateDirection(Agent.Action.TURN_LEFT, self.current_dir)
                            self.route.append(Agent.Action.TURN_RIGHT)
                            return Agent.Action.TURN_LEFT
                        else: # current_dir == 3
                            self.movingToQ.append(Agent.Action.TURN_RIGHT)
                            self.current_dir = updateDirection(Agent.Action.TURN_RIGHT, self.current_dir)
                            self.route.append(Agent.Action.TURN_LEFT)
                            return Agent.Action.TURN_RIGHT
            else: # Currently in moving phase
                if not self.movingToQ: # Should be facing space now
                    self.moving = False
                    self.xpos, self.ypos = updatePos(self.current_dir, self.xpos, self.ypos)
                    self.route.append(Agent.Action.FORWARD) # TODO: Remove this when better return route is implemented
                    return Agent.Action.FORWARD
                else:
                    nextTurn = self.movingToQ.pop()
                    self.current_dir = updateDirection(nextTurn, self.current_dir)
                    if (nextTurn == Agent.Action.TURN_RIGHT):
                        self.route.append(Agent.Action.TURN_LEFT)
                    else:
                        self.route.append(Agent.Action.TURN_RIGHT)
                    return nextTurn

    def getNeighbors(self):
        # returns a list of unvisited neighbors space objects
        neighbors = []

        if ( (self.xpos + 1) <= self.max_xpos and self.grid[self.xpos + 1][self.ypos].unexplored ):
            # right
            neighbors.append([0, self.grid[self.xpos + 1][self.ypos]])
        if ( (self.ypos + 1) <= self.max_ypos and self.grid[self.xpos][self.ypos + 1].unexplored ):
            # above
            neighbors.append([3, self.grid[self.xpos][self.ypos + 1]])
        if ( (self.xpos - 1) >= 0 and self.grid[self.xpos - 1][self.ypos].unexplored ):
            # left
            neighbors.append([1, self.grid[self.xpos - 1][self.ypos]])
        if ( (self.ypos - 1) >= 0 and self.grid[self.xpos][self.ypos - 1].unexplored ):
            # below
            neighbors.append([2, self.grid[self.xpos][self.ypos - 1]])

        return neighbors

    def path_print(self, path):
        board = [[-1 for col in range(7)] for row in range(7)]
        for i in range(self.max_xpos):
            for j in range(self.max_ypos):
                if(self.grid[i][j].unexplored):
                    #not explored
                    board[i][j] = -2
        start_value = 0
        for index, item in enumerate(path):
            board[item[0]][item[1]] = start_value
            start_value += 1
        print('\n'.join([''.join(['{:4}'.format(item) for item in row])
                         for row in board]))

    def returnASearch(self):
        #if they are unexplored then consider them "blocked" or "forbidden"
        #print("here")
        start_node = self.grid[self.xpos][self.ypos] # current node = start node
        start_node.g = start_node.h = start_node.f = 0
        #print(start_node)
        end_node = self.grid[0][0] # 0,0 is the exit = end node
        end_node.g = end_node.h = end_node.f = 0
        #print(end_node)
        direction = self.current_dir

        yet_to_visit_list = []
        visited_list = []
        #add current/start node to the yet to visit list
        yet_to_visit_list.append(start_node)

        while len(yet_to_visit_list) > 0:
            current_node = yet_to_visit_list[0]
            current_index = 0
            xcoord = current_node.xcoord
            ycoord = current_node.ycoord
            for index, item in enumerate(yet_to_visit_list):
                if ( item.f < current_node.f):
                    # continue looping until find the smallest f value
                    direction = getDirection(xcoord, ycoord, item.xcoord, item.ycoord) # gives us the direction we will face when we choose that space
                    current_node = item
                    current_index = index
            yet_to_visit_list.pop(current_index)
            visited_list.append(current_node) # visit the node with the smallest f(n)

            if( current_node == end_node ):
                #print("here")
                break

            neighbors = self.getSafeNeighbors()

            for neighbor in neighbors:
                #neighbor is in the visited list
                if (len([visited_neighbor for visited_neighbor in visited_list if ( visited_neighbor == neighbor[1] ) ]) > 0):
                    continue

                #create f, g, h costs for the neighbor
                neighbor[1].g = current_node.g + 1
                #neighbor[1].g = current_node.g + calculateDirection(direction, getDirection(current_node.xcoord, current_node.ycoord, neighbor[1].xcoord, neighbor[1].ycoord))
                neighbor[1].f = neighbor[1].g + neighbor[1].h

                # check neighbor is in yet_to_visit_list and g_cost
                if (len([n for n in yet_to_visit_list if ( neighbor[1] == n and neighbor[1].g > n.g ) ]) > 0):
                    continue
                yet_to_visit_list.append(neighbor[1])
        return_route = []
        for node in visited_list:
            return_route.append([node.xcoord, node.ycoord])
        return return_route

    def returnFunction(self):
        # when time to leave call this
        if (self.xpos == 0 and self.ypos == 0):  # Agent is at (0,0) & it's time to go!
            return Agent.Action.CLIMB

            # Get agent to 180-turn to get oriented for return trip
        if ((not self.first_F_found) and (self.route[len(self.route) - 1] == Agent.Action.FORWARD)):
            return_route = self.returnASearch()
            # print(return_route)
            # print(self.route)
            # print(self.safe)
            # self.path_print(return_route)
            self.first_F_found = True
            self.route.append(Agent.Action.TURN_RIGHT)
            self.route.append(Agent.Action.TURN_RIGHT)

        nextMove = self.route.pop()

        # If agent will be moving forward, update xpos & ypos
        # Else update direction
        if (nextMove == Agent.Action.FORWARD):
            self.xpos, self.ypos = updatePos(self.current_dir, self.xpos, self.ypos)
        else:
            self.current_dir = updateDirection(nextMove, self.current_dir)

        return nextMove

        #TODO: implement what to do in case of a tie - choose the smaller column number if the same, then choose the smaller row number if columns are the same

    def exploredNeighbors(self):
        neighbors = []

        if ((self.xpos + 1) <= self.max_xpos and self.grid[self.xpos + 1][self.ypos].unexplored == 0):
            neighbors.append(self.grid[self.xpos + 1][self.ypos])
        if ((self.ypos + 1) <= self.max_ypos and self.grid[self.xpos][self.ypos + 1].unexplored == 0):
            neighbors.append(self.grid[self.xpos][self.ypos + 1])
        if ((self.xpos - 1) >= 0 and self.grid[self.xpos - 1][self.ypos].unexplored == 0):
            neighbors.append(self.grid[self.xpos - 1][self.ypos])
        if ((self.ypos - 1) >= 0 and self.grid[self.xpos][self.ypos - 1].unexplored == 0):
            neighbors.append(self.grid[self.xpos][self.ypos - 1])

        return neighbors

    def blockedUpdate(self):
        # go through the blocked spaces list and check the neighbors and if the len of safe neighbors is > 1 then remove it from the blocked spaces
        for b in list.copy(self.blocked_spaces):
            candidates = []

            if ((b[0] + 1) <= self.max_xpos and self.grid[b[0] + 1][b[1]].unexplored):
                candidates.append(self.grid[b[0] + 1][b[1]])
            if ((b[1] + 1) <= self.max_ypos and self.grid[b[0]][b[1] + 1].unexplored):
                candidates.append(self.grid[b[0]][b[1] + 1])
            if ((b[0] - 1) >= 0 and self.grid[b[0] - 1][b[1]].unexplored):
                candidates.append(self.grid[b[0] - 1][b[1]])
            if ((b[1] - 1) >= 0 and self.grid[b[0]][b[1] - 1].unexplored):
                candidates.append(self.grid[b[0]][b[1] - 1])

            safe_candidates = [c for c in candidates if (((c.xcoord, c.ycoord) not in self.possible_pits) and (
                        (c.xcoord, c.ycoord) not in self.possible_wumpus) )]
            if(len(safe_candidates) > 1):
                self.blocked_spaces.remove(b)

    def getSafeNeighbors(self):
        # returns a list of unvisited neighbors space objects
        neighbors = []

        if ( (self.xpos + 1) <= self.max_xpos and ((self.xpos + 1),self.ypos) in self.safe):
            # right
            neighbors.append([0, self.grid[self.xpos + 1][self.ypos]])
        if ( (self.ypos + 1) <= self.max_ypos and (self.xpos,(self.ypos + 1)) in self.safe):
            # above
            neighbors.append([3, self.grid[self.xpos][self.ypos + 1]])
        if ( (self.xpos - 1) >= 0 and ((self.xpos - 1),self.ypos) in self.safe):
            # left
            neighbors.append([1, self.grid[self.xpos - 1][self.ypos]])
        if ( (self.ypos - 1) >= 0 and (self.xpos,(self.ypos - 1)) in self.safe):
            # below
            neighbors.append([2, self.grid[self.xpos][self.ypos - 1]])

        return neighbors
