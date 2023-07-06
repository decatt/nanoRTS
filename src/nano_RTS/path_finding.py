from pos import Pos
class PathFinding:
    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
    
    def find_path(self, start:Pos, target:Pos, obstacles:set, ignore_target:bool = True)->list:
        pass

    def next_pos(self, current:Pos, target:Pos, obstacles:set, find_range:int,ignore_target:bool = True)->Pos:
        pass

class BFS(PathFinding):
    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
        self.visited = set()
        self.queue = []
        self.parent = dict()
        self.directions = [Pos(0,1),Pos(1,0),Pos(0,-1),Pos(-1,0)]

    def score(self, pos:Pos, target:Pos)->int:
        return abs(pos.x - target.x) + abs(pos.y - target.y)
    
    def find_path(self, start:Pos, target:Pos, obstacles:set, ignore_target:bool = True):
        if target in obstacles and ignore_target:
            obstacles.remove(target)
        self.visited.clear()
        self.queue.clear()
        self.parent.clear()
        self.queue.append(start)
        self.visited.add(start)
        while len(self.queue) > 0:
            current = self.queue.pop(0)
            if current == target:
                path = []
                while current != start:
                    path.append(current)
                    current = self.parent[current]
                path.reverse()
                return path
            for dir in self.directions:
                next_pos = current + dir
                if next_pos.x < 0 or next_pos.x >= self.width or next_pos.y < 0 or next_pos.y >= self.height:
                    continue
                if next_pos in obstacles:
                    continue
                if next_pos in self.visited:
                    continue
                self.queue.append(next_pos)
                self.visited.add(next_pos)
                self.parent[next_pos] = current
        return None
    
    def get_neighbors_closest_to_target(self, pos:Pos, traget:Pos, obstacles:set)->Pos:
        closest = None
        closest_score = 100000000
        for dir in self.directions:
            next_pos = pos + dir
            if next_pos.x < 0 or next_pos.x >= self.width or next_pos.y < 0 or next_pos.y >= self.height:
                continue
            if next_pos in obstacles:
                continue
            score = self.score(next_pos, traget)
            if score < closest_score:
                closest_score = score
                closest = next_pos
        return closest

    
    def next_pos(self, current:Pos, target:Pos, obstacles:set, find_range:int = 6,ignore_target:bool = True)->Pos:
        next_pos = None
        if current.distance(target) > find_range:
            next_pos = self.get_neighbors_closest_to_target(current, target, obstacles)
        else:
            path = self.find_path(current, target, obstacles, ignore_target)
            if path is None or len(path) == 0:
                next_pos = self.get_neighbors_closest_to_target(current, target, obstacles)
            else:
                next_pos = path[0]
        if next_pos is None:
            return current
        return next_pos

if __name__ == "__main__":
    h = 4
    w = 4
    maze = [[0,0,0,0],
            [0,1,1,0],
            [0,1,1,0],
            [0,1,0,1]]
    obstacles = set()
    for i in range(h):
        for j in range(w):
            if maze[i][j] == 1:
                obstacles.add(Pos(j,i,w))
    bfs = BFS(w,h)
    current = Pos(0,0,w)
    target = Pos(3,3,w)
    while current != target:
        print(current)
        current = bfs.find_path(current, target, obstacles)[0]


