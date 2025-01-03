import math
import os
import random
import sys
import pygame
from pygame.locals import *

from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.spark import Spark
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Shadow Strike')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_without_outline = pygame.Surface((320, 240))

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
            'enemy/idle': Animation(load_images('entities/enemy/idle'), image_duration=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), image_duration=4),
            'player/idle': Animation(load_images('entities/player/idle'), image_duration=6),
            'player/run': Animation(load_images('entities/player/run'), image_duration=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particles/leaf': Animation(load_images('particles/leaf'), image_duration=20, loop=False),
            'particles/particle': Animation(load_images('particles/particle'), image_duration=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self)

        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))  # 8 by 15 is the dimensions of the image, changes depending on the image

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_without_outline.blit(self.assets['background'], (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            # If all enemies are dead
            if not len(self.enemies):
                self.transition += 1

                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)

                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (self.player.hitbox().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.hitbox().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                # bigger tree spawn more leaves
                # 1/50000 chance per frame
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.clouds.update()
            self.clouds.render(self.display_without_outline, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies:
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], speed-direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                image = self.assets['projectile']
                self.display.blit(image, (projectile[0][0] - image.get_width() / 2 - render_scroll[0], projectile[0][1] - image.get_height() / 2 - render_scroll[1]))

                # check if the projectile has hit a solid tile
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)

                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:  # 360 frames = 6 seconds timer
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    # check if the projectile has hit the player
                    if self.player.hitbox().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1

                        self.screenshake = max(20, self.screenshake)
                        self.sfx['hit'].play()

                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.hitbox().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.hitbox().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))

            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_without_outline.blit(display_silhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)

                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

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
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == K_SPACE:
                        self.player.dash()

                if event.type == KEYUP:
                    if event.key == K_a:
                        self.movement[0] = False
                    if event.key == K_d:
                        self.movement[1] = False

            if self.transition:
                transition_surface = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surface, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surface.set_colorkey((255, 255, 255))
                self.display.blit(transition_surface, (0, 0))

            self.display_without_outline.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_without_outline, self.screen.get_size()), screenshake_offset)

            pygame.display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    Game().run()
