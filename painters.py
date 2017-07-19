from libtcod import libtcodpy as libtcod
from consts import *


class GamePainter:
    def __init__(self, owner=None):
        self.owner = owner
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    def draw(self):
        # Draw map
        for x in range(self.owner.game_map.width):
            for y in range(self.owner.game_map.height):
                self.owner.game_map.tiles[x][y].painter.draw(self.con)

        # Draw objects
        for obj in self.owner.game_map.objects:
            obj.painter.draw(self.con)

        # Flush con to default console
        libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()


class ObjectPainter:
    def __init__(self, obj_type=None, owner=None):
        self.owner = owner
        self.obj_type = obj_type

    def __draw_obj(self, con, char, color):
        libtcod.console_set_default_foreground(con, color)
        libtcod.console_put_char(con, self.owner.x, self.owner.y, char, libtcod.BKGND_NONE)

    def draw(self, con):
        if self.owner.visible:
            if self.obj_type == 'player':
                self.__draw_obj(con, '@', libtcod.blue)
            elif self.obj_type == 'orc':
                self.__draw_obj(con, 'o', libtcod.desaturated_green)
            elif self.obj_type == 'troll':
                self.__draw_obj(con, 'T', libtcod.darker_green)
            elif self.obj_type == 'boss':
                self.__draw_obj(con, '@', libtcod.red)
            else:
                raise Exception("{} is not a valid obj_type for the ObjectPainter.".format(self.obj_type))


class TilePainter:
    def __init__(self, owner=None):
        self.owner = owner

    def draw(self, con):
        if self.owner.seen:
            if self.owner.block_sight:
                # Draw wall
                if self.owner.visible:
                    libtcod.console_put_char_ex(con, self.owner.x, self.owner.y, '#', libtcod.darkest_gray, libtcod.darkest_yellow)
                else:
                    libtcod.console_put_char_ex(con, self.owner.x, self.owner.y, '#', libtcod.darkest_gray, libtcod.black)
            else:
                # Draw floor
                if self.owner.visible:
                    libtcod.console_put_char_ex(con, self.owner.x, self.owner.y, ' ', libtcod.white, libtcod.light_yellow)
                else:
                    libtcod.console_put_char_ex(con, self.owner.x, self.owner.y, ' ', libtcod.white, libtcod.darker_gray)
