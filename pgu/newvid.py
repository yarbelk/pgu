"""Sprite and tile engine.

tilevid, isovid, hexvid are all subclasses of this interface.

Includes support for:

* Foreground Tiles
* Background Tiles
* Sprites
* Sprite-Sprite Collision handling
* Sprite-Tile Collision handling
* Scrolling
* Loading from PGU tile and sprite formats (optional)
* Set rate FPS (optional)

This code was previously known as the King James Version (named after the
Bible of the same name for historical reasons.)

"""

import pygame
from pygame.rect import Rect
from pygame.locals import *
import math
from collections import namedtuple
import yaml

PosT = namedtuple('Pos',('x', 'y', 'z'))

Pos = lambda x, y, z=0: PosT(x, y, z)
def Pos(*args):
    if type(args[0]) == PosT:
        return args[0]
    if len(args) == 2:
        args = args + (0,)
    return PosT(*args)
# Iso and Hex use 3 coords, so make this support it by default


class GeometryMixin(object):
    """basic geometyr mixin for square/rectangle geometries"""
    def get_pos(self, coords, offset=None):
        """Get a tile index from a pixel coord"""
        coords = Pos(coords)
        if offset is not None:
            offset = Pos(offset)
        else:
            offset =  Pos(0,0)
        coords = Pos(coords.x + offset.x, coords.y + offset.y)
        return Pos(coords.x / self.size.x, coords.y / self.size.y)

    def dist(self, sprite):
        return max(abs(self.pos.x - sprite.pos.x),
                   abs(self.pos.y - sprite.pos.y),
                   abs(self.pos.z - sprite.pos.z))


class BaseSprite(pygame.sprite.DirtySprite):
    def __init__(self, image, size, attributes, pos, *groups):
        self.image = image
        self.size = Pos(size)
        self.pos = Pos(size)
        self.old_pos = Pos(self.pos)
        surf_pos = self.get_surface_pos(pos)
        self.rect = Rect(surf_pos.x, surf_pos.y, size.x, size.y)
        self.old_rect = Rect(self.rect)
        super(BaseSprite, self).__init__(*groups)

    def move(self, pos):
        self.old_pos = Pos(self.pos)
        self.pos = Pos(pos)
        surf_pos = self.get_surface_pos(pos)
        self.rect = Rect(surf_pos.x, surf_pos.y, self.size.x, self.size.y)
        self.old_rect = Rect(self.rect)
        self.dirty = 1 if self.dirty < 2 else 2

    def get_surface_pos(self, pos):
        """Return a position to blit based on the tile coords passed in.
        useful for iso and hex grids."""
        pos = Pos(pos)
        top_left = pos.x * self.size[0]
        top_right = pos.y * self.size[1]
        return Rect(top_left, top_right, self.size.x, self.size.y)



class Tile(BaseSprite):
    """
    A tile, which is an image, size and position in tile coords
    """
    def __init__(self, image, pos, size=None, attributes=None,
                groups=tuple()):
        self.image = image
        self.pos = Pos(pos)
        size = size or image.size
        self.size = Pos(size)
        self.rect = self.get_surface_pos(pos)
        self.attributes = attributes
        pygame.sprite.DirtySprite.__init__(self, *groups)


class PguSprite(BaseSprite):
    pass


class SpriteCollectionMixin(object):
    """
    Mixin to hold logic for a collection of sprites (tiles, units, etc)
    """

    def load_atlas(self, atlas_file):
        self.atlas = Atlas(atlas_file)

    def paint_regions(self, surface, regions):
        """Paints regions supplied to the surface supplied"""
        for region in regions:
            self.tile_group.repaint_rect(self.surface, region)
            subsurface = self.surface.subsurface(region)
            surface.blit(subsurface, region)

    def set_draw_rect(self, surface, view):
        raise NotImplemented


class TileMap(GeometryMixin, SpriteCollectionMixin):
    """
    A container to hold the background tile map.

    Attributes:
        size -- size in tiles of the map
        atlas -- image atlas
        tile_descriptiors -- tile information loaded from map_file
        size -- size of tile in pixels.  Defaults to the size of the tile
                     image
        tiles -- 2d array of the tiles (Tile objects)
    """

    def __init__(self, map_file=None):
        self.tile_group = pygame.sprite.RenderUpdates()
        if map_file:
            self.load_map(map_file)
        self.surface = pygame.surface.Surface((320, 240))

    def load_map(self, map_file):
        with open(map_file) as map_fd:
            data = yaml.load_all(map_fd)
        self.size = data['meta']['size']
        self.atlas = self.load_atlas(data['meta']['atlas'])
        self.tile_descriptors = data['tiles']
        self.tile_size = Pos(data['tile_size'])
        self.tiles = [[Tile(self.atlas[tile['image']],
                           tile['pos'],
                           size=self.tile_size,
                           attributes=tile['attributes'],
                           groups=self.tile_group)
                           for tile in 
                           tile_row] for tile_row in self.tile_descriptors]

    def draw_map(self):
        """Paints full map onto the internal surface"""
        for tile_row in self.tiles:
            for tile in tile_row:
                tile.dirty = 1 if tile.dirty <2 else 2
        self.tile_group.draw(self.surface)

    def set_tile(self, tile, pos):
        tile.pos = pos
        tile.dirty = 1 if tile.dirty < 2 else 2
        self.tiles[pos.y][pos.x] = tile

    def draw(self, surface):
        return self.tile_group.draw(surface)

    def set_draw_rect(self, surface, view):
        for sprite in self.tile_group:
            sprite.dirty = 1 if sprite.dirty < 2 else 2


class SpriteCollection(SpriteCollectionMixin):
    def __init__(self, sprite_file=None):
        self.sprite_group = pygame.sprite.RenderUpdates()
        if sprite_file:
            self.load_sprites(sprite_file)

    def load_sprites(self, sprite_file):
        with open(sprite_file) as sprite_fd:
            data = yaml.load_all(sprite_fd)
        self.size = data['meta']['size']
        self.atlas = self.load_atlas(data['meta']['atlas'])
        self.sprites = data['sprites']  # use !!python/object:sprite.SomeSprite
        for sprite in self.sprites:
            sprite.add(self.sprite_group)

    def draw(self, surface):
        self.sprite_group.draw(surface)

    def set_draw_rect(self, surface, view):
        for sprite in self.sprite_group:
            sprite.dirty = 1 if sprite.dirty < 2 else 2


class NewVid(object):
    """
    This is a tile engine for keeping a background layer and a forground
    layers.
    """
    def __init__(self, screen, map_file=None, sprite_file=None):
        self.view = pygame.Rect(0, 0, 0, 0)
        self.old_view = pygame.Rect(self.view)
        self.screen = screen
        #self.map_bg = self.load_map(map_file)
        #self.sprites = self.load_sprites(sprite_file)

    def load_map(self, map_file):
        self.map_bg = TileMap(map_file)
        self.map_bg.draw_map()

    def load_sprites(self, sprite_file):
        self.sprites = SpriteCollection(sprite_file)

    def draw(self, surface, view):
        self.map_bg.set_draw_rect(surface,self.view)
        self.sprites.set_draw_rect(surface,self.view)
        self.map_bg.draw(surface)
        self.sprites.draw(surface)
