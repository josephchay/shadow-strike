import sys
import pygame
from pygame.locals import *


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Shadow Strike')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

    def run(self):
        while True:
            self.display.fill((14, 219, 248))

            for event in pygame.event.get():
                if (event.type == QUIT) or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            pygame.display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    Game().run()
