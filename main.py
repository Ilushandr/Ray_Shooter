import pygame
import os
import sys
from PIL import Image
from numba import njit, prange
from numba.typed import List
from math import cos, sin, atan2, inf, pi
from collections import deque
from random import randint

pygame.init()
display_info = pygame.display.Info()
#  Достаются значения разрешения экрана из display_info
size = width, height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode(size)
fps = 60
clock = pygame.time.Clock()
level = 4

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
        player.update()

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


def print_text(message, x, y, font_color=(0, 0, 0),
               font_type=None, font_size=32):
    font_type = pygame.font.Font(font_type, font_size)
    text = font_type.render(message, True, font_color)
    screen.blit(text, (x, y))


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
        print_text(message, x + 10, y + 10)


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

    def ray_cast(self):
        mx, my = pygame.mouse.get_pos()
        view_angle = atan2(my - self.y, mx - self.x)  # Считает угол относительно курсора
        collide_walls = [wall.rect for wall in walls]  # Спиоск всех преград

        # Начальные координаты многоугольника, по которому рисуется рейкаст
        coords = [(self.x + self.radius, self.y + self.radius)]
        for a in range(-self.fov, self.fov + 1):  # Цикл по углу обзора
            # Заранее считаем синус и косинус, шоб ресурсы потом не тратить
            # На 100 делится для точности и птушо в for пихается тока целые числа,
            # а fov у нас в радианах (радианы если шо от 0 до 6.3, а ля 0 до 360 в градусах)
            cos_a = cos(view_angle + a / 100)
            sin_a = sin(view_angle + a / 100)
            # Задаем rect как точку концов линий рейкаста
            point = pygame.Rect(self.x, self.y, 1, 1)

            # Цикл увеличения дистанции. Чем больше шаг, тем выше произ-ть,
            # но ниже точность рейкаста
            for c in range(0, 500, 20):
                point.x = self.x + c * cos_a
                point.y = self.y + c * sin_a
                if point.collidelistall(collide_walls):  # Если точка достигает стены
                    # Тут уже начинается подгон точки под границы ректа бинарным поиском
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

        #  Наконец рисуем полигон
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
    size = width, height = 800, 600
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    player = Player(10, 80)
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
