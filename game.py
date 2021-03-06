import os
import textwrap

from libtcod import libtcodpy as libtcod
from consts import *
import maps
import painters
import entities


class GameManager:

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        libtcod.console_set_custom_font('{}/assets/arial10x10.png'.format(dir_path), libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
        libtcod.sys_set_fps(LIMIT_FPS)

        # Create and fill map
        self.map = maps.Map(MAP_WIDTH, MAP_HEIGHT)
        self.map.game_manager = self
        self.map.populate()

        # Visibility
        self.fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                libtcod.map_set_properties(self.fov_map, x, y, not self.map.tiles[x][y].block_sight, self.map.tiles[x][y].blocks)
        self.fov_recompute = True
        self.recalculate_visibility()

        # Lower screen message queue
        self.messages = []
        self.add_message("Be careful, it's dangerous out there!", libtcod.red)

        self.painter = painters.GamePainter(owner=self)
        self.key = libtcod.Key()
        self.mouse = libtcod.Mouse()

        # Game State
        self.game_state = STATE_PLAYING

    def recalculate_visibility(self):
        if self.fov_recompute:
            libtcod.map_compute_fov(self.fov_map, self.map.player.x, self.map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)
            self.fov_recompute = False

    def calculate_visibility(self, obj):
        is_visible = libtcod.map_is_in_fov(self.fov_map, obj.x, obj.y)
        if not obj.seen and is_visible:
            obj.seen = True

        obj.visible = is_visible

        return is_visible

    def add_message(self, message, color = libtcod.white):
        message_lines = textwrap.wrap(message, MSG_WIDTH)

        for line in message_lines:
            if len(self.messages) >= MSG_HEIGHT:
                del self.messages[0]

            self.messages.append((line, color))

    def handle_keys(self):
        action = None

        if self.key.vk == libtcod.KEY_ENTER and self.key.lalt:
            # Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        elif self.key.vk == libtcod.KEY_SPACE:
            self.game_state = self.game_state ^ 1
            return None

        elif self.key.vk == libtcod.KEY_ESCAPE:
            return ACTION_EXIT

        # movement keys
        if self.game_state == STATE_PLAYING:
            if self.key.vk == libtcod.KEY_UP:
                self.map.player.move_or_attack(0, -1)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_DOWN:
                self.map.player.move_or_attack(0, 1)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_LEFT:
                self.map.player.move_or_attack(-1, 0)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_RIGHT:
                self.map.player.move_or_attack(1, 0)
                action = ACTION_MOVE

        return action

    def get_element_under_mouse(self):
        (x, y) = self.painter.camera_to_map_coordinates(self.mouse.cx - CAMERA_X, self.mouse.cy - CAMERA_Y)

        elements = [obj.name for obj in self.map.objects[::-1] if obj.visible and obj.x == x and obj.y == y]

        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and self.map.tiles[x][y].visible and self.map.tiles[x][y].blocks:
            elements.append("wall")

        return ", ".join(elements).capitalize()

    def run(self):
        while not libtcod.console_is_window_closed():
            # Key and mouse handler
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, self.key, self.mouse)
            action = self.handle_keys()
            if action == ACTION_EXIT:
                break
            if action == ACTION_MOVE:
                self.fov_recompute = True

            # Calculate visibility for tiles and objects
            self.recalculate_visibility()
            for row in self.map.tiles:
                for tile in row:
                    self.calculate_visibility(tile)
            for obj in self.map.objects:
                self.calculate_visibility(obj)

            # Do actions
            if self.game_state is STATE_PLAYING:
                for obj in self.map.objects:
                    obj.wait -= 1
                    if obj.ai:
                        obj.ai.take_turn()

            self.painter.draw()

