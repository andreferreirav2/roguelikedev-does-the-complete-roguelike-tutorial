import os
from libtcod import libtcodpy as libtcod
from consts import *
import maps
import painter
import entities


class GameManager:
    __instance = None

    @staticmethod
    def get_instance():
        if GameManager.__instance is None:
            GameManager()
        return GameManager.__instance

    def __init__(self):
        if GameManager.__instance is not None:
            raise Exception("This is a singleton, back off!")

        dir_path = os.path.dirname(os.path.realpath(__file__))
        libtcod.console_set_custom_font('{}/assets/arial10x10.png'.format(dir_path),
                                        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
        libtcod.sys_set_fps(LIMIT_FPS)

        self.game_map = maps.Map(MAP_WIDTH, MAP_HEIGHT, auto_create=True)

        center_x1, center_y1 = self.game_map.rooms[0].center()
        center_x2, center_y2 = self.game_map.rooms[-1].center()
        self.game_map.add_object(entities.Object(center_x1, center_y1, '@', libtcod.blue, speed=PLAYER_SPEED), is_player=True)
        self.game_map.add_object(entities.Object(center_x2, center_y2, '@', libtcod.red))

        self.fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                libtcod.map_set_properties(self.fov_map, x, y, not self.game_map.tiles[x][y].block_sight, self.game_map.tiles[x][y].blocks)
        libtcod.map_compute_fov(self.fov_map, self.game_map.player.x, self.game_map.player.y, TORCH_RADIUS,  FOV_LIGHT_WALLS, FOV_ALG)

        # Game State
        self.game_state = STATE_PLAYING

        GameManager.__instance = self


    def calculate_visibility(self, obj):
        is_visible = libtcod.map_is_in_fov(self.fov_map, obj.x, obj.y)
        if not obj.seen and is_visible:
            obj.seen = True

        return is_visible

    def handle_keys(self):
        key = libtcod.console_check_for_keypress()
        action = None

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        elif key.vk == libtcod.KEY_SPACE:
            self.game_state = self.game_state ^ 1
            return None

        elif key.vk == libtcod.KEY_ESCAPE:
            return ACTION_EXIT

        # movement keys
        if self.game_state == STATE_PLAYING:
            if libtcod.console_is_key_pressed(libtcod.KEY_UP):
                self.game_map.player.move_or_attack(0, -1)
                action = ACTION_MOVE

            elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
                self.game_map.player.move_or_attack(0, 1)
                action = ACTION_MOVE

            elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
                self.game_map.player.move_or_attack(-1, 0)
                action = ACTION_MOVE

            elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
                self.game_map.player.move_or_attack(1, 0)
                action = ACTION_MOVE

        return action

    def render_all(self):
        self.game_map.draw()

        for obj in self.game_map.objects:
            obj.draw()

        painter.Painter.get_instance().flush()

    def run(self):
        while not libtcod.console_is_window_closed():
            self.render_all()
            action = self.handle_keys()

            if self.game_state is STATE_PLAYING:
                for obj in self.game_map.objects:
                    obj.wait -= 1
                    if not obj.is_player:
                        obj.move_or_attack(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

            if action == ACTION_EXIT:
                break
            # if action == ACTION_MOVE:
            libtcod.map_compute_fov(self.fov_map, self.game_map.player.x, self.game_map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)

