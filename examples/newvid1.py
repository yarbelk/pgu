import pygame
from pygame.locals import *
from pygame.rect import Rect
from random import random

# the following line is not needed if pgu is installed
import sys; sys.path.insert(0, "..")

from pgu import newvid

SW,SH = 320,240
TW,TH = 16,16

def init():
    screen = pygame.display.set_mode((SW,SH),HWSURFACE)
    g = newvid.NewVid(screen=screen)
    g.view = screen.get_rect()
    g.old_view = screen.get_rect()
    map_obj = newvid.TileMap()
    g.map_bg = map_obj

    tiles = [[newvid.Tile(pygame.Surface((16,16)),
                        newvid.Pos(x,y),
                        newvid.Pos(16,16))
                        for x in xrange(20)] for y in xrange(15)]
    for tile_row in tiles:
        for tile in tile_row:
            c = Color(1,2,3)
            c.hsva = (int(random() * 255),70 ,70, 70); c
            tile.image.fill(c)
            tile.add(g.map_bg.tile_group)
    map_obj.tiles = tiles
    for y, tile_row in enumerate(tiles):
        for x, tile in enumerate(tile_row):
            map_obj.set_tile(tile, newvid.Pos(x,y))

    map_obj.tile_size = newvid.Pos(16,16)
    map_obj.size = newvid.Pos(20, 15)

    sprites = newvid.SpriteCollection()

    sprite = newvid.PguSprite(pygame.Surface((16,16)),
                        newvid.Pos(16,16), None,
                        newvid.Pos(int(random() * 20),int(random() * 15)),)
    sprite.image.fill(Color(0,0,0))
    sprite.add(sprites.sprite_group)

    sprites.sprites = [sprite,]
    g.sprites = sprites


    return g

def run(g):
    g.quit = 0

    g.map_bg.draw_map()
    g.draw(g.screen, g.screen.get_rect())
    pygame.display.flip()

    while not g.quit:
        for e in pygame.event.get():
            if e.type is QUIT: g.quit = 1
            if e.type is KEYDOWN and e.key == K_ESCAPE: g.quit = 1
            if e.type is KEYDOWN and e.key != K_ESCAPE:
                for sprite in g.sprites.sprites:
                    sprite.move(newvid.Pos(int(random() * 20), int(random() * 15)))
        g.draw(g.screen, g.screen.get_rect())
        pygame.display.flip()

run(init())
