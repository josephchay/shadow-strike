import sys
import pygame
from pygame.locals import *

from scripts.entities import PhysicsEntity, Player
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Shadow Strike')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'player/idle': Animation(load_images('entities/player/idle'), image_duration=6),
            'player/run': Animation(load_images('entities/player/run'), image_duration=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
        }

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self)
        self.tilemap.load('map.json')

        self.scroll = [0, 0]

    def run(self):
        while True:
            self.display.blit(self.assets['background'], (0, 0))

            self.scroll[0] += (self.player.hitbox().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.hitbox().centery - self.display.get_height() / 2 - self.scroll[1]) / 30

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display, offset=render_scroll)

            for event in pygame.event.get():
                if (event.type == QUIT) or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_a:
                        self.movement[0] = True
                    if event.key == K_d:
                        self.movement[1] = True
                    if event.key == K_w:
                        self.player.velocity[1] = -3
                if event.type == KEYUP:
                    if event.key == K_a:
                        self.movement[0] = False
                    if event.key == K_d:
                        self.movement[1] = False

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            pygame.display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    Game().run()
