import pygame
from math import cos, sin, atan2


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(walls)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self, radius):
        super().__init__(all_sprites)
        self.x = width // 2
        self.y = height // 2
        self.radius = radius
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, 'white',
                           (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, 2 * radius, 2 * radius)

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        view_angle = atan2(my - self.y, mx - self.x)
        collide_walls = [wall.rect for wall in walls]

        coords = [(self.x + self.radius, self.y + self.radius)]
        for a in range(-50, 51):
            cos_a = cos(view_angle + a / 50)
            sin_a = sin(view_angle + a / 50)
            point = pygame.Rect(self.x, self.y, 1, 1)
            for c in range(0, 500, 20):
                point.x = self.x + c * cos_a
                point.y = self.y + c * sin_a
                if point.collidelistall(collide_walls):
                    l, r = c - 50, c
                    while r - l > 1:
                        m = (r + l) / 2
                        point.x = self.x + m * cos_a
                        point.y = self.y + m * sin_a
                        if point.collidelistall(collide_walls):
                            r = m
                        else:
                            l = m
                    break
            coords.append((point.x, point.y))

        pygame.draw.polygon(screen, pygame.Color(255, 255, 255, a=255), coords)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.y -= v
        if keys[pygame.K_s]:
            self.y += v
        if keys[pygame.K_a]:
            self.x -= v
        if keys[pygame.K_d]:
            self.x += v
        self.rect.x = self.x
        self.rect.y = self.y
        self.ray_cast()


class Map:
    def __init__(self):
        map = [['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', '#', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', '#', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', '#', ' ', ' ', '#', '#', ' ', '#', '#'],
               ['#', ' ', '#', '#', '#', ' ', ' ', '#', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', '#', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#', ' ', '#'],
               ['#', ' ', '#', ' ', '#', ' ', ' ', '#', ' ', ' ', ' ', '#'],
               ['#', ' ', '#', ' ', '#', ' ', ' ', '#', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', '#', ' ', ' ', '#', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#']]
        map_w = len(map[0])
        map_h = len(map)

        w = width // map_w
        h = height // map_h
        for row in range(map_h):
            for col in range(map_w):
                if map[row][col] == '#':
                    Wall(col * w, row * h, w, h)


if __name__ == '__main__':
    pygame.init()
    size = width, height = 800, 600
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    player = Player(10)
    map = Map()

    v = 3
    fps = 60
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill('black')
        all_sprites.draw(screen)
        all_sprites.update()
        player.update()
        pygame.display.flip()
        clock.tick(fps)
        print(clock.get_fps())
