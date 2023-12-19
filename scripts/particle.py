class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)

        self.animation = self.game.assets['particles/' + self.type].copy()
        self.animation.frame = frame

    def update(self):
        kill = False
        if self.animation.done:
            kill = True

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()

        return kill

    def render(self, surface, offset=(0, 0)):
        image = self.animation.image()
        surface.blit(image, (self.pos[0] - offset[0] - image.get_width() // 2, self.pos[1] - offset[1] - image.get_height() // 2))
