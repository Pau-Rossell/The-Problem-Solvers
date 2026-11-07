from heapq import heappop, heappush
from math import sqrt

# Available heuristics. Select one with: python run.py --heuristic <name> [--weight W]
# The heuristic value is multiplied by W (default 1). W > 1 is no longer admissible:
# fewer expansions, but the returned path may be longer than optimal.
HEURISTICS = {
    'zero':      lambda p, g: 0,
    'manhattan': lambda p, g: abs(p[0] - g[0]) + abs(p[1] - g[1]),
    'euclidean': lambda p, g: sqrt((p[0] - g[0])**2 + (p[1] - g[1])**2),
}

def solve(grid, start, goal, heuristic='euclidean', weight=1.0):
    # Modify the h function, monitor how the changes affect performance, and discuss the observed results.
    if heuristic not in HEURISTICS:
        raise ValueError(f'unknown heuristic {heuristic!r}; choose from {sorted(HEURISTICS)}')
    if weight < 0:
        raise ValueError('weight must be >= 0')
    h_fn = HEURISTICS[heuristic]

    def h(position):
        return weight * h_fn(position, goal)

    frontier = [(h(start), 0, start)]
    parent = {start: None}
    cost = {start: 0}
    expanded = 0
    exploration = []

    while frontier:
        _, current_cost, current = heappop(frontier)
        if current_cost != cost[current]:
            continue

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
            if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[neighbor] == 0:
                new_cost = current_cost + 1
                if new_cost < cost.get(neighbor, float('inf')):
                    cost[neighbor] = new_cost
                    parent[neighbor] = current
                    heappush(frontier, (new_cost + h(neighbor), new_cost, neighbor))

    return [], expanded, exploration
