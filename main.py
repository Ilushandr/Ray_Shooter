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
    def __init__(self, radius, fov):
        super().__init__(all_sprites)
        self.x = width // 2
        self.y = height // 2
        self.radius = radius
        self.fov = fov  # Угол обзора игрока
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, 'white',
                           (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, 2 * radius, 2 * radius)
        self.obstacles = [wall.rect for wall in walls]  # Спиоск всех преград

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        x, y = self.x + self.radius, self.y + self.radius
        aim_x, aim_y = x, y
        view_angle = atan2(my - y, mx - x)  # Считает угол относительно курсора
        # Начальные координаты многоугольника, по которому рисуется рейкаст
        coords = [(x, y)]
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
            for c in range(0, 1000, 20):
                point.x = x + c * cos_a
                point.y = y + c * sin_a
                if point.collidelistall(self.obstacles):  # Если точка достигает стены
                    # Тут уже начинается подгон точки под границы ректа бинарным поиском
                    l, r = c - 50, c
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

        #  Наконец рисуем полигон
        pygame.draw.polygon(screen, pygame.Color(255, 255, 255), coords)
        pygame.draw.line(screen, 'red', (x, y),
                         (aim_x, aim_y))

    def movement(self, dx, dy):
        # Метод обрабатывает столкновение игрока с препятствиями и меняет его координаты
        # Изменение по x
        self.rect.x += dx
        for block in self.obstacles:
            if self.rect.colliderect(block):
                if dx < 0:
                    self.rect.left = block.right
                elif dx > 0:
                    self.rect.right = block.left
                break

        # Изменение по y
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
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    map = Map()
    player = Player(10, 90)

    v = 5
    fps = 60
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill('black')
        all_sprites.draw(screen)
        player.update()
        pygame.display.flip()
        clock.tick(fps)
        print(clock.get_fps())
