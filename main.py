import pygame
import os
import sys
from PIL import Image
from numba.typed import List
from math import cos, sin, atan2, pi, degrees
from collections import deque
from random import randint, choice, random
from RayCasting import ray_cycle, in_view

pygame.init()
display_info = pygame.display.Info()
size = WIDTH, HEIGHT = display_info.current_w, display_info.current_h
SCREEN = pygame.display.set_mode(size, flags=pygame.FULLSCREEN)

FPS = 60
CLOCK = pygame.time.Clock()

LEVEL = 3
ENEMY_TYPES = [(40, 10, 8, 10), (100, 25, 4, 25), (200, 5, 2, 50)]

ENEMY_IMAGE = pygame.image.load('data/enemy.png').convert_alpha()
BULLET_IMAGE = pygame.image.load('data/bullet.png').convert_alpha()
HEAL_IMAGE = pygame.image.load('data/heal.png').convert_alpha()
DROP_BULLET_IMAGE = pygame.image.load('data/drop_bullet.png').convert_alpha()

all_sprites = pygame.sprite.Group()
walls_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()
spawn_points_group = pygame.sprite.Group()
drops_group = pygame.sprite.Group()


class Level:
    def __init__(self):
        self.map = self.create_level()
        self.distances = None

        self.map_w = len(self.map[0])
        self.map_h = len(self.map)
        self.cell_w = WIDTH // self.map_w
        self.cell_h = HEIGHT // self.map_h

        rects = self.merge_rects(self.get_horizontal_rects(), self.get_vertical_rects())
        self.create_walls(rects)
        self.create_spawn_points()

    def player_location(self):
        # Возвращает положение игрока на карте
        for row in range(self.map_h):
            for col in range(self.map_w):
                if self.map[row][col] == '@':
                    self.map[row].replace('@', ' ')
                    return (col * self.cell_w + self.cell_w // 2,
                            row * self.cell_h + self.cell_h // 2)

    def create_spawn_points(self):
        # Создает точки спавна мобов на карте
        for row in range(self.map_h):
            for col in range(self.map_w):
                if self.map[row][col] == 'E':
                    self.map[row].replace('E', ' ')
                    SpawnPoint(col * self.cell_w + self.cell_w // 2,
                               row * self.cell_h + self.cell_h // 2)

    def create_level(self):
        # Создает карту уровня
        with open(f'levels/level_{LEVEL}.txt') as file:
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
        # Рассчитывает и возвращает матрицу с расстояниями до игрока на каждой клетке карты
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
        # Возвращает следующую точку, в которую следует идти, чтобы приблизиться к игроку
        if self.distances[row][col] != '#':
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                next_row, next_col = row + dr, col + dc
                if ((dr or dc) and self.cell_in_map(next_row, next_col) and
                        self.distances[next_row][next_col] != '#' and
                        self.distances[next_row][next_col] < self.distances[row][col]):
                    return next_col, next_row
        return row, col

    def update(self):
        self.distance_to_player()


class SpawnPoint(pygame.sprite.Sprite):
    def __init__(self, x, y, types=(0, 1, 2), spawn_time=FPS * 4):
        super().__init__(spawn_points_group)
        self.x, self.y = x, y
        self.types = types  # Типы врагов
        self.spawn_time = spawn_time  # Время до появления след врага
        self.timer = self.spawn_time  # Отсчитывает время поялвения врага

    def update(self):
        if (self.timer <= 0 and
                not in_view(self.x, self.y, player.x, player.y, ray_obstacles)):
            Enemy(self.x, self.y, choice(self.types))
            self.timer = self.spawn_time
        self.timer -= 1


class Drop(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(drops_group)
        self.x, self.y = x, y
        self.rect = pygame.Rect(x, y, 20, 20)
        self.common = False
        self.common_drops = ((self.change_damage, 'gun'), (self.change_accuracy, 'gun'),
                             (self.change_reload, 'gun'), (self.change_multishot, 'gun'),
                             (self.heal, 'heal'))
        self.rare_drops = (((self.change_damage, 200, 'gun'), (self.change_reload, -50, 'gun')),
                           ((self.change_damage, -50, 'gun'), (self.change_reload, 200, 'gun')),
                           ((self.change_multishot, 5, 'gun'), (self.change_damage, -50, 'gun')),
                           ((self.change_damage, 200, 'gun'), (self.change_accuracy, 110, 'gun')),
                           ((self.change_reload, 120, 'gun'), (self.change_accuracy, 70, 'gun')),
                           ((self.change_hp, 25, 'heal'),))
        self.drop = self.definition_drop()

    def definition_drop(self):
        chance = random()
        if chance <= 0.2:
            drop = choice(self.rare_drops)
        else:
            drop = choice(self.common_drops)
            self.common = True
        if drop[-1] == 'heal':
            self.image = HEAL_IMAGE
        else:
            self.image = DROP_BULLET_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        return drop

    def pick_up(self):
        if player.rect.colliderect(self.rect):
            self.get_drop()
            self.kill()

    def get_drop(self):
        if self.common:
            self.drop[0]()
            self.common = False
        else:
            for drop, percent, flag in self.drop:
                drop(percent)

    def change_damage(self, percent=50):
        if percent < 0 and gun.reload_speed <= 1:
            return
        gun.dmg *= 1 + percent / 100

    def change_reload(self, percent=50):
        if gun.reload_speed > 1:
            gun.reload_speed *= 0 + percent / 100

    def change_accuracy(self, percent=50):
        if gun.accuracy * (0 + percent / 100) >= 0.001:
            gun.accuracy *= 0 + percent / 100

    def change_multishot(self, quantity=1):
        gun.multishot += quantity

    def change_hp(self, quantity=25):
        player.max_hp += quantity

    def heal(self, quantity=25):
        if player.hp < player.max_hp:
            player.hp += (player.hp + quantity) % player.max_hp

    def update(self):
        SCREEN.blit(self.image, self.rect)
        self.pick_up()


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(walls_group)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        pygame.draw.rect(SCREEN, 'black', (self.x, self.y,
                                           self.w, self.h))


class Floor(pygame.sprite.Sprite):
    image = Image.open(f'data/floor{randint(1, 6)}.png')

    def __init__(self):
        super(Floor, self).__init__(all_sprites)
        self.image = Floor.image
        self.result_floor_image = Image.new('RGB', (WIDTH, HEIGHT))
        self.image = self.create_floor()
        self.rect = self.image.get_rect()

    def create_floor(self):
        # Склеивает спрайты пола в зависимости от разрешения экрана
        w = WIDTH // self.image.width
        h = HEIGHT // self.image.height
        for row in range(h * 5):
            for col in range(w * 5):
                self.result_floor_image.paste(self.image,
                                              (col * self.image.width, row * self.image.height))
        self.result_floor_image.save('data/floor_result.png')
        self.image = load_image('floor_result.png')
        return self.image


class Character(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.collision_rect = pygame.Rect(0, 0, 25, 25)

    def movement(self, dx, dy, enemies=True):
        # Метод обрабатывает столкновение игрока с препятствиями и меняет его координаты
        # Изменение по x
        x, y = self.collision_rect.x, self.collision_rect.y
        self.collision_rect.x += dx
        for block in obstacles:
            if (block != self.collision_rect and self.collision_rect.colliderect(block) and
                    ((block not in enemy_rects) or
                     (block in enemy_rects and enemies))):
                if dx < 0:
                    self.collision_rect.left = block.right
                elif dx > 0:
                    self.collision_rect.right = block.left
                break

        # Изменение по y
        self.collision_rect.y += dy
        for block in obstacles:
            if (block != self.collision_rect and self.collision_rect.colliderect(block) and
                    ((block not in enemy_rects) or
                     (block in enemy_rects and enemies))):
                if dy < 0:
                    self.collision_rect.top = block.bottom
                elif dy > 0:
                    self.collision_rect.bottom = block.top
                break

        if not in_view(x, y, self.collision_rect.x, self.collision_rect.y, ray_obstacles):
            self.collision_rect.x, self.collision_rect.y = x, y

    def update_angle(self, x1, y1):
        x0, y0 = self.x, self.y
        view_angle = atan2(y1 - y0, x1 - x0)  # Считает угол относительно курсора
        return view_angle

    def impact(self, bullet_weight, vx1, vy1):
        # Отталкивает при попадании
        vx2, vy2 = cos(self.view_angle) * self.speed, sin(self.view_angle) * self.speed
        self.dx = (self.weight * vx2 + bullet_weight * vx1) / (self.weight + bullet_weight)
        self.dy = (self.weight * vy2 + bullet_weight * vy1) / (self.weight + bullet_weight)

    def change_coords(self):
        vx0 = cos(self.view_angle) * self.speed
        vy0 = sin(self.view_angle) * self.speed
        self.vx = vx0 + self.dx
        self.vy = vy0 + self.dy
        self.movement(self.vx, self.vy)
        if self.dx * (vx0 + self.dx) > 0:
            self.dx += vx0
        else:
            self.dx = 0
        if self.dy * (vy0 + self.dy) > 0:
            self.dy += vy0
        else:
            self.dy = 0


class Player(Character):
    def __init__(self, fov, speed, radius=10):
        super().__init__()
        self.x, self.y = level_map.player_location()
        self.v = speed
        self.radius = radius
        self.fov = fov  # Угол обзора игрока
        self.max_hp = 10
        self.hp = self.max_hp

        self.image = pygame.image.load('data/player_3.png').convert_alpha()
        self.current_image = self.image
        self.view_angle = self.update_angle(*pygame.mouse.get_pos())
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.current_image.get_rect()
        self.rect.center = self.x, self.y

        self.collision_rect.center = self.rect.center

    def shoot(self):
        if gun.reload < 0:
            gun.shot(self.x + self.image.get_width() / 2 * cos(self.view_angle),
                     self.y + self.image.get_height() / 2 * sin(self.view_angle))
            gun.reload = gun.reload_speed

    def ray_cast(self):
        coords = self.start_ray_coords(self.x, self.y, self.view_angle)
        coords.extend(ray_cycle(self.x, self.y, self.view_angle, ray_obstacles, level_map.cell_w,
                                level_map.cell_h, level_map.map_w, level_map.map_h, self.fov))
        pygame.draw.polygon(SCREEN, 'black', coords)

    def start_ray_coords(self, x, y, alpha):
        if -pi <= alpha <= -pi / 2:
            return [(x, y), (WIDTH, HEIGHT), (0, HEIGHT), (0, 0),
                    (WIDTH, 0), (WIDTH, HEIGHT), (x, y)]
        elif -pi / 2 <= alpha <= 0:
            return [(x, y), (0, HEIGHT), (0, 0), (WIDTH, 0),
                    (WIDTH, HEIGHT), (0, HEIGHT), (x, y)]
        elif 0 <= alpha <= pi / 2:
            return [(x, y), (0, 0), (WIDTH, 0), (WIDTH, HEIGHT),
                    (0, HEIGHT), (0, 0), (x, y)]
        else:
            return [(x, y), (WIDTH, 0), (WIDTH, HEIGHT),
                    (0, HEIGHT), (0, 0), (WIDTH, 0), (x, y)]

    def move_character(self):
        # Здесь происходит управление игроком
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.movement(0, -self.v, enemies=False)
        if keys[pygame.K_s]:
            self.movement(0, self.v, enemies=False)
        if keys[pygame.K_a]:
            self.movement(-self.v, 0, enemies=False)
        if keys[pygame.K_d]:
            self.movement(self.v, 0, enemies=False)
        self.x, self.y = self.collision_rect.center
        self.rect.center = self.x, self.y

    def update(self):
        self.move_character()
        self.ray_cast()
        self.view_angle = self.update_angle(*pygame.mouse.get_pos())
        self.current_image = pygame.transform.rotate(self.image, -degrees(self.view_angle))
        # pygame.draw.rect(SCREEN, 'white', self.collision_rect)
        SCREEN.blit(self.current_image, self.rect)


class Enemy(Character):
    def __init__(self, x, y, complexity):
        super(Enemy, self).__init__()
        self.x = x
        self.y = y
        self.location = (self.y // level_map.cell_h, self.x // level_map.cell_w)
        self.destination = self.location  # Точка, в которую нужно идти

        self.hp, self.dmg, self.speed, self.weight = ENEMY_TYPES[complexity]
        self.radius = 20
        self.view_angle = 0
        self.vx, self.vy = 0, 0
        self.dx, self.dy = 0, 0

        self.image = ENEMY_IMAGE
        self.current_image = self.image

        self.rect = self.current_image.get_rect()
        self.rect.center = self.x, self.y
        self.collision_rect.center = self.rect.center

        obstacles.append(self.collision_rect)
        enemy_rects.append(self.collision_rect)
        enemies_group.add(self)

    def move(self):
        # Метод ищет следующую точку пути и меняет значения скорости, если попала пуля
        ray_coords = (self.collision_rect.topleft, self.collision_rect.topright,
                      self.collision_rect.bottomright, self.collision_rect.bottomleft)
        # Проверяет, находится ли игрок в зоне видимости
        if all((in_view(*pos, player.x, player.y, ray_obstacles)
                for pos in ray_coords)):
            self.view_angle = atan2(player.y - self.y, player.x - self.x)
        else:
            x1, y1 = self.destination
            self.view_angle = atan2(y1 * level_map.cell_h + level_map.cell_h // 2 - self.y,
                                    x1 * level_map.cell_w + level_map.cell_w // 2 - self.x)

        vx0 = cos(self.view_angle) * self.speed
        vy0 = sin(self.view_angle) * self.speed
        self.vx = vx0 + self.dx
        self.vy = vy0 + self.dy
        self.movement(self.vx, self.vy)

        if self.dx * (vx0 + self.dx) > 0:
            self.dx += vx0
        else:
            self.dx = 0
        if self.dy * (vy0 + self.dy) > 0:
            self.dy += vy0
        else:
            self.dy = 0

    def dead(self):
        obstacles.remove(self.collision_rect)
        enemy_rects.remove(self.collision_rect)
        chance = random()
        if chance <= 10000:
            Drop(self.x, self.y)
        self.kill()

    def update(self):
        if self.hp <= 0:
            self.dead()

        self.view_angle = self.update_angle(player.x, player.y)
        self.location = (self.y // level_map.cell_h, self.x // level_map.cell_w)
        self.destination = level_map.cheapest_path(*self.location)

        self.move()
        self.change_coords()
        self.x, self.y = self.collision_rect.center
        self.rect.center = self.x, self.y
        self.current_image = pygame.transform.rotate(self.image, -degrees(self.view_angle))
        SCREEN.blit(self.current_image, self.rect)


class Weapon:
    def __init__(self):
        self.dmg = 70  # Урон пули
        self.reload_speed = 20  # Скорость перезарядки
        self.reload = self.reload_speed  # Таймер для скорости перезарядки
        self.accuracy = 0.1  # Точность
        self.a = -0.5  # Ускроение
        self.v0 = 50  # Начальная скорость
        self.bullets_weight = 10  # Масса пули
        self.multishot = 1  # Кол-во пулек за выстрел

    def shot(self, x, y):
        hover_shoot = pygame.mixer.Sound('sounds/hover_over_the_button.mp3')
        hover_shoot.set_volume(0.05)
        hover_shoot.play()
        mx, my = pygame.mouse.get_pos()
        phi = atan2(my - y, mx - x)
        for i in range(-self.multishot // 2, self.multishot // 2):
            alpha = randint(-int(self.accuracy * 1000), int(self.accuracy * 1000))
            Bullet(x, y, phi + alpha / 1000 + i / 100, self.v0, self.a,
                   self.dmg, self.bullets_weight)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, player_x, player_y, phi, v0, a, dmg, weight):
        super().__init__(bullets_group)
        self.point = pygame.Rect(player_x, player_y, 1, 1)
        self.current_image = BULLET_IMAGE
        self.phi = phi  # Угол полета пули
        self.v = v0
        self.a = a
        self.dmg = dmg
        self.weight = weight

        self.cos_phi = cos(phi)
        self.sin_phi = sin(phi)

        self.pos_x = player_x
        self.pos_y = player_y

    def update(self):
        # Изменяем полеожение пули и ее скорость
        if self.v <= 0:
            self.kill()
        if self.point.collidelistall(obstacles):
            self.kill()
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
        self.current_image = pygame.transform.rotate(BULLET_IMAGE, -degrees(self.phi))
        SCREEN.blit(self.current_image, self.point)

    def hit(self):
        # Отвечает за удар пули по врагу
        for enemy in enemies_group:
            if self.point.colliderect(enemy.rect):
                enemy.hp -= self.dmg
                enemy.impact(self.weight, self.v * self.cos_phi, self.v * self.sin_phi)
                self.kill()

    def bounce(self):
        # Рассчитвает рикошет пули
        for block in obstacles:
            if block not in enemy_rects and self.point.colliderect(block):
                x0 = self.pos_x - ((self.v - self.a) * self.cos_phi)
                y0 = self.pos_y - ((self.v - self.a) * self.sin_phi)
                # Точка пересечения с ректом
                x, y = block.clipline(x0, y0, self.pos_x, self.pos_y)[0]
                if (block.bottom - 2 <= y <= block.bottom + 2 or
                        block.top - 2 <= y <= block.top + 2):
                    self.sin_phi = -self.sin_phi
                else:
                    self.cos_phi = -self.cos_phi
                break


class Button:
    def __init__(self, width, height, action=None):
        self.width = width
        self.height = height
        self.action = action

    def draw(self, x, y, message):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hover_sound = pygame.mixer.Sound('sounds/hover_over_the_button.mp3')
        hover_sound.set_volume(0.1)

        if x < mouse[0] < x + self.width and y < mouse[1] < y + self.height:
            pygame.draw.rect(SCREEN, (18, 19, 171), (x, y, self.width, self.height))
            if click[0] == 1:
                if self.action:
                    hover_sound.play()
                    pygame.mixer.music.stop()
                    self.action()
        else:
            pygame.draw.rect(SCREEN, (68, 53, 212), (x, y, self.width, self.height))
        self.print_text(message, x + 5, y + 5)

    def print_text(self, message, x, y, font_color=(0, 0, 0),
                   font_type=None, font_size=32):
        font_type = pygame.font.Font(font_type, font_size)
        text = font_type.render(message, True, font_color)
        SCREEN.blit(text, (x, y))


def fps_counter():
    font = pygame.font.Font(None, 20)
    text = font.render(str(round(CLOCK.get_fps(), 4)), True, 'white')
    text_x = 0
    text_y = 0
    SCREEN.blit(text, (text_x, text_y))


def go_game():
    init_globals()
    exit_button = Button(100, 25, start_menu)
    pygame.mixer.music.load('sounds/background_game.mp3')
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)

    pause = False
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause = not pause
        if not pause:
            if pygame.mouse.get_pressed()[0]:
                player.shoot()
            all_sprites.draw(SCREEN)

            bullets_group.update()
            gun.reload -= 1
            level_map.update()
            enemies_group.update()
            spawn_points_group.update()
            drops_group.update()
            player.update()

            fps_counter()

        exit_button.draw(WIDTH - 120, 10, 'В меню')
        pygame.display.flip()
        CLOCK.tick(FPS)


def clear_groups():
    all_sprites.empty()
    walls_group.empty()
    enemies_group.empty()
    bullets_group.empty()
    spawn_points_group.empty()


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
    clear_groups()
    menu_background = pygame.image.load('pictures/menu.jpg')

    font_game = pygame.font.Font(None, 112)
    start_button = Button(280, 70, go_game)
    quit_button = Button(280, 70, quit)
    pygame.mixer.music.load('sounds/background_menu.mp3')
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
        SCREEN.blit(menu_background, (0, 0))
        SCREEN.blit(font_game.render('Ray Shooter', True, (18, 19, 171)),
                    font_game.render('Ray Shooter', True, (18, 19, 171)).get_rect(
                        center=(500, 300)))
        start_button.draw(270, 600, 'Начать игру')
        quit_button.draw(270, 700, 'Выход')
        pygame.display.update()
        CLOCK.tick(60)


def init_globals():
    global player, level_map, floor, gun, enemy_rects, obstacles, ray_obstacles
    level_map = Level()
    floor = Floor()
    gun = Weapon()
    player = Player(100, 10)
    enemy_rects = []
    obstacles = [wall.rect for wall in walls_group]  # Спиоск всех преград
    ray_obstacles = List([(wall.rect.x, wall.rect.y,
                           wall.rect.w, wall.rect.h) for wall in walls_group])


if __name__ == '__main__':
    init_globals()
    start_menu()
