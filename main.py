import pygame
import os
import sys
from PIL import Image
from numba import njit
from numba.typed import List
from math import cos, sin, atan2, pi, sqrt
from collections import deque
from random import randint

pygame.init()
display_info = pygame.display.Info()
#  Достаются значения разрешения экрана из display_info
size = width, height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode(size)
fps = 60
clock = pygame.time.Clock()
level = 3

all_sprites = pygame.sprite.Group()
walls = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()


def go_game():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    start_menu()
        if pygame.mouse.get_pressed()[0]:
            player.shoot()

        all_sprites.draw(screen)

        bullets.update()
        gun.reload -= 1
        level_map.update()
        enemies.update()
        player.update()
        walls.update()

        fps_counter()
        pygame.display.flip()
        clock.tick(fps)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)

    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def start_menu():
    menu_background = pygame.image.load('pictures/menu.jpg')

    font_game = pygame.font.Font(None, 112)
    start_button = Button(280, 70)
    quit_button = Button(280, 70)
    pygame.mixer.music.load('sounds/background.mp3')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)
    show = True
    while show:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                show = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit()
        screen.blit(menu_background, (0, 0))
        screen.blit(font_game.render('Ray Shooter', True, (18, 19, 171)),
                    font_game.render('Ray Shooter', True, (18, 19, 171)).get_rect(
                        center=(500, 300)))
        start_button.draw(270, 600, 'Начать игру', go_game)
        quit_button.draw(270, 700, 'Выход', quit)
        pygame.display.update()
        clock.tick(60)


class Button:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def draw(self, x, y, message, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hover_sound = pygame.mixer.Sound('sounds/hover_over_the_button.mp3')
        hover_sound.set_volume(0.1)

        if x < mouse[0] < x + self.width and y < mouse[1] < y + self.height:
            pygame.draw.rect(screen, (18, 19, 171), (x, y, self.width, self.height))
            if click[0] == 1:
                if action is not None:
                    hover_sound.play()
                    pygame.mixer.music.stop()
                    action()
        else:
            pygame.draw.rect(screen, (68, 53, 212), (x, y, self.width, self.height))
        self.print_text(message, x + 10, y + 10)

    def print_text(self, message, x, y, font_color=(0, 0, 0),
                   font_type=None, font_size=32):
        font_type = pygame.font.Font(font_type, font_size)
        text = font_type.render(message, True, font_color)
        screen.blit(text, (x, y))


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(walls)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        pygame.draw.rect(screen, 'black', (self.x, self.y,
                                           self.w, self.h))


class Floor(pygame.sprite.Sprite):
    image = Image.open('data/floor.png')

    def __init__(self):
        super(Floor, self).__init__(all_sprites)
        self.image = Floor.image
        self.result_floor_image = Image.new('RGB', (width, height))
        self.image = self.create_floor()
        self.rect = self.image.get_rect()

    def create_floor(self):
        w = width // self.image.width
        h = height // self.image.height
        for row in range(h + 5):
            for col in range(w + 5):
                self.result_floor_image.paste(self.image,
                                              (col * self.image.width, row * self.image.height))
        self.result_floor_image.save('data/floor_result.png')
        self.image = load_image('floor_result.png')
        return self.image


class Bullet(pygame.sprite.Sprite):
    def __init__(self, player_x, player_y, phi, v0, a, dmg):
        super().__init__(bullets)
        self.point = pygame.Rect(player_x, player_y, 1, 1)
        self.phi = phi  # Угол полета пули
        self.v = v0  # Скорость полета пули
        self.a = a  # Ускорение пули
        self.dmg = dmg

        self.cos_phi = cos(phi)
        self.sin_phi = sin(phi)

        self.pos_x = player_x
        self.pos_y = player_y

    def update(self):
        # Изменяем полеожение пули и ее скорость
        if self.v <= 0:
            self.kill()
        elif self.point.collidelistall(obstacles):
            self.bounce()
        self.hit()

        # Приходится сохранять координаты пули, т.к. rect округляет и в конце выходит
        # большая погрешность
        dx = self.v * self.cos_phi
        dy = self.v * self.sin_phi
        self.pos_x = self.pos_x + dx
        self.pos_y = self.pos_y + dy
        self.v += self.a

        self.point.x = self.pos_x
        self.point.y = self.pos_y
        pygame.draw.line(screen, '#FD4A03', (self.point.x, self.point.y),
                         (self.point.x - dx, self.point.y - dy), 5)

    def hit(self):
        for enemy in enemies:
            if self.point.colliderect(enemy.rect):
                self.kill()
                enemy.hp -= self.dmg
                enemy.stun()

    def bounce(self):
        for block in obstacles:
            if self.point.colliderect(block):
                x0 = self.pos_x - ((self.v - self.a) * self.cos_phi)
                y0 = self.pos_y - ((self.v - self.a) * self.sin_phi)
                x, y = block.clipline(x0, y0, self.pos_x, self.pos_y)[0]
                if (block.bottom - 2 <= y <= block.bottom + 2 or
                        block.top - 2 <= y <= block.top + 2):
                    self.sin_phi = -self.sin_phi
                else:
                    self.cos_phi = -self.cos_phi
                break


class Weapon:
    def __init__(self):
        self.dmg = 5
        self.reload_speed = 1
        self.reload = self.reload_speed
        self.accuracy = 0.05
        self.a = -0.5
        self.v0 = 40

    def shot(self):
        mx, my = pygame.mouse.get_pos()
        x, y = player.x, player.y
        phi = atan2(my - y, mx - x)
        for i in range(-2, 3):
            alpha = randint(-self.accuracy * 100, self.accuracy * 100)
            Bullet(x, y, phi + alpha / 100 + i / 100, self.v0, self.a, self.dmg)


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
            if block != self.rect and self.rect.colliderect(block):
                if dx < 0:
                    self.rect.left = block.right
                elif dx > 0:
                    self.rect.right = block.left
                break
        # Изменение по y
        self.rect.y += dy
        for block in obstacles:
            if block != self.rect and self.rect.colliderect(block):
                if dy < 0:
                    self.rect.top = block.bottom
                elif dy > 0:
                    self.rect.bottom = block.top
                break


class Player(Character):
    def __init__(self, fov, radius=10):
        super().__init__()
        self.x, self.y = level_map.player_location()
        self.radius = radius
        self.fov = fov  # Угол обзора игрока

        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                self.radius * 2, self.radius * 2)

    def shoot(self):
        if gun.reload < 0:
            gun.shot()
            gun.reload = gun.reload_speed

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        x, y = self.x, self.y
        view_angle = atan2(my - y, mx - x)  # Считает угол относительно курсора

        coords = self.start_ray_coords(x, y, view_angle)
        coords.extend(ray_cycle(x, y, view_angle, ray_obstacles, level_map.cell_w,
                                level_map.cell_h, level_map.map_w, level_map.map_h, self.fov))
        pygame.draw.polygon(screen, 'black', coords)

    def start_ray_coords(self, x, y, alpha):
        if -pi <= alpha <= -pi / 2:
            return [(x, y), (width, height), (0, height), (0, 0),
                    (width, 0), (width, height), (x, y)]
        elif -pi / 2 <= alpha <= 0:
            return [(x, y), (0, height), (0, 0), (width, 0),
                    (width, height), (0, height), (x, y)]
        elif 0 <= alpha <= pi / 2:
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
        self.x = self.rect.x + self.radius
        self.y = self.rect.y + self.radius

    def update(self):
        self.move_character()
        self.ray_cast()
        pygame.draw.circle(screen, 'blue', (self.x, self.y), self.radius)


