from libtcod import libtcodpy as libtcod
from consts import *


class Painter:
    __painter = None

    @staticmethod
    def get_instance():
        if Painter.__painter is None:
            Painter()
        return Painter.__painter

    def __init__(self):
        # Secondary console to draw on
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
        Painter.__painter = self

    def flush(self):
        libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()


class GamePainter:
    def __init__(self, owner=None):
        self.owner = owner

    def draw(self):
        self.owner.game_map.draw()

        for obj in self.owner.game_map.objects:
            obj.painter.draw()

        Painter.get_instance().flush()


class ObjectPainter:
    def __init__(self, obj_type=None, owner=None):
        self.owner = owner
        self.obj_type = obj_type

    def __draw_obj(self, char, color):
        libtcod.console_set_default_foreground(Painter.get_instance().con, color)
        libtcod.console_put_char(Painter.get_instance().con, self.owner.x, self.owner.y, char, libtcod.BKGND_NONE)

    def draw(self):
        if self.owner.visible:
            if self.obj_type == 'player':
                self.__draw_obj('@', libtcod.blue)
            elif self.obj_type == 'orc':
                self.__draw_obj('o', libtcod.desaturated_green)
            elif self.obj_type == 'troll':
                self.__draw_obj('T', libtcod.darker_green)
            elif self.obj_type == 'boss':
                self.__draw_obj('@', libtcod.red)
            else:
                raise Exception("{} is not a valid obj_type for the ObjectPainter.".format(self.obj_type))


class TilePainter:
    def __init__(self, owner=None):
        self.owner = owner

    def draw(self):
        if self.owner.seen:
            if self.owner.block_sight:
                # Draw wall
                if self.owner.visible:
                    libtcod.console_put_char_ex(Painter.get_instance().con, self.owner.x, self.owner.y, '#', libtcod.darkest_gray, libtcod.darkest_yellow)
                else:
                    libtcod.console_put_char_ex(Painter.get_instance().con, self.owner.x, self.owner.y, '#', libtcod.darkest_gray, libtcod.black)
            else:
                # Draw floor
                if self.owner.visible:
                    libtcod.console_put_char_ex(Painter.get_instance().con, self.owner.x, self.owner.y, ' ', libtcod.white, libtcod.light_yellow)
                else:
                    libtcod.console_put_char_ex(Painter.get_instance().con, self.owner.x, self.owner.y, ' ', libtcod.white, libtcod.darker_gray)
