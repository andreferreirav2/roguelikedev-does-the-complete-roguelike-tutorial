from libtcod import libtcodpy as libtcod
from consts import *


class GamePainter:
    def __init__(self, owner=None):
        self.owner = owner
        self.con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
        self.panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

    def draw(self):
        # Draw map
        for x in range(self.owner.map.width):
            for y in range(self.owner.map.height):
                self.owner.map.tiles[x][y].painter.draw(self.con)

        # Draw objects
        for obj in self.owner.map.objects:
            obj.painter.draw(self.con)

        # Draw the GUI
        libtcod.console_set_default_background(self.panel, libtcod.black)
        libtcod.console_clear(self.panel)
        self.draw_bar(1, 1, BAR_WIDTH, 'HP', self.owner.map.player.fighter.hp, self.owner.map.player.fighter.max_hp, libtcod.red, libtcod.darker_red)
        self.draw_bar(1, 3, BAR_WIDTH, 'MP', self.owner.map.player.fighter.hp, self.owner.map.player.fighter.max_hp, libtcod.blue, libtcod.darker_blue)

        # Draw the messages
        for (y, (line, color)) in enumerate(self.owner.messages):
            libtcod.console_set_default_foreground(self.panel, color)
            libtcod.console_print_ex(self.panel, MSG_X, y + 1, libtcod.BKGND_NONE, libtcod.LEFT, line)

        # Flush alternatives to default console
        libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_blit(self.panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
        libtcod.console_flush()

    def draw_bar(self, x, y, total_width, name, value, maximum, bar_color, back_color):
        bar_width = int(float(value) / maximum * total_width)

        # render the background first
        libtcod.console_set_default_background(self.panel, back_color)
        libtcod.console_rect(self.panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

        #now render the bar on top
        libtcod.console_set_default_background(self.panel, bar_color)
        if bar_width > 0:
            libtcod.console_rect(self.panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

        # finally, some centered text with the values
        libtcod.console_set_default_foreground(self.panel, libtcod.white)
        libtcod.console_print_ex(self.panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, "{}: {}/{}".format(name, str(value), str(maximum)))


class ObjectPainter:
    def __init__(self, obj_type=None, owner=None):
        self.owner = owner
        self.obj_type = obj_type

    def __draw_obj(self, con, char, color):
        libtcod.console_set_default_foreground(con, color)
        libtcod.console_put_char(con, self.owner.x, self.owner.y, char, libtcod.BKGND_NONE)

    def draw(self, con):
        if self.owner.visible:
            if self.owner.state == STATE_DEAD:
                self.__draw_obj(con, '%', libtcod.darker_red)
                return

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
