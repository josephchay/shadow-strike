import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]

        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.animation_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def hitbox(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if self.action != action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.hitbox()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                elif frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.hitbox()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                elif frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        elif movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.image(), self.flip, False), (self.pos[0] - offset[0] + self.animation_offset[0], self.pos[1] - offset[1] + self.animation_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            # checks whether there's a tile in front of the enemy (via 7 to the right or left, 23 down - can be customized)
            if tilemap.solid_check((self.hitbox().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])  # only move on the x-axis
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

            if not self.walking:
                # distance between enemy and player
                distance = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])

                # if the player is within 16 pixels of the enemy on the y-axis
                if abs(distance[1]) < 16:
                    # if enemy is facing left and the player is the left of the enemy
                    if self.flip and distance[0] < 0:
                        self.game.projectiles.append([[self.hitbox().centerx - 7, self.hitbox().centery], -1.5, 0])

                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))

                    # if enemy is facing right and the player is the right of the enemy
                    if not self.flip and distance[0] > 0:
                        self.game.projectiles.append([[self.hitbox().centerx + 7, self.hitbox().centery], 1.5, 0])

                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.hitbox().colliderect(self.game.player.hitbox()):

                self.game.screenshake = max(20, self.game.screenshake)

                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.hitbox().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.hitbox().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

                # Add more sparks for intensity
                self.game.sparks.append(Spark(self.hitbox().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.hitbox().center, math.pi, 5 + random.random()))
                return True

    def render(self, surface, offset=(0, 0)):
        super().render(surface, offset=offset)

        if self.flip:
            surface.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.hitbox().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.hitbox().centery - offset[1]))
        else:
            surface.blit(self.game.assets['gun'], (self.hitbox().centerx + 4 - offset[0], self.hitbox().centery - offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1

        if self.air_time > 200:
            if not self.game.dead:
                self.game.screenshake = max(20, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)

            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True

            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if abs(self.dashing) in {60, 50}:  # if at the start of the end
            for i in range(20):
                # Generate a random angle between 0 and 2*pi radians (full circle).
                angle = random.random() * math.pi * 2

                # Generate a random speed between 0.5 and 1.0.
                speed = random.random() * 0.5 + 0.5

                # Calculate the velocity vector components (x, y) using trigonometry.
                # cos(angle) and sin(angle) determine the direction,
                # and multiplying by speed sets the magnitude of the velocity.
                particle_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.hitbox().center, velocity=particle_velocity, frame=random.randint(0, 7)))

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8

            # at the end of first 10 frames of dash, slow down
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1

            particle_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]  # no changes in y, dash only on x
            self.game.particles.append(Particle(self.game, 'particle', self.hitbox().center, velocity=particle_velocity,
                                                frame=random.randint(0, 7)))

        # normalization
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surface, offset=offset)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                # velocity impulse for jumping off wall
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5

                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                # velocity impulse for jumping off wall
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5

                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        elif self.jumps:
            self.velocity[1] = -3.5
            self.jumps -= 1
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
