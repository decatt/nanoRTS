from pos import Pos

def astar_search(start_pos:Pos, end_pos:Pos, obstacle:list[Pos])->Pos:
    open_list = [start_pos]
    close_list = []
    g = {start_pos:0}
    f = {start_pos:g[start_pos]+start_pos.distance(end_pos)}
    parent = {start_pos:None}
    while len(open_list) > 0:
        current_pos = min(f, key=f.get)
        if current_pos == end_pos:
            return get_path(parent, current_pos)
        open_list.remove(current_pos)
        close_list.append(current_pos)
        for neighbor_pos in get_neighbor(current_pos):
            if neighbor_pos in close_list:
                continue
            if neighbor_pos in obstacle:
                continue
            if neighbor_pos not in open_list:
                open_list.append(neighbor_pos)
                g[neighbor_pos] = g[current_pos] + current_pos.distance(neighbor_pos)
                f[neighbor_pos] = g[neighbor_pos] + neighbor_pos.distance(end_pos)
                parent[neighbor_pos] = current_pos
            else:
                if g[current_pos] + current_pos.distance(neighbor_pos) < g[neighbor_pos]:
                    g[neighbor_pos] = g[current_pos] + current_pos.distance(neighbor_pos)
                    f[neighbor_pos] = g[neighbor_pos] + neighbor_pos.distance(end_pos)
                    parent[neighbor_pos] = current_pos
    return None

def get_path(parent:dict[Pos,Pos], current_pos:Pos)->Pos:
    path = []
    while current_pos is not None:
        path.append(current_pos)
        current_pos = parent[current_pos]
    return path[::-1]

def get_neighbor(pos:Pos)->list[Pos]:
    neighbor = []
    neighbor.append(pos + Pos(0,1))
    neighbor.append(pos + Pos(1,0))
    neighbor.append(pos + Pos(0,-1))
    neighbor.append(pos + Pos(-1,0))
    return neighbor