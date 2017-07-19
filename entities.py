from libtcod import libtcodpy as libtcod
from consts import *
import game
import painters


class Object:
    def __init__(self, x, y, blocks=False, speed=DEFAULT_SPEED, painter=None):
        self.x = x
        self.y = y
        self.blocks = blocks
        self.is_player = False
        self.seen = True
        self.visible = False
        self.speed = speed
        self.wait = libtcod.random_get_int(0, 0, speed)
        self.painter = painter
        if painter is not None:
            painter.owner = self

    def move_or_attack(self, dx, dy):
        if self.wait > 0:
            return
        occupier = game.GameManager.get_instance().game_map.get_occupier(self.x + dx, self.y + dy)
        if occupier is None:
            self.x += dx
            self.y += dy
        elif isinstance(occupier, Object):
            # TODO ATTACK!
            pass
        self.wait = self.speed