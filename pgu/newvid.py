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

PosL = lambda x, y, z=0: PosT(x, y, z)
def Pos(*args):
    if type(args[0]) == PosT:
        return args[0]
    if type(args[0]) == tuple:
        return PosL(*(args[0]))
    return PosL(*args)
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
    def __init__(self, image, tile_size, size, attributes, pos, *groups):
        self.image = image
        self.tile_size = Pos(tile_size)
        self.size = Pos(size)
        self.pos = Pos(pos)
        self.old_pos = Pos(self.pos)
        self.rect = self.get_surface_pos(pos)
        self.old_rect = Rect(self.rect)
        self.groups = groups
        self.dirty = 1
        for attribute in attributes:
            if self.hasattr(attribute):
                self.setattr(attributes[attribute])
            else:
                raise AttributeError("Bad Attribute")
        super(BaseSprite, self).__init__(*groups)

    def move(self, pos):
        self.old_pos = Pos(self.pos)
        self.pos = Pos(pos)
        surf_pos = self.get_surface_pos(pos)
        self.rect = Rect(surf_pos.x, surf_pos.y, self.tile_size.x, self.tile_size.y)
        self.old_rect = Rect(self.rect)
        self.dirty = 1 if self.dirty < 2 else 2

    def get_surface_pos(self, pos):
        """Return a position to blit based on the tile coords passed in.
        useful for iso and hex grids."""
        pos = Pos(pos)
        top_left = pos.x * self.tile_size[0]
        top_right = pos.y * self.tile_size[1]
        return Rect(top_left, top_right, self.tile_size.x, self.tile_size.y)



class Tile(BaseSprite):
    """
    A tile, which is an image, size and position in tile coords
    """
    def __init__(self, image, tile_size, size, attributes, pos,
            *groups):
        self._layer = -1
        super(Tile, self).__init__(image, tile_size, size, attributes, pos,
                *groups)


class PguSprite(BaseSprite):
    def __init__(self, image, tile_size, size, attributes, pos,
            *groups):
        self._layer = 0
        super(PguSprite, self).__init__(image, tile_size, size, attributes, pos,
                *groups)


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

    def get_old_rects(self):
        """ return the old positions of sprites that are dirty """
        dirty_rects = []
        for sprite in self.sprites:
            if sprite.dirty:
                dirty_rects.append([sprite.rect])
        return dirty_rects


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

    def __init__(self, layer_group, bg_group,  map_file=None, *groups):
        self.layer_group = layer_group
        self.bg_group = bg_group
        self.groups = groups + (layer_group, bg_group)
        if map_file:
            self.load_map(map_file, groups)

    def load_map(self, map_file):
        with open(map_file) as map_fd:
            data = yaml.load_all(map_fd)
        self.size = data['meta']['size']
        self.atlas = self.load_atlas(data['meta']['atlas'])
        self.tile_descriptors = data['tiles']
        self.tile_size = Pos(data['tile_size'])
        self.sprites = [[Tile(self.atlas[tile['image']],
                           tile_size=self.tile_size,
                           size=tile['size'],
                           attributes=tile['attributes'],
                           pos=tile['pos'],
                           *self.group)
                           for tile in
                           tile_row] for tile_row in self.tile_descriptors]
        self.surface = pygame.surface.Surface((size[0] * tile_size[0],
                                              size[1] * tile_size[1]))

    def set_bg(self):
        self.bg_group.draw(self.surface)
        self.layer_group._bgd = self.surface

    def get_bg(self):
        return self.surface

    def set_tile(self, tile, pos):
        tile.pos = pos
        tile.dirty = 1 if tile.dirty < 2 else 2
        self.sprites[pos[1]][pos[0]].kill()
        self.sprites[pos[1]][pos[0]] = tile
        self.surface.blit(tile)


class SpriteCollection(SpriteCollectionMixin):
    def __init__(self, layer_group, sprite_group, sprite_file=None, *groups):
        self.layer_group = layer_group
        self.sprite_group = sprite_group
        self.groups = groups + (layer_group, sprite_group)
        if sprite_file:
            self.load_sprites(sprite_file, groups)

    def load_sprites(self, sprite_file):
        with open(sprite_file) as sprite_fd:
            data = yaml.load_all(sprite_fd)
        self.size = data['meta']['size']
        self.atlas = self.load_atlas(data['meta']['atlas'])
        self.sprites = data['sprites']  # use !!python/object:sprite.SomeSprite
        for sprite in self.sprites:
            sprite.add(self.sprite_group)


class NewVid(object):
    """
    This is a tile engine for keeping a background layer and a forground
    layers.
    """
    def __init__(self, screen, layer_group, bg_group, map_file=None, sprite_file=None,
            *groups):
        self.view = pygame.Rect(0, 0, 0, 0)
        self.old_view = pygame.Rect(self.view)
        self.screen = screen
        #self.map_bg = self.load_map(map_file)
        #self.sprites = self.load_sprites(sprite_file)
        self.layer_group = layer_group
        self.bg_group = bg_group

    def load_map(self, map_file):
        self.map_bg = TileMap(layer_group, map_file, self.groups)
        self.map_bg.set_bg()

    def load_sprites(self, sprite_file):
        self.sprites = SpriteCollection(sprite_file,self.layer_group)

    def draw(self, surface, view):
        self.layer_group.clear(surface, self.map_bg.get_bg())
        self.layer_group.draw(surface)