class Enemy(Character):
    def __init__(self, x, y, complexity):
        super(Enemy, self).__init__()
        types = [(100, 10, 7), (70, 25, 4), (200, 5, 5)]
        self.x = x
        self.y = y
        self.location = (self.y // level_map.cell_h, self.x // level_map.cell_w)
        self.destination = self.location

        self.hp, self.dmg, self.speed = types[complexity]
        self.radius = 15

        self.image = pygame.Surface((self.radius, self.radius),
                                    pygame.SRCALPHA, 32)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(self.x, self.y, self.radius * 2, self.radius * 2)

        self.stun_time = 10
        self.stun_timer = 0

        obstacles.append(self.rect)
        enemy_rects.append(self.rect)
        enemies.add(self)

    def move(self):
        ray_coords = (self.rect.topleft, self.rect.topright,
                      self.rect.bottomright, self.rect.bottomleft)
        if all((in_view(*pos, player.x, player.y, ray_obstacles)
                for pos in ray_coords)):
            phi = atan2(player.y - self.y, player.x - self.x)
        else:
            x1, y1 = self.destination
            phi = atan2(y1 * level_map.cell_h + level_map.cell_h // 2 - self.y,
                        x1 * level_map.cell_w + level_map.cell_w // 2 - self.x)
        self.movement(cos(phi) * self.speed, sin(phi) * self.speed)

    def stun(self):
        self.stun_timer = self.stun_time

    def dead(self):
        obstacles.remove(self.rect)
        enemy_rects.remove(self.rect)
        self.kill()

    def render(self):
        pygame.draw.circle(screen, 'red',
                           (self.x, self.y), self.radius)

    def update(self):
        if self.hp <= 0:
            self.dead()
        if self.stun_timer <= 0:
            self.location = (self.rect.y // level_map.cell_h, self.rect.x // level_map.cell_w)
            self.destination = level_map.cheapest_path(*self.location)
            level_map.distances[self.location[0]][self.location[1]] = 1000

            self.move()
            self.x = self.rect.x + self.radius
            self.y = self.rect.y + self.radius
        self.stun_timer -= 1
        self.render()


class Map:
    def __init__(self):
        self.map = self.create_level()
        self.distances = None

        self.map_w = len(self.map[0])
        self.map_h = len(self.map)
        self.cell_w = width // self.map_w
        self.cell_h = height // self.map_h

        rects = self.merge_rects(self.get_horizontal_rects(), self.get_vertical_rects())
        self.create_walls(rects)

    def player_location(self):
        for row in range(self.map_h):
            for col in range(self.map_w):
                if self.map[row][col] == '@':
                    return (col * self.cell_w + self.cell_w // 2,
                            (row) * self.cell_h + self.cell_h // 2)

    def create_level(self):
        # Создает карту уровня
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

    def distance_to_player(self):
        inf = 1000
        x, y = player.x // self.cell_w, player.y // self.cell_h
        self.distances = [[inf if col != '#' else '#' for col in row]
                          for row in self.map]
        self.distances[y][x] = 0

        queue = deque()
        queue.append((y, x))

        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if dr or dc:
                    next_row, next_col = row + dr, col + dc
                    if (self.cell_in_map(next_row, next_col) and
                            self.distances[next_row][next_col] == inf):
                        self.distances[next_row][next_col] = self.distances[row][col] + 1
                        queue.append((next_row, next_col))

    def cell_in_map(self, row, col):
        return 0 <= row < self.map_h and 0 <= col < self.map_w

    def cheapest_path(self, row, col):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_row, next_col = row + dr, col + dc
            if ((dr or dc) and self.cell_in_map(next_row, next_col) and
                    self.distances[next_row][next_col] != '#' and
                    self.distances[next_row][next_col] < self.distances[row][col]):
                return next_col, next_row
        return row, col

    def update(self):
        self.distance_to_player()


class SpawnPoint:
    def __init__(self, types=(0, 1, 2), spawn_time=fps * 5):
        self.types = types
        self.spawn_time = spawn_time
        self.timer = self.spawn_time


@njit(fastmath=True)
def ray_cycle(player_x, player_y, view_angle, obstacles, tile_w, tile_h, map_w, map_h, fov):
    rounded_x = (player_x // tile_w) * tile_w
    rounded_y = (player_y // tile_h) * tile_h
    coords = []

    for alpha in range(-fov, fov + 1):  # Цикл по углу обзора
        alpha = view_angle + alpha / 100
        sin_a = sin(alpha) if sin(alpha) else 0.000001
        cos_a = cos(alpha) if cos(alpha) else 0.000001
        ray_x, ray_y = player_x, player_y

        # Пересечение по вертикали
        ray_x, dx = (rounded_x + tile_w, 1) if cos_a >= 0 else (rounded_x, -1)
        found = False
        for _ in range(0, map_w * tile_w, tile_w):
            length_v = (ray_x - player_x) / cos_a
            ray_y = player_y + length_v * sin_a

            for ox, oy, map_w, map_h in obstacles:
                if ox <= ray_x <= ox + map_w and oy <= ray_y <= oy + map_h:
                    found = True
                    break
            if found:
                break
            ray_x += tile_w * dx
        res_v = (int(ray_x), int(ray_y), length_v)

        # Пересечение по горизонтали
        ray_y, dy = (rounded_y + tile_h, 1) if sin_a >= 0 else (rounded_y, -1)
        found = False
        for _ in range(0, map_h * tile_h, tile_h):
            length_h = (ray_y - player_y) / sin_a
            ray_x = player_x + length_h * cos_a

            for ox, oy, map_w, map_h in obstacles:
                if ox <= ray_x <= ox + map_w and oy <= ray_y <= oy + map_h:
                    found = True
                    break
            if found:
                break
            ray_y += tile_h * dy
        res_h = (int(ray_x), int(ray_y), length_h)

        res = (res_v[0], res_v[1]) if res_v[2] <= res_h[2] else (res_h[0], res_h[1])

        if (len(coords) > 1 and (coords[-1][0] == res[0] and coords[-2][0] == res[0] or
                                 coords[-1][1] == res[1] and coords[-2][1] == res[1])):
            coords[-1] = res
        else:
            coords.append(res)
    return coords


@njit(fastmath=True)
def in_view(x1, y1, x2, y2, obstacles):
    phi = atan2(y2 - y1, x2 - x1)
    cos_phi = cos(phi)
    sin_phi = sin(phi)
    distance = sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    length = 0
    ray_x, ray_y = x1, y1
    while distance > 1:
        ray_x = x1 + length * cos_phi
        ray_y = y1 + length * sin_phi
        distance = sqrt((ray_x - x2) ** 2 + (ray_y - y2) ** 2)

        for ox, oy, map_w, map_h in obstacles:
            if ox <= ray_x <= ox + map_w and oy <= ray_y <= oy + map_h:
                return False
        length += 1

    return True


def fps_counter():
    font = pygame.font.Font(None, 20)
    text = font.render(str(round(clock.get_fps(), 4)), True, 'white')
    text_x = 0
    text_y = 0
    screen.blit(text, (text_x, text_y))


if __name__ == '__main__':
    level_map = Map()
    floor = Floor()
    gun = Weapon()
    enemy_rects = []
    obstacles = [wall.rect for wall in walls]  # Спиоск всех преград
    ray_obstacles = List([(wall.rect.x, wall.rect.y,
                           wall.rect.w, wall.rect.h) for wall in walls])
    player = Player(100)
    enemy1 = Enemy(100, 100, 0)
    enemy2 = Enemy(width - 200, height - 200, 0)
    enemy3 = Enemy(200, 200, 0)

    v = 10
    start_menu()
