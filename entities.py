from libtcod import libtcodpy as libtcod
from consts import *
import game
import painter


class Object:
    def __init__(self, x, y, char, color, blocks=False, speed=DEFAULT_SPEED):
        self.x = x
        self.y = y
        self.blocks = blocks
        self.char = char
        self.color = color
        self.is_player = False
        self.seen = True
        self.speed = speed
        self.wait = libtcod.random_get_int(0, 0, speed)

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

    def draw(self):
        # Draw the player
        painter.Painter.get_instance().draw_object(self.x, self.y, char=self.char, color=self.color, visible=game.GameManager.get_instance().calculate_visibility(self))

