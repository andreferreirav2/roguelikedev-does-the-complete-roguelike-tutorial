from libtcod import libtcodpy as libtcod
from consts import *


class GamePainter:
    def __init__(self, owner=None):
        self.owner = owner
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.panel = libtcod.console_new(PANEL_WIDTH, PANEL_HEIGHT)
        self.gui = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.camera_x_offset, self.camera_y_offset = 0, 0

    def map_to_camera_coordinates(self, map_x, map_y):
        x, y = (map_x - self.camera_x_offset, map_y - self.camera_y_offset)

        if x < 0 or y < 0 or x >= CAMERA_WIDTH or y >= CAMERA_HEIGHT:
            return None, None  # if it's outside the view, return nothing

        return x, y

    def camera_to_map_coordinates(self, camera_x, camera_y):
        map_x, map_y = camera_x + self.camera_x_offset, camera_y + self.camera_y_offset

        if map_x < 0 or map_y < 0 or map_x >= MAP_WIDTH or map_y >= MAP_HEIGHT:
            return None, None  # if it's outside the map, return nothing

        return map_x, map_y

    def center_camera(self, map_x, map_y):
        if MAP_WIDTH > CAMERA_WIDTH:
            camera_x_offset = map_x - CAMERA_WIDTH / 2
            if camera_x_offset < - CAMERA_PADDING:
                camera_x_offset = - CAMERA_PADDING
            if camera_x_offset + CAMERA_WIDTH > MAP_WIDTH - 1 + CAMERA_PADDING:
                camera_x_offset = MAP_WIDTH - CAMERA_WIDTH - 1 + CAMERA_PADDING
        else:
            camera_x_offset = - (CAMERA_WIDTH - MAP_WIDTH) / 2

        if MAP_HEIGHT > CAMERA_HEIGHT:
            camera_y_offset = map_y - CAMERA_HEIGHT / 2
            if camera_y_offset < - CAMERA_PADDING:
                camera_y_offset = - CAMERA_PADDING
            if camera_y_offset + CAMERA_HEIGHT > MAP_HEIGHT - 1 + CAMERA_PADDING:
                camera_y_offset = MAP_HEIGHT - CAMERA_HEIGHT - 1 + CAMERA_PADDING
        else:
            camera_y_offset = - (CAMERA_HEIGHT - MAP_HEIGHT) / 2

        if camera_x_offset != self.camera_x_offset or camera_y_offset != self.camera_y_offset:
            (self.camera_x_offset, self.camera_y_offset) = (camera_x_offset, camera_y_offset)

    def draw(self):
        libtcod.console_clear(self.con)

        self.center_camera(self.owner.map.player.x, self.owner.map.player.y)

        # Draw map
        for camera_x in range(CAMERA_WIDTH):
            for camera_y in range(CAMERA_HEIGHT):
                map_x, map_y = self.camera_to_map_coordinates(camera_x, camera_y)
                if map_x is not None and map_y is not None:
                    self.owner.map.tiles[map_x][map_y].painter.draw(self.con, camera_x, camera_y)

        # Draw objects
        for obj in self.owner.map.objects:
            camera_x, camera_y = self.map_to_camera_coordinates(obj.x, obj.y)
            obj.painter.draw(self.con, camera_x, camera_y)

        # Draw the GUI
        libtcod.console_set_default_background(self.panel, libtcod.black)
        libtcod.console_clear(self.panel)
        self.draw_bar(1, 1, BAR_WIDTH, 'HP', self.owner.map.player.fighter.hp, self.owner.map.player.fighter.max_hp, libtcod.red, libtcod.darker_red)
        self.draw_bar(1, 3, BAR_WIDTH, 'MP', self.owner.map.player.fighter.hp, self.owner.map.player.fighter.max_hp, libtcod.blue, libtcod.darker_blue)

        # Draw margins
        libtcod.console_set_default_foreground(self.gui, libtcod.dark_amber)
        self.draw_outine_box(CAMERA_X - 1, CAMERA_Y - 1, CAMERA_WIDTH + 2, CAMERA_HEIGHT + 2)
        self.draw_outine_box(PANEL_X - 1, PANEL_Y - 1, PANEL_WIDTH + 2, PANEL_HEIGHT + 2)

        # Draw what is under the cursor
        libtcod.console_set_default_foreground(self.panel, libtcod.light_gray)
        libtcod.console_print_ex(self.panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, self.owner.get_element_under_mouse())

        # Draw the messages
        for (y, (line, color)) in enumerate(self.owner.messages):
            libtcod.console_set_default_foreground(self.panel, color)
            libtcod.console_print_ex(self.panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)

        # Flush alternatives to default console
        libtcod.console_blit(self.gui, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_blit(self.con, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, CAMERA_X, CAMERA_Y)
        libtcod.console_blit(self.panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, PANEL_X, PANEL_Y)
        libtcod.console_flush()

    def draw_outine_box(self, x, y, width, height):
        for dx in range(x, x + width):
            libtcod.console_put_char(self.gui, dx, y, libtcod.CHAR_HLINE, libtcod.BKGND_NONE)
            libtcod.console_put_char(self.gui, dx, y + height - 1, libtcod.CHAR_HLINE, libtcod.BKGND_NONE)
        for dy in range(y, y + height):
            libtcod.console_put_char(self.gui, x, dy, libtcod.CHAR_VLINE, libtcod.BKGND_NONE)
            libtcod.console_put_char(self.gui, x + width - 1, dy, libtcod.CHAR_VLINE, libtcod.BKGND_NONE)
        libtcod.console_put_char(self.gui, x, y, libtcod.CHAR_NW, libtcod.BKGND_NONE)
        libtcod.console_put_char(self.gui, x, y + height - 1, libtcod.CHAR_SW, libtcod.BKGND_NONE)
        libtcod.console_put_char(self.gui, x + width - 1, y, libtcod.CHAR_NE, libtcod.BKGND_NONE)
        libtcod.console_put_char(self.gui, x + width - 1, y + height - 1, libtcod.CHAR_SE, libtcod.BKGND_NONE)

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

    def __draw_obj(self, con, x, y, char, color):
        libtcod.console_set_default_foreground(con, color)
        libtcod.console_put_char(con, x, y, char, libtcod.BKGND_NONE)

    def draw(self, con, camera_x=None, camera_y=None):
        if camera_x is None or camera_y is None:
            return

        if self.owner.visible:
            if self.owner.state == STATE_DEAD:
                self.__draw_obj(con, camera_x, camera_y, '%', libtcod.darker_red)
                return

            if self.obj_type == 'player':
                self.__draw_obj(con, camera_x, camera_y, '@', libtcod.blue)
            elif self.obj_type == 'orc':
                self.__draw_obj(con, camera_x, camera_y, 'o', libtcod.desaturated_green)
            elif self.obj_type == 'troll':
                self.__draw_obj(con, camera_x, camera_y, 'T', libtcod.darker_green)
            elif self.obj_type == 'boss':
                self.__draw_obj(con, camera_x, camera_y, '@', libtcod.red)
            else:
                raise Exception("{} is not a valid obj_type for the ObjectPainter.".format(self.obj_type))


class TilePainter:
    def __init__(self, owner=None):
        self.owner = owner

    def draw(self, con, camera_x, camera_y):
        if camera_x is None or camera_y is None:
            return

        if self.owner.seen:
            if self.owner.block_sight:
                # Draw wall
                if self.owner.visible:
                    libtcod.console_put_char_ex(con, camera_x, camera_y, '#', libtcod.darkest_gray, libtcod.darkest_yellow)
                else:
                    libtcod.console_put_char_ex(con, camera_x, camera_y, '#', libtcod.darkest_gray, libtcod.black)
            else:
                # Draw floor
                if self.owner.visible:
                    libtcod.console_put_char_ex(con, camera_x, camera_y, ' ', libtcod.white, libtcod.light_yellow)
                else:
                    libtcod.console_put_char_ex(con, camera_x, camera_y, ' ', libtcod.white, libtcod.darker_gray)
