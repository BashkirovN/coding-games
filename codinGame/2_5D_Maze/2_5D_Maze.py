import sys
from collections import deque

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.
OVER = 'over'
NEUTRAL = 'neutral'
DIR_VERT = 'moving verticaly'
DIR_HOR = 'moving horizontally'
 
NEUTRAL_PASSIBLE = ['.', 'O', 'X', '|', '-']
OVER_PASSIBLE = ['+', 'X', '|', '-']
SLOPES = ['|', '-']

class Node:
    visited = False
    def __init__(self, x, y, steps=0, level=NEUTRAL):
        self.x = x
        self.y = y
        self.level = level
        self.steps = steps

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.level == other.level
    
    def __str__(self):
        return f"({self.x},{self.y}) {self.level}, {self.steps}"

starty, startx = [int(i) for i in input().split()]
endy, endx = [int(i) for i in input().split()]
h, w = [int(i) for i in input().split()]

lab = []
visited = []
q = deque([Node(startx, starty)])

for i in range(h):
    line = input()
    if i == starty:
        line = line[:startx] + '@' + line[startx + 1:]
    lab.append(line)
    print(line, file=sys.stderr, flush=True)

def valid(x, y):
    global w, h
    return 0 <= x < w and 0<= y < h

def validSlopeFace(dir, cell):
    return cell == '|' and dir == DIR_VERT or cell == '-' and dir == DIR_HOR

def canMove(x, y, level, dir):
    global lab
    cell = lab[y][x]
    if level == NEUTRAL and cell in NEUTRAL_PASSIBLE:
        if cell in SLOPES and not validSlopeFace(dir, cell):
            return None
        return OVER if cell in SLOPES else NEUTRAL

    elif level == OVER and cell in OVER_PASSIBLE:
        if cell in SLOPES and not validSlopeFace(dir, cell):
            return None
        return NEUTRAL if cell in SLOPES else OVER
    else:
        return None



# Write an answer using print
# To debug: print("Debug messages...", file=sys.stderr, flush=True)

# Bfs
while q:
    cur = q.popleft()
    cur_cell = lab[cur.y][cur.x]

    if cur.x == endx and cur.y == endy:
        print(cur.steps)
        break

    visited.append(cur)

    # Right
    if valid(cur.x+1, cur.y) and cur_cell != '|':
        newLevel = canMove(cur.x+1, cur.y, cur.level, DIR_HOR)
        if newLevel:
            n = Node(cur.x+1, cur.y, cur.steps+1, newLevel)
            if n not in visited:
                q.append(n)
    
    # Left
    if valid(cur.x-1, cur.y) and cur_cell != '|':
        newLevel = canMove(cur.x-1, cur.y, cur.level, DIR_HOR)
        if newLevel:
            n = Node(cur.x-1, cur.y, cur.steps+1, newLevel)
            if n not in visited:
                q.append(n)
    
    # Down
    if valid(cur.x, cur.y+1) and cur_cell != '-':
        newLevel = canMove(cur.x, cur.y+1, cur.level, DIR_VERT)
        if newLevel:
            n = Node(cur.x, cur.y+1, cur.steps+1, newLevel)
            if n not in visited:
                q.append(n)
    
    # Up
    if valid(cur.x, cur.y-1) and cur_cell != '-':
        newLevel = canMove(cur.x, cur.y-1, cur.level, DIR_VERT)
        if newLevel:
            n = Node(cur.x, cur.y-1, cur.steps+1, newLevel)
            if n not in visited:
                q.append(n)

