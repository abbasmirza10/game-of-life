from collections import Counter


def get_live_neighbors(x, y, rows, height):
    return [rows[ny][nx] for dx in [-1, 0, 1] for dy in [-1, 0, 1] 
            if not(dx == 0 and dy == 0) 
            and 0 <= (ny := y + dy) < height 
            and 0 <= (nx := x + dx) < len(rows[ny]) 
            and rows[ny][nx] != ' ']

def get_next_row(y, rows, height):
    width = max(len(row) for row in rows)
    return ''.join(rows[y][x] if x < len(rows[y]) and rows[y][x] != ' ' and (len(get_live_neighbors(x, y, rows, height)) in [2, 3]) 
                   else min(get_live_neighbors(x, y, rows, height)) if x < len(rows[y]) and rows[y][x] == ' ' and len(get_live_neighbors(x, y, rows, height)) == 3 
                   else ' ' if x < width else '' 
                   for x in range(width))

def life_alphabet(pattern):
    rows = pattern.split('\n')
    height = len(rows)
    next_rows = [get_next_row(y, rows, height).rstrip() + ' ' * (max(len(row) for row in rows) - len(get_next_row(y, rows, height).rstrip())) for y in range(height)]
    return '\n'.join(next_rows).rstrip(' ')


def life_ring(width, height, ticks, border):
    def get_neighbors(x, y):
        return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]

    def parse_border(border):
        border_map = {}
        border_iter = iter(border)
        for x in range(-1, width + 1):
            border_map[(x, -1)] = next(border_iter)
        for y in range(height):
            border_map[(width, y)] = next(border_iter)
        for x in range(width, -1, -1):
            border_map[(x, height)] = next(border_iter)
        for y in range(height - 1, -1, -1):
            border_map[(-1, y)] = next(border_iter)
        return border_map

    def get_new_generation(current):
        neighbor_count = Counter()
        for x, y in current:
            for nx, ny in get_neighbors(x, y):
                neighbor_count[(nx, ny)] += 1
        return {(x, y) for (x, y), count in neighbor_count.items() if count == 3 or (count == 2 and (x, y) in current)}

    border_map = parse_border(border)
    current = {(x, y) for (x, y), state in border_map.items() if state == '#'}
    for _ in range(ticks):
        current = get_new_generation(current)
        current.update((x, y) for (x, y), state in border_map.items() if state == '#')
        current.difference_update((x, y) for (x, y), state in border_map.items() if state == ' ')
    return '\n'.join(''.join('#' if (x, y) in current else ' ' for x in range(width)) for y in range(height)) + '\n'