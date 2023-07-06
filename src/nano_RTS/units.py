import numpy as np
import json
from pos import Pos
from player import Player
from dataclasses import dataclass

class UnitType:
    def __init__(self) -> None:
        self.id = 0
        self.name = ""
        self.cost = 0
        self.hp = 0
        self.minDamage = 0
        self.maxDamage = 0
        self.attackRange = 0
        self.produceTime = 0
        self.moveTime = 0
        self.attackTime = 0
        self.harvestTime = 0
        self.returnTime = 0
        self.harvestAmount = 0
        self.sightRadius = 0
        self.isResource = False
        self.isStockpile = False
        self.canHarvest = False
        self.canMove = False
        self.canAttack = False
        self.produces = []
        self.producedBy = []

class Unit:
    def __init__(self,unit_id:int,player_id:int, pos:int, map_width:int, unit_type:UnitType, resources:int = 0) -> None:
        self.unit_id = unit_id
        self.player_id = player_id
        self.pos = pos
        self.unit_type = unit_type
        self.current_hp = unit_type.hp
        self.current_action = None
        self.execute_current_action_time = 0
        self.current_action_target = -1
        self.carried_resource = resources
        self.building_unit_type = None
        self.width = map_width

    def busy(self):
        return self.current_action is not None

def load_unit_types(path='UnitTypeTable.json'):
    with open(path, 'r') as f:
        data = json.load(f)
    uint_types_json = data['unitTypes']
    unit_types = dict()
    for uint_type_json in uint_types_json:
        uint_type = UnitType()
        uint_type.id = uint_type_json['ID']
        uint_type.name = uint_type_json['name']
        uint_type.cost = uint_type_json['cost']
        uint_type.hp = uint_type_json['hp']
        uint_type.minDamage = uint_type_json['minDamage']
        uint_type.maxDamage = uint_type_json['maxDamage']
        uint_type.attackRange = uint_type_json['attackRange']
        uint_type.produceTime = uint_type_json['produceTime']
        uint_type.moveTime = uint_type_json['moveTime']
        uint_type.attackTime = uint_type_json['attackTime']
        uint_type.harvestTime = uint_type_json['harvestTime']
        uint_type.returnTime = uint_type_json['returnTime']
        uint_type.harvestAmount = uint_type_json['harvestAmount']
        uint_type.sightRadius = uint_type_json['sightRadius']
        uint_type.isResource = uint_type_json['isResource']
        uint_type.isStockpile = uint_type_json['isStockpile']
        uint_type.canHarvest = uint_type_json['canHarvest']
        uint_type.canMove = uint_type_json['canMove']
        uint_type.canAttack = uint_type_json['canAttack']
        uint_type.produces = uint_type_json['produces']
        uint_type.producedBy = uint_type_json['producedBy']
        unit_types[uint_type.name] = uint_type
    unit_type_terrain = UnitType()
    unit_type_terrain.id = -1
    unit_type_terrain.name = 'terrain'
    unit_type_terrain.cost = 1
    unit_type_terrain.hp = 1000000
    unit_type_terrain.minDamage = 1
    unit_type_terrain.maxDamage = 1
    unit_type_terrain.attackRange = 1
    unit_type_terrain.produceTime = 10
    unit_type_terrain.moveTime = 10
    unit_type_terrain.attackTime = 10
    unit_type_terrain.harvestTime = 10
    unit_type_terrain.returnTime = 10
    unit_type_terrain.harvestAmount = 1
    unit_type_terrain.sightRadius = 0
    unit_type_terrain.isResource = False
    unit_type_terrain.isStockpile = False
    unit_type_terrain.canHarvest = False
    unit_type_terrain.canMove = False
    unit_type_terrain.canAttack = False
    unit_type_terrain.produces = []
    unit_type_terrain.producedBy = []
    unit_types['terrain'] = unit_type_terrain
    return unit_types
