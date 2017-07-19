import math

from libtcod import libtcodpy as libtcod
from consts import *


class Object:
    def __init__(self, name, x, y, blocks=True, speed=DEFAULT_SPEED, fighter=None, ai=None, painter=None):
        self.name = name
        self.x = x
        self.y = y
        self.blocks = blocks
        self.is_player = False
        self.seen = True
        self.visible = False
        self.speed = speed
        self.wait = libtcod.random_get_int(0, 0, speed)
        self.game_map = None

        self.fighter = fighter
        if fighter is not None:
            fighter.owner = self

        self.ai = ai
        if ai is not None:
            ai.owner = self

        self.painter = painter
        if painter is not None:
            painter.owner = self

    def distance(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance_to(self, other):
        # return the distance to another object
        return self.distance(other.x, other.y)

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = self.distance(target_x, target_y)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def move(self, dx, dy):
        if not self.game_map.is_occupied(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_or_attack(self, dx, dy):
        if self.wait > 0:
            return
        self.wait = self.speed

        if not self.game_map.is_occupied(self.x + dx, self.y + dy):
            self.move(dx, dy)
        else:
            occupier = self.game_map.get_occupier(self.x + dx, self.y + dy)
            if occupier and occupier.fighter:
                occupier.fighter.attack(occupier)


class Fighter:
    def __init__(self, hp, defense, power):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            target.fighter.take_damage(damage)
            print "{} attacks {} and takes {} hp ({}/{}hp).".format(self.owner.name.capitalize(), target.name, str(damage), str(target.fighter.hp), str(target.fighter.max_hp))
        else:
            print "{} tickles {}, the poor thing.".format(self.owner.name.capitalize(), target.name)


class BasicMonster:
    def __init__(self):
        self.owner = None

    def take_turn(self):
        monster = self.owner
        player = monster.game_map.player

        if monster.wait > 0:
            return
        monster.wait = monster.speed

        if monster.visible:
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            else:
                if monster.fighter:
                    monster.fighter.attack(player)
                else:
                    print "The {} growls.".format(self.owner.name)

