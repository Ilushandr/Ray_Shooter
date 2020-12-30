import pygame
from numba import njit, prange
from numba.typed import List
from math import cos, sin, atan2, inf, pi
from collections import deque


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(walls)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        # pygame.draw.rect(screen, 'black', (self.x, self.y, self.w, self.h), 1)
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
    def shot(self, v0=40, a=-0.5):
        mx, my = pygame.mouse.get_pos()
        x, y = player.x + player.radius, player.y + player.radius
        phi = atan2(my - y, mx - x)
        for i in range(-10, 11):
            Bullet(x, y, phi + i / 100, v0, a)


class Character(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.hp = 100
        self.damage = 10

    def movement(self, dx, dy):
        # Метод обрабатывает столкновение игрока с препятствиями и меняет его координаты
        # Изменение по x
        self.rect.x += dx
        for block in obstacles:
            if self.rect.colliderect(block):
                if dx < 0:
                    self.rect.left = block.right
                elif dx > 0:
                    self.rect.right = block.left
                break
        # Изменение по y
        self.rect.y += dy
        for block in obstacles:
            if self.rect.colliderect(block):
                if dy < 0:
                    self.rect.top = block.bottom
                elif dy > 0:
                    self.rect.bottom = block.top
                break


class Player(Character):
    def __init__(self, x, y, fov, radius=10):
        super().__init__()
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
            ray_x, ray_y = calc_cycle(x, y, view_angle + a / 100, ray_obstacles,
                                      map.cell_w, map.cell_h, map.map_w, map.map_h)
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
        self.location_on_the_map = (self.x // (width // map.map_w), self.y // (width // map.map_h))


class Map:
    def __init__(self):
        self.map = self.create_level()
        self.map_w = len(self.map[0])
        self.map_h = len(self.map)
        self.cell_w = width // self.map_w
        self.cell_h = height // self.map_h

        rects = self.merge_rects(self.get_horizontal_rects(), self.get_vertical_rects())
        self.create_walls(rects)

    def create_level(self):
        #  Это карта уровня
        with open(f'levels/level_{level}.txt') as file:
            map = file.readlines()
            return [row.rstrip() for row in map]

    def create_walls(self, rects):
        for rect in rects:
            Wall(rect.x, rect.y, rect.w, rect.h)

    def merge_rects(self, horizontal, vertical):
        rects = []
        for h_rect in horizontal:
            container = []
            for v_rect in vertical:
                if h_rect.contains(v_rect):
                    container.append(v_rect)
                    vertical.remove(v_rect)
            if container:
                rect = h_rect.unionall(container)
                rects.append(rect)
        for v_rect in vertical:
            container = []
            for h_rect in horizontal:
                if v_rect.contains(h_rect):
                    container.append(h_rect)
                    horizontal.remove(h_rect)
            if container:
                rect = v_rect.unionall(container)
                rects.append(rect)

        return rects

    def get_horizontal_rects(self):
        rects = []
        for row in range(self.map_h):
            row_rects = []
            is_rect = False
            for col in range(self.map_w):
                if self.map[row][col] == '#':
                    if not is_rect:
                        row_rects.append([])
                        is_rect = True
                    row_rects[-1].append(col)
                else:
                    is_rect = False
            for i in range(len(row_rects)):
                col, w = row_rects[i][0], len(row_rects[i])
                row_rects[i] = pygame.Rect(col * self.cell_w, row * self.cell_h,
                                           w * self.cell_w, self.cell_h)
            rects.extend(row_rects)
        return rects

    def get_vertical_rects(self):
        rects = []
        for col in range(self.map_w):
            col_rects = []
            is_rect = False
            for row in range(self.map_h):
                if self.map[row][col] == '#':
                    if not is_rect:
                        col_rects.append([])
                        is_rect = True
                    col_rects[-1].append(row)
                else:
                    is_rect = False
            for i in range(len(col_rects)):
                row, h = col_rects[i][0], len(col_rects[i])
                col_rects[i] = pygame.Rect(col * self.cell_w, row * self.cell_h,
                                           self.cell_w, h * self.cell_h)
            rects.extend(col_rects)
        return rects


class Mobs(Character):
    def __init__(self, x, y, complexity):
        super(Mobs, self).__init__()
        self.x = x
        self.y = y
        self.cell_width = width // map.map_w
        self.cell_height = height // map.map_h
        self.location_on_the_map = (self.x // self.cell_width,
                                    self.y // self.cell_height)
        if complexity == 1:
            self.radius = 10
        elif complexity == 2:
            self.radius = 20
        elif complexity == 3:
            self.radius = 30
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.location_on_the_map[0] * self.cell_width,
                                self.location_on_the_map[1] * self.cell_height,
                                2 * self.radius,
                                2 * self.radius)
        enemies.add(self)
        obstacles.append(self.rect)
        self.render()

    def render(self):
        for i in range(len(enemies)):
            pygame.draw.circle(self.image, 'red',
                               (self.radius, self.radius), self.radius)

    def cell_in_map(self, r, c):
        return 0 <= r < map.map_h and 0 <= c < map.map_w

    def get_path(self, r1, c1, r2, c2):
        distance = [[inf] * map.map_w for _ in range(map.map_h)]
        distance[r1][c1] = 0
        prev = [[None] * map.map_w for _ in range(map.map_h)]
        queue = deque()
        queue.append((r1, c1))
        while queue:
            r, c = queue.popleft()
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if (dr, dc) != (0, 0):
                        next_r, next_c = r + dr, c + dc
                        if (self.cell_in_map(next_r, next_c) and
                                distance[next_r][next_c] == inf):
                            distance[next_r][next_c] = distance[r][c] + 1
                            prev[next_r][next_c] = (r, c)
                            queue.append((next_r, next_c))
        if distance[r2][c2] == inf or (r1, c1) == (r2, c2):
            return [(r1, c1)]
        path = [(r2, c2)]
        while prev[r2][c2] != (r1, c1):
            r2, c2 = prev[r2][c2]
            path.append((r2, c2))
        return path

    def update(self):
        path = self.get_path(*self.location_on_the_map, *player.location_on_the_map)
        self.render()


@njit(parallel=True, fastmath=True)
def calc_cycle(player_x, player_y, alpha, obstacles, tile_w, tile_h, w, h):
    sin_a = sin(alpha) if sin(alpha) else 0.000001
    cos_a = cos(alpha) if cos(alpha) else 0.000001
    rounded_x = (player_x // tile_w) * tile_w
    rounded_y = (player_y // tile_h) * tile_h

    # Пересечение по вертикали
    ray_x, dx = (rounded_x + tile_w, 1) if cos_a >= 0 else (rounded_x, -1)
    found = False
    for _ in range(0, rounded_x * tile_w, tile_w):
        length_v = (ray_x - player_x) / cos_a
        ray_y = player_y + length_v * sin_a

        for ox, oy, w, h in obstacles:
            if ox <= ray_x <= ox + w and oy <= ray_y <= oy + h:
                found = True
                break
        if found:
            break
        ray_x += tile_w * dx
    res_v = (ray_x, ray_y, length_v)

    # Пересечение по горизонтали
    ray_y, dy = (rounded_y + tile_h, 1) if sin_a >= 0 else (rounded_y, -1)
    found = False
    for _ in range(0, h * tile_h, tile_h):
        length_h = (ray_y - player_y) / sin_a
        ray_x = player_x + length_h * cos_a

        for ox, oy, w, h in obstacles:
            if ox <= ray_x <= ox + w and oy <= ray_y <= oy + h:
                found = True
                break
        if found:
            break
        ray_y += tile_h * dy
    res_h = (ray_x, ray_y, length_h)
    return (res_v[0], res_v[1]) if res_v[2] <= res_h[2] else (res_h[0], res_h[1])


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
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    level = 3
    map = Map()
    gun = Weapon()
    obstacles = [wall.rect for wall in walls]  # Спиоск всех преград
    ray_obstacles = List([(wall.rect.x, wall.rect.y,
                           wall.rect.w, wall.rect.h) for wall in walls])
    player = Player(width // 2, height // 2, 90)
    mob = Mobs(860, 500, 3)

    v = 8
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit()
        screen.fill('white')
        bullets.update()
        player.update()

        fps_counter()
        pygame.display.flip()
        clock.tick(fps)
