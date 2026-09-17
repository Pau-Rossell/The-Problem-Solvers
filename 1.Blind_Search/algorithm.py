import random

"""
Return (path, expanded, exploration): path includes start and goal; expanded counts visited nodes.

grid: NumPy array, grid[row, column], 0 = free, 1 = obstacle.
start, goal: (row, column). Only up/down/left/right moves are allowed.
Return ([], expanded, exploration) when no path exists.
"""
# DFS(Use .pop(-1))
def blind_search(grid, start, goal, strategy):
    # random search demo starts
    frontier = [start]
    parent = {start: None}
    expanded = 0
    exploration = []

    strategy = strategy.upper()
    if strategy not in ['DFS', 'BFS']:
        raise ValueError("Invalid strategy. Use 'DFS' or 'BFS'.")

    while frontier:
        
        if strategy == 'DFS':
            current = frontier.pop(-1) # LIFO
        elif strategy == 'BFS':
            current = frontier.pop(0) # FIFO

        expanded += 1
        exploration.append(current)

        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            return path[::-1], expanded, exploration

        r, c = current
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (r + dr, c + dc)
            nr, nc = neighbor
            if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[neighbor] == 0 and neighbor not in parent:
                parent[neighbor] = current
                frontier.append(neighbor)

    # random search demo ends
    return [], expanded, exploration

def solve(grid, start, goal):
    return blind_search(grid, start, goal, strategy='BFS') # DFS or BFS

# BFS(He eliminado el for loop porque no era necesario)(Use .pop(0))
# def solve(grid, start, goal):
#     frontier = [start]
#     parent = {start: None}
#     expanded = 0
#     exploration = []

#     while frontier:
        
#         current = frontier.pop(0) # FIFO
        
#         expanded += 1
#         exploration.append(current)

#         if current == goal:
#             path = []
#             while current is not None:
#                 path.append(current)
#                 current = parent[current]
#             return path[::-1], expanded, exploration

#         r, c = current
#         for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
#             neighbor = (r + dr, c + dc)
#             nr, nc = neighbor
#             if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[neighbor] == 0 and neighbor not in parent:
#                 parent[neighbor] = current
#                 frontier.append(neighbor)

#     # random search demo ends
#     return [], expanded, exploration