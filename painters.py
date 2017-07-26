from libtcod import libtcodpy as libtcod
from consts import *


class GamePainter:
    def __init__(self, owner=None):
        self.owner = owner
        self.con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
        self.panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

        self.camera_x_offset, self.camera_y_offset = 0, 0

    def map_to_camera_coordinates(self, map_x, map_y):
        (x, y) = (map_x - self.camera_x_offset, map_y - self.camera_y_offset)

        if x < 0 or y < 0 or x >= CAMERA_WIDTH or y >= CAMERA_HEIGHT:
            return None, None  # if it's outside the view, return nothing

        return x, y

    def camera_to_map_coordinates(self, camera_x, camera_y):
        return camera_x + self.camera_x_offset, camera_y + self.camera_y_offset

    def center_camera(self, map_x, map_y):
        # new camera coordinates (top-left corner of the screen relative to the map)
        x = map_x - CAMERA_WIDTH / 2  # coordinates so that the target is at the center of the screen
        y = map_y - CAMERA_HEIGHT / 2

        # make sure the camera doesn't see outside the map
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x > MAP_WIDTH - CAMERA_WIDTH - 1:
            x = MAP_WIDTH - CAMERA_WIDTH - 1
        if y > MAP_HEIGHT - CAMERA_HEIGHT - 1:
            y = MAP_HEIGHT - CAMERA_HEIGHT - 1

        if x != self.camera_x_offset or y != self.camera_y_offset:
            (self.camera_x_offset, self.camera_y_offset) = (x, y)

    def draw(self):
        libtcod.console_clear(self.con)

        self.center_camera(self.owner.map.player.x, self.owner.map.player.y)

        # Draw map
        for camera_x in range(CAMERA_WIDTH):
            for camera_y in range(CAMERA_HEIGHT):
                map_x, map_y = self.camera_to_map_coordinates(camera_x, camera_y)
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

        # Draw what is under the cursor
        libtcod.console_set_default_foreground(self.panel, libtcod.light_gray)
        libtcod.console_print_ex(self.panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, self.owner.get_element_under_mouse())

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
