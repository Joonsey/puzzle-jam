from __future__ import annotations
import os
import pygame
from pytmx.util_pygame import load_pygame

from threading import Thread

import client

pygame.init()


RENDER_SIZE = 400, 320
DISPLAY_SIZE = 1080, 720
TARGET_FPS = 60
UPDATE_FREQ = 60 / 60

class GameContext:
    def __init__(self, game: Game) -> None:
        self.game = game

    def draw(self) -> None:
        ...

    def update(self, dt: float, keys) -> None:
        ...

class MainMenu(GameContext):
    def draw(self) -> None:
        ...

    def update(self, dt: float, keys) -> None:
        Thread(target=self.game.client.register_with_server, args=("test_phrase",), daemon=True).start()
        if self.game.client.peer_to_peer_established:
            self.game.client.start()
            self.game.context = Zone(self.game)


class WorldMap(GameContext):
    def draw(self) -> None:
        self.game.render.fill((255, 255, 255))
        self.game.draw_players()

        self.game.draw_render()

    def update(self, dt: float, keys) -> None:
        self.game.player.udpate(dt, keys)
        self.game.send_update()


class Zone(GameContext):
    def __init__(self, game: Game) -> None:
        super().__init__(game)

    def draw(self) -> None:
        self.game.render.fill((255, 255, 255))
        self.game.draw_map()
        self.game.draw_players()

        self.game.draw_render()

    def update(self, dt: float, keys) -> None:
        self.game.player.udpate(dt, keys)
        self.game.move_camera_to_player_pos()
        self.game.send_update()

        self.game.draw_render()


class Player:
    def __init__(self) -> None:
        self.position: tuple[float, float] = (0, 0)
        self.direction: bool = False
        self.anim_frame: int = 0
        self.state: int = 0
        self.bounds: list[pygame.Rect] = []

    def draw(self, surf: pygame.Surface, position) -> None:
        sprite = pygame.Surface((16, 16))
        sprite.fill((0, 124, 0))
        surf.blit(sprite, position)

    def udpate(self, dt: float,  keys) -> None:
        old_pos = self.position
        speed = 60 * dt

        new_x, new_y = old_pos
        if keys[pygame.K_w]:
            new_y = old_pos[1] - speed
        elif keys[pygame.K_s]:
            new_y = old_pos[1] + speed

        if any([pygame.Rect(new_x, new_y, 16, 16).colliderect(ob) for ob in self.bounds]):
            _, new_y = old_pos

        if keys[pygame.K_a]:
            new_x = old_pos[0] - speed
        elif keys[pygame.K_d]:
            new_x = old_pos[0] + speed

        if any([pygame.Rect(new_x, new_y, 16, 16).colliderect(ob) for ob in self.bounds]):
            new_x, _ = old_pos

#        for rect in self.bounds:
#            if rect.colliderect(new_x, new_y, 16, 16):
#                x,y = self.game.account_for_camera_offset((rect.x, rect.y))
#                pygame.draw.rect(self.game.render, (255,0,0), (x, y, rect.width, rect.height))
        self.position = (new_x, new_y)


    def update_bounds(self, bounds: list[pygame.Rect]) -> None:
        self.bounds = bounds


class Game:
    def __init__(self) -> None:
        self.render = pygame.Surface(RENDER_SIZE)
        self.width, self.height = RENDER_SIZE
        self.client = client.Client("localhost", 8888)  # TODO
        self.player = Player()
        self.clock = pygame.Clock()
        self.frame_count = 0

        self.camera_offset: tuple[float, float] = (0, 0)

        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption("puzzle-jam-4")
        self.context: GameContext = MainMenu(self)

        # TODO refactor
        self.cave_map = load_pygame(os.path.join("assets", "maps" ,"cave.tmx"))
        player_spawn = self.cave_map.get_object_by_name("player_spawn")
        self.player.position = player_spawn.x, player_spawn.y
        self.camera_offset = self.player.position

        bounds = [pygame.Rect(ob.x, ob.y, ob.width, ob.height) for ob in self.cave_map.get_layer_by_name('bounds')] # pyright: ignore
        self.player.update_bounds(bounds)

    def draw_render(self) -> None:
        pygame.transform.scale(self.render, DISPLAY_SIZE, self.display)

    def draw_map(self) -> None:
        tile_size = 16
        for x, y, image in self.cave_map.get_layer_by_name('ground').tiles():  #pyright: ignore
            pos = self.account_for_camera_offset((x* tile_size, y* tile_size))
            if -100 <= pos[0] <= RENDER_SIZE[0] + 100 and -100 <= pos[1] <= RENDER_SIZE[1] + 100:
                self.render.blit(image, pos)

    def draw_other_player(self) -> None:
        if not self.client.other_player:
            return

        player = self.client.other_player

        sprite = pygame.Surface((16, 16))
        sprite.fill((0, 124, 0))
        self.render.blit(sprite, self.account_for_camera_offset(player.position))

    def move_camera_to_player_pos(self) -> None:
        camera_factor = 20
        target_pos = self.player.position
        target_pos = target_pos[0] - (RENDER_SIZE[0] // 2) + 8, \
            target_pos[1] - (RENDER_SIZE[1] // 2) + 8, \

        self.camera_offset = self.camera_offset[0] + (target_pos[0] - self.camera_offset[0]) / camera_factor, \
            self.camera_offset[1] + (target_pos[1] - self.camera_offset[1]) / camera_factor


    def account_for_camera_offset(self, position: tuple) -> tuple[float, float]:
        return position[0] - self.camera_offset[0], position[1] - self.camera_offset[1]

    def draw_players(self) -> None:
        self.player.draw(self.render, self.account_for_camera_offset(self.player.position))
        self.draw_other_player()

    def send_update(self) -> None:
        if not self.client.peer_to_peer_established:
            return

        if not self.frame_count % UPDATE_FREQ:
            player = self.player
            self.client.send_update(player.position, player.direction, player.anim_frame, player.state)

    def run(self) -> None:
        self.playing = True
        while self.playing:
            dt = self.clock.tick(30) / 1000
            self.frame_count += 1
            keys = pygame.key.get_pressed()
            self.context.draw()
            self.context.update(dt, keys)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.playing = False

        self.client.stop()
        pygame.quit()
game = Game()
game.run()
