import numpy as np
from xml.dom import minidom

class Pos:
    def __init__(self, x, y, width = None):
        self.x = x
        self.y = y
        self.w = width
        if width is not None:
            self.int_pos = self.x + self.y * self.w
        else:
            self.int_pos = None

    def __eq__(self, __value: object) -> bool:
        return self.x == __value.x and self.y == __value.y
    
    def __add__(self, __value: object) -> object:
        return Pos(self.x + __value.x, self.y + __value.y)
    
    def next_pos(self, dir:'Pos')->'Pos':
        return self + dir
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def pos_dir_to_int_dir(self)->int:
        if self.x == 0 and self.y == 1:
            return 0
        elif self.x == 1 and self.y == 0:
            return 1
        elif self.x == 0 and self.y == -1:
            return 2
        elif self.x == -1 and self.y == 0:
            return 3
        else:
            return -1
        
def next_int_pos(int_pos:int, dir:Pos, width:int)->int:
    int_pos_x = int_pos % width
    int_pos_y = int_pos // width
    int_pos_x += dir.x
    int_pos_y += dir.y
    return int_pos_x + int_pos_y * width

def is_in_range(int_pos1:int,int_pos2:int,width:int,range:int):
    int_pos_x1 = int_pos1 % width
    int_pos_y1 = int_pos1 // width
    int_pos_x2 = int_pos2 % width
    int_pos_y2 = int_pos2 // width
    d = abs(int_pos_x1 - int_pos_x2) + abs(int_pos_y1 - int_pos_y2)
    if d <= range and d > 0:
        return True
    else:
        return False
        
    
