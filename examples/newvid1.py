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
    layer_group = pygame.sprite.LayeredDirty()
    g = newvid.NewVid(screen=screen, layer_group=layer_group)
    g.view = screen.get_rect()
    g.old_view = Rect(g.view)
    map_obj = newvid.TileMap(layer_group)
    g.map_bg = map_obj

    tiles = [[newvid.Tile(pygame.Surface((16,16)),
                        newvid.Pos(16,16),
                        newvid.Pos(1,1),
                        {},
                        newvid.Pos(x,y),
                        layer_group,)
                        for x in xrange(20)] for y in xrange(15)]
    for tile_row in tiles:
        for tile in tile_row:
            c = Color(1,2,3)
            c.hsva = (int(random() * 255),30,70, 70); c
            tile.image.fill(c)
    map_obj.sprites = tiles
    map_obj.tile_size = newvid.Pos(16,16)
    map_obj.size = newvid.Pos(20, 15)
    map_obj.surface = pygame.surface.Surface((SW, SH))
    map_obj.set_bg()
#
#    sprites = newvid.SpriteCollection()
#
#    sprite = newvid.PguSprite(pygame.Surface((16,16)),
#                        newvid.Pos(16,16), None,
#                        newvid.Pos(0, 0),)
#    sprite.image.fill(Color(255,0,0))
#    sprite.add(sprites.sprite_group)
#
#    sprite2 = newvid.PguSprite(pygame.Surface((16,16)),
#                        newvid.Pos(32,32), None,
#                        newvid.Pos(10,10),)
#    sprite2.image.fill(Color(0,255,0))
#    sprite2.add(sprites.sprite_group)
#    sprites.sprites = [sprite, sprite2]
#    for sprite in sprites.sprites:
#        print sprite.pos
#    g.sprites = sprites


    return g

def run(g):
    g.quit = 0

    g.map_bg.draw_map()
    g.draw_bg(g.screen)
    g.draw(g.screen, g.screen.get_rect())
    pygame.display.flip()

    while not g.quit:
        for e in pygame.event.get():
            if e.type is QUIT:
                g.quit = 1
            if e.type is KEYDOWN:
                if e.key == K_ESCAPE:
                    g.quit = 1
                if e.key == K_UP:
                    for sprite in g.sprites.sprites:
                        sprite.move((sprite.pos.x, (sprite.pos.y - 1) % 15))
                if e.key == K_DOWN:
                    for sprite in g.sprites.sprites:
                        sprite.move((sprite.pos.x, (sprite.pos.y + 1) % 15))
                if e.key == K_LEFT:
                    for sprite in g.sprites.sprites:
                        sprite.move(((sprite.pos.x - 1) % 20, sprite.pos.y))
                if e.key == K_RIGHT:
                    for sprite in g.sprites.sprites:
                        sprite.move(((sprite.pos.x + 1) % 20, sprite.pos.y))
        g.draw(g.screen, g.screen.get_rect())
        pygame.display.flip()

run(init())
