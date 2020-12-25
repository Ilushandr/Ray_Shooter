import pygame
from numba import njit, prange
from numba.typed import List
from math import cos, sin, atan2, pi


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(walls)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = pygame.Surface((w, h),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        pass


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, phi, v0, a):
        super().__init__(bullets)
        self.point = pygame.Rect(x, y, 1, 1)
        self.phi = phi  # Угол полета пули
        self.v = v0  # Скорость полета пули
        self.a = a  # Ускорение пули

        self.cos_phi = cos(phi)
        self.sin_phi = sin(phi)

        self.pos_x = x
        self.pos_y = y

    def update(self):
        # Изменяем полеожение пули и ее скорость
        if self.v <= 0:
            self.kill()
        elif self.point.collidelistall(obstacles):
            self.bounce()
        # Приходится сохранять координаты пули, т.к. rect округляет и в конце выходит
        # большая погрешность
        dx = self.v * self.cos_phi
        dy = self.v * self.sin_phi
        self.pos_x = self.pos_x + dx
        self.pos_y = self.pos_y + dy
        self.v += self.a

        self.point.x = self.pos_x
        self.point.y = self.pos_y
        pygame.draw.line(screen, 'orange', (self.point.x, self.point.y),
                         (self.point.x - dx, self.point.y - dy), 5)

    def bounce(self):
        for block in obstacles:
            if self.point.colliderect(block):
                if block.collidepoint((self.point.x + self.v * -self.cos_phi, self.point.y)):
                    self.sin_phi = -self.sin_phi
                else:
                    self.cos_phi = -self.cos_phi


class Weapon:
    def shot(self, v0=30, a=-0.5):
        mx, my = pygame.mouse.get_pos()
        x, y = player.x + player.radius, player.y + player.radius
        phi = atan2(my - y, mx - x)
        for i in range(-10, 11):
            Bullet(x, y, phi + i / 100, v0, a)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, fov, radius=10):
        super().__init__(all_sprites)
        self.x = x
        self.y = y
        self.radius = radius
        self.fov = fov  # Угол обзора игрока
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, 20, 20)
        self.aim_x, self.aim_y = x + radius, y + radius

    def shoot(self):
        gun.shot()

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        x, y = self.x + self.radius, self.y + self.radius
        view_angle = atan2(my - y, mx - x)  # Считает угол относительно курсора
        coords = self.ray_cycle(view_angle, x, y)
        self.draw_raycast(x, y, coords)

    def draw_raycast(self, x, y, coords):
        pygame.draw.polygon(screen, 'black', coords)
        pygame.draw.line(screen, 'red', (x, y),
                         (self.aim_x, self.aim_y))

    def ray_cycle(self, view_angle, x, y):
        coords = self.start_ray_coords(x, y, view_angle)
        for a in range(-self.fov, self.fov + 1):  # Цикл по углу обзора
            ray_x, ray_y = calc_cycle(x, y, view_angle + a / 100, ray_obstacles)
            if a == 0:
                self.aim_x, self.aim_y = ray_x, ray_y
            coords.append((ray_x, ray_y))
        return coords

    def start_ray_coords(self, x, y, a):
        if -pi <= a <= -pi / 2:
            return [(x, y), (width, height), (0, height), (0, 0),
                    (width, 0), (width, height), (x, y)]
        elif -pi / 2 <= a <= 0:
            return [(x, y), (0, height), (0, 0), (width, 0),
                    (width, height), (0, height), (x, y)]
        elif 0 <= a <= pi / 2:
            return [(x, y), (0, 0), (width, 0), (width, height),
                    (0, height), (0, 0), (x, y)]
        else:
            return [(x, y), (width, 0), (width, height),
                    (0, height), (0, 0), (width, 0), (x, y)]

    def movement(self, dx, dy):
        # Метод обрабатывает столкновение игрока с препятствиями и меняет его координаты
        # Изменение по x
        if dx:
            self.rect.x += dx
            for block in obstacles:
                if self.rect.colliderect(block):
                    if dx < 0:
                        self.rect.left = block.right
                    elif dx > 0:
                        self.rect.right = block.left
                    break

        # Изменение по y
        if dy:
            self.rect.y += dy
            for block in obstacles:
                if self.rect.colliderect(block):
                    if dy < 0:
                        self.rect.top = block.bottom
                    elif dy > 0:
                        self.rect.bottom = block.top
                    break

    def move_character(self):
        # Здесь происходит управление игроком
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.movement(0, -v)
        if keys[pygame.K_s]:
            self.movement(0, v)
        if keys[pygame.K_a]:
            self.movement(-v, 0)
        if keys[pygame.K_d]:
            self.movement(v, 0)
        self.x = self.rect.x
        self.y = self.rect.y

    def update(self):
        self.move_character()
        self.ray_cast()


class Map:
    def __init__(self):
        #  Это карта уровня
        map = [['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', '#', '#', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', ' ', ' ', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', ' ', ' ', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', ' ', ' ', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', ' ', ' ', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', '#', ' ', '#', '#', ' ', '#', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#'],
               ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'], ]
        map_w = len(map[0])
        map_h = len(map)

        w = width // map_w
        h = height // map_h
        for row in range(map_h):
            for col in range(map_w):
                if map[row][col] == '#':
                    Wall(col * w, row * h, w, h)


@njit(parallel=True, fastmath=True)
def calc_cycle(x, y, a, obstacles):
    step = 10
    ray_x = x
    ray_y = y
    cos_a = cos(a)
    sin_a = sin(a)

    found = False
    for length in prange(0, 1000):
        if found:
            return ray_x, ray_y

        length *= step
        ray_x = x + length * cos_a
        ray_y = y + length * sin_a

        for ox, oy, w, h in obstacles:
            if ox <= ray_x <= ox + w and oy <= ray_y <= oy + h:
                l, r = length - step, length
                while r - l > 1:
                    left = True
                    m = (r + l) / 2
                    ray_x = x + m * cos_a
                    ray_y = y + m * sin_a
                    for ox, oy, w, h in obstacles:
                        if ox <= ray_x <= ox + w and oy <= ray_y <= oy + h:
                            left = False
                            r = m
                            break
                    if left:
                        l = m
                found = True
    return ray_x, ray_y


def fps_counter():
    font = pygame.font.Font(None, 20)
    text = font.render(str(round(clock.get_fps(), 4)), True, 'white')
    text_x = 0
    text_y = 0
    screen.blit(text, (text_x, text_y))


if __name__ == '__main__':
    pygame.init()
    display_info = pygame.display.Info()
    #  Достаются значения разрешения экрана из display_info
    size = width, height = display_info.current_w, display_info.current_h
    flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode(size, flags=flags)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    map = Map()
    player = Player(width // 2, height // 2, 90)
    gun = Weapon()

    obstacles = [wall.rect for wall in walls]  # Спиоск всех преград
    ray_obstacles = List([(wall.rect.x, wall.rect.y,
                           wall.rect.w, wall.rect.h) for wall in walls])  # Спиоск всех преград

    v = 7
    fps = 60
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    player.shoot()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit()

        screen.fill('white')
        all_sprites.draw(screen)
        bullets.update()
        player.update()
        fps_counter()

        pygame.display.flip()
        clock.tick(fps)
