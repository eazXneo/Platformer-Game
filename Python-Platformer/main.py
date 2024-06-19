import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False)for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    """
    direction=False means only one direction
    """
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheets = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheets.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheets, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    # TODO make it show the pink platform by changing where the rect is
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class GameConfig():
    def __init__(self):
        self.block_size = 96

        """
        floor = [Block(i* block_size, HEIGHT - block_size, block_size) 
            for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
        objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
                Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]
        """

        self.ground = self.calc_ground()
        self.static_enemies = self.calc_static_enemies()
        
        # this is annoying (make list, turn on by default.)
        # self.static_enemies.on()

        # self.ground = [Block(100, HEIGHT -  block_size, block_size)]
        self.all_blocks = [*self.ground, *self.static_enemies]

    def calc_ground(self):
        ground = []

        list_blocks = [ [0,0], [1,0], [2,0], [3,0], [6,0],
                        [8,2], [9,2], [10,2], [11,0], [12,0],
                        [12,3], [13,0], [14,0], [16,0], [17,0],
                        [18,0], [20,1], [21,2], [23,4], [24,4],
                        [24,1], [25,1], [25,4], [27,0], [28,0],
                        [30,2], [32,0], [33,0], [36,0], [37,0],
                        [37,3], [39,0], [39,1], [40,0], [40,1],
                        [40,2], [42,4], [43,5], [44,5], [46,4],
                        [46,6], [47,4], [48,4], [49,6],
                        [51,0], [52,0], [53,0], [54,2]
                    ]
        
        for b in list_blocks:
            ground.append(Block(
                    100 + (b[0] * self.block_size), 
                    HEIGHT - (self.block_size * (b[1] + 1)), 
                    self.block_size))

        return ground
    
    def calc_static_enemies(self):
        s_enemies = []

        list_blocks = [ [5,0], [7,0], [11,1], [12,1], [13,1],
                        [13,3], [14,1], [24,2], [25,2], [29,2],
                        [31,2], [32,1], [37,1], [43,6], [46,5],
                        [47,5], [48,5]
                    ]

        for b in list_blocks:
            new_s_enemy = Spike(100 + (b[0] * self.block_size), HEIGHT - (self.block_size * b[1]) - 32, 16, 16)
            s_enemies.append(new_s_enemy)

        return s_enemies
     
    def get_static_enemy(self):
        return self.static_enemies
    
    def get_all_blocks(self):
        return self.all_blocks

    def debug_game_config(self):
        safety_blocks = [Block(-192 + (i * self.block_size), HEIGHT, self.block_size) 
            for i in range(60)]
        self.all_blocks += safety_blocks


class Player(pygame.sprite.Sprite):
    """
    Pygame Sprite allows for methods to detect collisions ... ???
    """

    COLOUR = (100, 0, 100)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
    ANIMATION_DELAY = 4

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = 0
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
    
    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        # gravity (only falling for now)
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1
        
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Spike(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        self.spike = load_sprite_sheets("Traps", "Spikes", width, height)
        self.image = self.spike["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
    
    def draw(self, win, offset_x, angle=0):
        win.blit(pygame.transform.rotate(self.image, 90), (self.rect.x - offset_x, self.rect.y))


def get_background(name):
    """
    returns list of all background tiles that we need to draw
    """

    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x):
    """
    draw (actually visible) background, players, obstacles
    """

    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)


    # TODO: add WASD
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    # remember handle_vertical_collision() returns a list and collide() returns only one object
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Pink.png")
    
    player = Player(100, 100, 50, 50)
    
    gameConfig = GameConfig()
    # DEBUG set
    gameConfig.debug_game_config()

    # s_enemy = gameConfig.get_static_enemy()[0]
    objects = gameConfig.get_all_blocks()
    
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                # TODO: use K_UP?
                if (event.key == pygame.K_UP or event.key == pygame.K_SPACE or event.key == pygame.K_w) and player.jump_count < 2:
                    player.jump() 

        player.loop(FPS)
        # fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        # scroll window horizontally
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
    
    pygame.quit()
    quit()

if __name__=="__main__":
    main(window)
