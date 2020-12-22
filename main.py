import pygame
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


class Gun:
    def __init__(self):
        pass


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, radius=10):
        super().__init__(all_sprites)
        self.x = x
        self.y = y
        self.radius = radius
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, 2 * radius, 2 * radius)
        pygame.draw.circle(self.image, 'red',
                           (radius, radius), radius)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, fov, radius=10):
        super().__init__(all_sprites)
        self.x = x
        self.y = y
        self.radius = radius
        self.fov = fov  # Угол обзора игрока
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, 'white',
                           (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, 20, 20)
        self.obstacles = [wall.rect for wall in walls]  # Спиоск всех преград
        self.enemies = [enemy for enemy in enemies]

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        x, y = self.x + self.radius, self.y + self.radius
        aim_x, aim_y = x, y
        view_angle = atan2(my - y, mx - x)  # Считает угол относительно курсора
        # Начальные координаты многоугольника, по которому рисуется рейкаст
        coords = self.start_ray_coords(x, y, view_angle)
        for a in range(-self.fov, self.fov + 1):  # Цикл по углу обзора
            # Заранее считаем синус и косинус, шоб ресурсы потом не тратить
            # На 100 делится для точности и птушо в for пихается тока целые числа,
            # а fov у нас в радианах (радианы если шо от 0 до 6.3, а ля 0 до 360 в градусах)
            cos_a = cos(view_angle + a / 100)
            sin_a = sin(view_angle + a / 100)
            # Задаем rect как точку концов линий рейкаста
            point = pygame.Rect(x, y, 1, 1)

            # Цикл увеличения дистанции. Чем больше шаг, тем выше произ-ть,
            # но ниже точность рейкаста
            step = 15
            for c in range(0, 1000, step):
                point.x = x + c * cos_a
                point.y = y + c * sin_a
                if point.collidelistall(self.obstacles):  # Если точка достигает стены
                    # Тут уже начинается подгон точки под границы ректа бинарным поиском
                    l, r = c - step, c
                    while r - l > 1:
                        m = (r + l) / 2
                        point.x = x + m * cos_a
                        point.y = y + m * sin_a
                        if point.collidelistall(self.obstacles):
                            r = m
                        else:
                            l = m

                    break
            if a == 0:
                aim_x, aim_y = point.x, point.y
            coords.append((point.x, point.y))
        # Наконец рисуем полигон
        pygame.draw.polygon(screen, 'black', coords)
        pygame.draw.line(screen, 'red', (x, y),
                         (aim_x, aim_y))

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
            for block in self.obstacles:
                if self.rect.colliderect(block):
                    if dx < 0:
                        self.rect.left = block.right
                    elif dx > 0:
                        self.rect.right = block.left
                    break

        # Изменение по y
        if dy:
            self.rect.y += dy
            for block in self.obstacles:
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
    display_info = pygame.display.Info()
    #  Достаются значения разрешения экрана из display_info
    size = width, height = display_info.current_w, display_info.current_h
    flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode(size, flags=flags)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    map = Map()
    Enemy(width // 4, height // 2, 20)
    player = Player(width // 2, height // 2, 90)
    v = 5
    fps = 60
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill('white')

        all_sprites.draw(screen)
        player.update()

        pygame.display.flip()
        clock.tick(fps)
        print(clock.get_fps())