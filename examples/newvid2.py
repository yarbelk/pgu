import pygame
from pygame.locals import *
from pygame.rect import Rect
from random import random
pygame.init()

# the following line is not needed if pgu is installed
import sys; sys.path.insert(0, "..")

from pgu import newvid

SW,SH = 320,240
TW,TH = 16,16
frame_rate =16

class AnimatedSprite(newvid.PguSprite):
    def __init__(self, *args, **kwargs):
        self.moving = False
        self.target_pos = None
        self.dx = self.dy = 0
        self._dx = self._dy = 0
        super(AnimatedSprite, self).__init__(*args, **kwargs)

    def move(self, pos):
#        if self.moving:
#            return
        self.moving = True
        self.target_pos = newvid.Pos(pos)
        self.target_surface_pos = self.get_surface_pos(pos)
        self._dx = float(self.target_surface_pos[0] - self.rect[0]) / frame_rate
        self._dy = float(self.target_surface_pos[1] - self.rect[1]) / frame_rate
        print "_dx, _dy: {self._dx}, {self._dy}".format(self=self)
        print "pos: {self.pos}".format(self=self)
        print "surface_pos: {}".format(self.get_surface_pos(self.pos))
        print "target_pos: {self.target_pos}".format(self=self)
        print "target_surface_pos: {self.target_surface_pos}".format(self=self)

    def _set_dX(self):
        self.dx, self.dy = self.dx + self._dx, self.dy + self._dy

    def update(self, clock, *args):
        if self.moving:
            if self.target_surface_pos == self.rect:
                self.pos = self.target_pos
                self.moving = False
                self.dx = self.dy = self._dx = self._dy = 0
            self._set_dX()
            self.rect[0] += self.dx
            self.rect[1] += self.dy
            if int(self.dx) >= 1:
                self.dx = 0
            if int(self.dy) >= 1:
                self.dy = 0
            self.dirty = 1 if self.dirty < 2 else 2

def init():
    screen = pygame.display.set_mode((SW,SH),HWSURFACE)
    layer_group = pygame.sprite.LayeredDirty()
    bg_group = pygame.sprite.RenderUpdates()
    sprite_group = pygame.sprite.RenderUpdates()
    g = newvid.NewVid(screen=screen, layer_group=layer_group,
                      bg_group=bg_group)
    g.view = screen.get_rect()
    g.old_view = Rect(g.view)
    map_obj = newvid.TileMap(layer_group, bg_group)
    g.map_bg = map_obj

    tiles = [[newvid.Tile(pygame.Surface((16,16)),
                        newvid.Pos(16,16),
                        newvid.Pos(1,1),
                        {},
                        newvid.Pos(x,y),
                        layer_group, bg_group)
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

    sprite_col = newvid.SpriteCollection(layer_group, sprite_group, sprite_file=None)

    sprite = AnimatedSprite(
                        pygame.Surface((16,16)),
                        newvid.Pos(16,16),
                        newvid.Pos(1,1),
                        {},
                        newvid.Pos(0, 0),
                        layer_group,
                        sprite_group)
    sprite.image.fill(Color(255,0,0))

#    sprite2 = AnimatedSprite(
#                        pygame.Surface((16,16)),
#                        newvid.Pos(16,16),
#                        newvid.Pos(1,1),
#                        {},
#                        newvid.Pos(1, 0),
#                        layer_group,
#                        sprite_group)
#    sprite2.image.fill(Color(255,0,0))
#
    sprite_col.sprites = [sprite]
    g.sprites = sprite_col


    return g

def run(g):
    g.quit = 0

    g.map_bg.set_bg()
    g.draw(g.screen, g.screen.get_rect())
    pygame.display.flip()
    clock = pygame.time.Clock()

    while not g.quit:
        for e in pygame.event.get():
            if e.type is QUIT:
                g.quit = 1
            if e.type is KEYDOWN:
                if e.key == K_ESCAPE:
                    g.quit = 1
                if e.key == K_UP:
                    for sprite in g.sprites.sprites:
                        sprite.move((sprite.pos.x, (sprite.pos.y - 2) % 15))
                if e.key == K_DOWN:
                    for sprite in g.sprites.sprites:
                        sprite.move((sprite.pos.x, (sprite.pos.y + 2) % 15))
                if e.key == K_LEFT:
                    for sprite in g.sprites.sprites:
                        sprite.move(((sprite.pos.x - 2) % 20, sprite.pos.y))
                if e.key == K_RIGHT:
                    for sprite in g.sprites.sprites:
                        sprite.move(((sprite.pos.x + 2) % 20, sprite.pos.y))
        clock.tick(frame_rate)
        g.sprites.update(clock)
        g.draw(g.screen, g.screen.get_rect())
        pygame.display.flip()

run(init())
