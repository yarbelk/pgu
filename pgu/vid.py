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


class _Sprite(pygame.DirtySprite):
    """ Base class for sprites and tiles

    Arguments:
        ishape -- an image, or an image, rectstyle.  The rectstyle will
            describe the shape of the image, used for collision
            detection.
    """
    #TODO make this inherit from pygame.sprite.DirtySprite
    # This would mean changing how updates are done, to take advantage of
    # dirtyness.
    def __init__(self, ishape=None, *groups):
        self.image = ishape
        self._image = self.image
        self.tile_h = self.image.get_height()
        self.tile_w = self.image.get_width()
        super(_Sprite, self).__init__(*groups)

    def __setattr__(self, k, v):
        if k == 'image' and v != None:
            self.image_h = v.get_height()
            self.image_w = v.get_width()
            self.tile_h = v.get_height()
            self.tile_w = v.get_width()
        self.__dict__[k] = v


class Sprite(_Sprite):
    """The object used for Sprites.

    Arguments:
        ishape -- an image, or an image, rectstyle.  The rectstyle will
            describe the shape of the image, used for collision
            detection.
        pos -- initial (x, y) position of the Sprite.

    Attributes:
        rect -- the current position of the Sprite
        _rect -- the previous position of the Sprite
        groups -- the groups the Sprite is in
        agroups -- the groups the Sprite can hit in a collision
        hit -- the handler for hits -- hit(g, s, a)
        loop -- the loop handler, called once a frame
        irect -- the bounding rectangle for the image

    """
    def __init__(self, ishape, pos, *groups):
        image, shape = self._ishape_tupple(ishape)
        super(Sprite, self).__init__(image)
        self.shape = shape
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], shape.w, shape.h)
        self._rect = pygame.Rect(self.rect)
        self.irect = pygame.Rect(pos[0]-self.shape.x, pos[1]-self.shape.y,
            image.get_width(), image.get_height())
        self._irect = pygame.Rect(self.irect)
        super(Sprite, self).__init__(*groups)

    def _ishape_tupple(self, ishape):
        if not isinstance(ishape, tuple):
            ishape = ishape, None
        image, shape = ishape
        if isinstance(shape, tuple):
            shape = pygame.Rect(shape)
        if shape == None:
            shape = pygame.Rect(0, 0, image.get_width(), image.get_height())
        return (image, shape)

    def setimage(self, ishape):
        """Set the image of the Sprite.

        Arguments:
            ishape -- an image, or an image, rectstyle.  The rectstyle will
                      describe the shape of the image, used for collision detection.

        """
        image, shape = self._ishape_tupple(ishape)
        self.image = image
        self.shape = shape
        self.rect.w, self.rect.h = shape.w, shape.h
        self.irect.w, self.irect.h = image.get_width(), image.get_height()
        self.updated = 1

class Tile(_Sprite):
    """Tile Object used by TileCollide.

    Arguments:
        image -- an image for the Tile.

    Attributes:
        agroups -- the groups the Tile can hit in a collision
        hit -- the handler for hits -- hit(g, t, a)

    """
    def __init__(self, image=None):
        super(Tile, self).__init__(image)


class NewVid(object):
    """
    layers - bg, icon, top,
    """
    def __init__(self, max_tile_size=256):
        self.sprites = pygame.sprite.RenderUpdates()
        self.layers = pygame.sprite.LayeredDirty(default_layer='fg')
        self.size = None
        self.view = pygame.Rect(0, 0, 0, 0)
        self._view = pygame.Rect(self.view)
        self.bounds = None

    def get_sprite_blit_rect(self, pos, sprite):
        sprite_rect = sprite.get_rect()
        sprite_rect.top_left = pos
        return sprite_rect

    def set(self, pos, sprite):
        sprite.pos = pos
        sprite.rect = self.get_sprite_blit_rect(pos, sprite)
        sprite.dirty = 1 if sprite.dirty != 2 else 2

    def get(self, pos):
        """Get a sprite from the forground """
        sprites = self.layers.get_sprites_at(pos)
        for sprite in sprites:
            if sprite.layer == 'fg':
                return sprite

    def paint(self, surface):
        return self.layers.draw(surface)

    def update(self, screen):
        self.layers.update(*args)

    def tga_load_level(self, fname, bg=0):
        """Load a TGA level.

        Arguments:
            g        -- a Tilevid instance
            fname    -- tga image to load
            bg        -- set to 1 if you wish to load the background layer

        """
        if type(fname) == str: img = pygame.image.load(fname)
        else: img = fname
        w, h = img.get_width(), img.get_height()
        self.resize((w, h), bg)
        for y in range(0, h):
            for x in range(0, w):
                fg, bg, code, _a = img.get_at((x, y))
                t_sprite = Sprite()
                t_sprite.layer = 'fg'
                t_sprite.add(self.layers)
                self.tlayer[y][x] = t

                if bg:
                    b_sprite = Sprite()
                    b_sprite.layer = 'bg'
                    b_sprite.add(self.layers)
                    self.blayer[y][x] = b
                self.clayer[y][x] = c

    def tga_load_tiles(self, fname, size, tdata={}):
        """Load a TGA tileset.

        Arguments:
            g       -- a Tilevid instance
            fname    -- tga image to load
            size    -- (w, h) size of tiles in pixels
            tdata    -- tile data, a dict of tile:(agroups, hit handler, config)

        """
        TW, TH = size
        if type(fname) == str:
            img = pygame.image.load(fname).convert_alpha()
        else: img = fname
        w, h = img.get_width(), img.get_height()

        n = 0
        for y in range(0, h, TH):
            for x in range(0, w, TW):
                i = img.subsurface((x, y, TW, TH))
                tile = Tile(i)
                tile.layer = 'bg'
                tile.add(self.layers)
                self.tiles[n] = tile
                if n in tdata:
                    agroups, hit, config = tdata[n]
                    tile.agroups = self.string2groups(agroups)
                    tile.hit = hit
                    tile.config = config
                n += 1


class Vid(object):
    """An engine for rendering Sprites and Tiles.

    Attributes:
        sprites -- a list of the Sprites to be displayed.  You may append and
                   remove Sprites from it.
        images  -- a dict for images to be put in.
        size    -- the width, height in Tiles of the layers.  Do not modify.
        view    -- a pygame.Rect of the viewed area.  You may change .x, .y,
                    etc to move the viewed area around.
        bounds  -- a pygame.Rect (set to None by default) that sets the bounds
                    of the viewable area.  Useful for setting certain borders
                    as not viewable.
        tlayer  -- the foreground tiles layer
        clayer  -- the code layer (optional)
        blayer  -- the background tiles layer (optional)
        groups  -- a hash of group names to group values (32 groups max, as a tile/sprites
                membership in a group is determined by the bits in an integer)

    """

    def __init__(self):
        self.tiles = [None for x in xrange(0, 256)]
        self.sprites = pygame.sprite.RenderUpdates()
        self.blayer = pygame.sprite.RenderUpdates()
        self.tlayer = pygame.sprite.RenderUpdates()
        self.alayer = pygame.sprite.RenderUpdates()
        self.size = None
        self.view = pygame.Rect(0, 0, 0, 0)
        self._view = pygame.Rect(self.view)
        self.bounds = None

    def resize(self, size, bg=0):
        """Resize the layers.

        Arguments:
            size -- w, h in Tiles of the layers
            bg   -- set to 1 if you wish to use both a foreground layer and a
                    background layer

        """
        self.size = size
        w, h = size
        self.layers = [[[0 for x in xrange(0, w)] for y in xrange(0, h)]
            for z in xrange(0, 4)]
        self.tlayer = self.layers[0]
        self.blayer = self.layers[1]
        if not bg: self.blayer = None
        self.clayer = self.layers[2]
        self.alayer = self.layers[3]

        self.view.x, self.view.y = 0, 0
        self._view.x, self.view.y = 0, 0
        self.bounds = None

        self.updates = []

    def set(self, pos, v):
        """Set a tile in the foreground to a value.

        Use this method to set tiles in the foreground, as it will make
        sure the screen is updated with the change.  Directly changing
        the tlayer will not guarantee updates unless you are using .paint()

        Arguments:
            pos -- (x, y) of tile
            v -- value

        """
        if self.tlayer[pos[1]][pos[0]] == v: return
        self.tlayer[pos[1]][pos[0]] = v
        self.alayer[pos[1]][pos[0]] = 1
        self.updates.append(pos)

    def get(self, pos):
        """Get the tlayer at pos.

        Arguments:
            pos -- (x, y) of tile

        """
        return self.tlayer[pos[1]][pos[0]]

    def paint(self, s):
        """Paint the screen.

        Arguments:
            screen -- a pygame.Surface to paint to

        Returns the updated portion of the screen (all of it)

        """
        return []

    def update(self, s):
        """Update the screen.

        Arguments:
            screen -- a pygame.Rect to update

        Returns a list of updated rectangles.

        """
        self.updates = []
        return []

    def tga_load_level(self, fname, bg=0):
        """Load a TGA level.

        Arguments:
            g        -- a Tilevid instance
            fname    -- tga image to load
            bg        -- set to 1 if you wish to load the background layer

        """
        if type(fname) == str: img = pygame.image.load(fname)
        else: img = fname
        w, h = img.get_width(), img.get_height()
        self.resize((w, h), bg)
        for y in range(0, h):
            for x in range(0, w):
                t, b, c, _a = img.get_at((x, y))
                self.tlayer[y][x] = t
                if bg: self.blayer[y][x] = b
                self.clayer[y][x] = c

    def tga_save_level(self, fname):
        """Save a TGA level.

        Arguments:
            fname -- tga image to save to

        """
        w, h = self.size
        img = pygame.Surface((w, h), SWSURFACE, 32)
        img.fill((0, 0, 0, 0))
        for y in range(0, h):
            for x in range(0, w):
                t = self.tlayer[y][x]
                b = 0
                if self.blayer:
                    b = self.blayer[y][x]
                c = self.clayer[y][x]
                _a = 0
                img.set_at((x, y), (t, b, c, _a))
        pygame.image.save(img, fname)

    def tga_load_tiles(self, fname, size, tdata={}):
        """Load a TGA tileset.

        Arguments:
            g       -- a Tilevid instance
            fname    -- tga image to load
            size    -- (w, h) size of tiles in pixels
            tdata    -- tile data, a dict of tile:(agroups, hit handler, config)

        """
        TW, TH = size
        if type(fname) == str: img = pygame.image.load(fname).convert_alpha()
        else: img = fname
        w, h = img.get_width(), img.get_height()

        n = 0
        for y in range(0, h, TH):
            for x in range(0, w, TW):
                i = img.subsurface((x, y, TW, TH))
                tile = Tile(i)
                self.tiles[n] = tile
                if n in tdata:
                    agroups, hit, config = tdata[n]
                    tile.agroups = self.string2groups(agroups)
                    tile.hit = hit
                    tile.config = config
                n += 1

    def load_images(self, idata):
        """Load images.

        Arguments:
            idata -- a list of (name, fname, shape)

        """
        for name, fname, shape in idata:
            self.images[name] = pygame.image.load(fname).convert_alpha(), shape

    def run_codes(self, cdata, rect):
        """Run codes.

        Arguments:
            cdata -- a dict of code:(handler function, value)
            rect -- a tile rect of the parts of the layer that should have
                 their codes run

        """
        tw, th = self.tiles[0].image.get_width(), self.tiles[0].image.get_height()

        x1, y1, w, h = rect
        clayer = self.clayer
        t = Tile()
        for y in range(y1, y1+h):
            for x in range(x1, x1+w):
                n = clayer[y][x]
                if n in cdata:
                    fnc, value = cdata[n]
                    t.tx, t.ty = x, y
                    t.rect = pygame.Rect(x*tw, y*th, tw, th)
                    fnc(self, t, value)

    def string2groups(self, str):
        """Convert a string to groups."""
        if str == None: return 0
        return self.list2groups(str.split(", "))

    def list2groups(self, igroups):
        """Convert a list to groups."""
        for s in igroups:
            if not s in self.groups:
                self.groups[s] = 2**len(self.groups)
        v = 0
        for s, n in self.groups.items():
            if s in igroups: v|=n
        return v

    def groups2list(self, groups):
        """Convert a groups to a list."""
        v = []
        for s, n in self.groups.items():
            if (n&groups)!=0: v.append(s)
        return v

    def hit(self, x, y, t, s):
        tiles = self.tiles
        tw, th = tiles[0].image.get_width(), tiles[0].image.get_height()
        t.tx = x
        t.ty = y
        t.rect = Rect(x*tw, y*th, tw, th)
        t._rect = t.rect
        if hasattr(t, 'hit'):
            t.hit(self, t, s)

    def loop(self):
        """Update and hit testing loop.  Run this once per frame."""
        self.loop_sprites() #sprites may move
        self.loop_tilehits() #sprites move
        self.loop_spritehits() #no sprites should move
        for s in self.sprites:
            s._rect = pygame.Rect(s.rect)

    def loop_sprites(self):
        as_ = self.sprites[:]
        for s in as_:
            if hasattr(s, 'loop'):
                s.loop(self, s)

    def loop_tilehits(self):
        tiles = self.tiles
        tw, th = tiles[0].image.get_width(), tiles[0].image.get_height()

        layer = self.layers[0]

        as_ = self.sprites[:]
        for s in as_:
            self._tilehits(s)

    def _tilehits(self, s):
        tiles = self.tiles
        tw, th = tiles[0].image.get_width(), tiles[0].image.get_height()
        layer = self.layers[0]

        for _z in (0, ):
            if s.groups != 0:

                _rect = s._rect
                rect = s.rect

                _rectx = _rect.x
                _recty = _rect.y
                _rectw = _rect.w
                _recth = _rect.h

                rectx = rect.x
                recty = rect.y
                rectw = rect.w
                recth = rect.h

                rect.y = _rect.y
                rect.h = _rect.h

                hits = []
                ct, cb, cl, cr = rect.top, rect.bottom, rect.left, rect.right
                #nasty ol loops
                y = ct/th*th
                while y < cb:
                    x = cl/tw*tw
                    yy = y/th
                    while x < cr:
                        xx = x/tw
                        t = tiles[layer[yy][xx]]
                        if (s.groups & t.agroups)!=0:
                            #self.hit(xx, yy, t, s)
                            d = math.hypot(rect.centerx-(xx*tw+tw/2),
                                rect.centery-(yy*th+th/2))
                            hits.append((d, t, xx, yy))

                        x += tw
                    y += th

                hits.sort()
                #if len(hits) > 0: print self.frame, hits
                for d, t, xx, yy in hits:
                    self.hit(xx, yy, t, s)

                #switching directions...
                _rect.x = rect.x
                _rect.w = rect.w
                rect.y = recty
                rect.h = recth

                hits = []
                ct, cb, cl, cr = rect.top, rect.bottom, rect.left, rect.right
                #nasty ol loops
                y = ct/th*th
                while y < cb:
                    x = cl/tw*tw
                    yy = y/th
                    while x < cr:
                        xx = x/tw
                        t = tiles[layer[yy][xx]]
                        if (s.groups & t.agroups)!=0:
                            d = math.hypot(rect.centerx-(xx*tw+tw/2),
                                rect.centery-(yy*th+th/2))
                            hits.append((d, t, xx, yy))
                            #self.hit(xx, yy, t, s)
                        x += tw
                    y += th

                hits.sort()
                #if len(hits) > 0: print self.frame, hits
                for d, t, xx, yy in hits:
                    self.hit(xx, yy, t, s)

                #done with loops
                _rect.x = _rectx
                _rect.y = _recty

    def loop_spritehits(self):
        as_ = self.sprites[:]

        groups = {}
        for n in range(0, 31):
            groups[1<<n] = []
        for s in as_:
            g = s.groups
            n = 1
            while g:
                if (g&1)!=0: groups[n].append(s)
                g >>= 1
                n <<= 1

        for s in as_:
            if s.agroups!=0:
                rect1, rect2 = s.rect, Rect(s.rect)
                #if rect1.centerx < 320: rect2.x += 640
                #else: rect2.x -= 640
                g = s.agroups
                n = 1
                while g:
                    if (g&1)!=0:
                        for b in groups[n]:
                            if (s != b and (s.agroups & b.groups)!=0
                                    and s.rect.colliderect(b.rect)):
                                s.hit(self, s, b)

                    g >>= 1
                    n <<= 1

    def screen_to_tile(self, pos):
        """Convert a screen position to a tile position."""
        return pos

    def tile_to_screen(self, pos):
        """Convert a tile position to a screen position."""
        return pos


class TileBasedVidMixin(object):
    def set_bounds(self):
        if self.bounds is not None:
            self.view.clamp_ip(self.bounds)

    def blit_tiles(self, screen, to_update):
        tile_h = self.tiles[0].tile_h
        tile_w = self.tiles[0].tile_w
        yy = - (self.view.y % tile_h)
        xx = - (self.view.x % tile_w)
        us = []
        for (x, y) in to_update:
            if self.blayer is not None:
                screen.blit(self.tiles[self.blayer[y][x]].image,(xx,yy))
            screen.blit(self.tiles[self.tlayer[y][x]].image,(xx,yy))
            us.append(Rect(xx, yy, tile_w, tile_h))
        return us

    def _get_sprite_removal_list(self, rect):
        y_bottom = max(0, rect.y / self.tile_h)
        y_top = min(self.size[1], rect.bottom / self.tile_h + 1)
        x_bottom = max(0, rect.x / self.tile_h)
        x_top = min(self.size[1], rect.top / self.tile_w + 1)
        to_check = [[(x,y) for y in xrange(y_bottom, y_top)]
                    for x in xrange(x_bottom, x_top)]

    def remove_sprites(self, screen):
        old_sprites_removed = self.sprites.removed[:]
        self.sprites.removed = []
        old_sprites_removed.extend(self.sprites[:])

        for sprite in old_sprites_removed:
            sprite.irect.x = sprite.rect.x-sprite.shape.x
            sprite.irect.y = sprite.rect.y-sprite.shape.y
            if (s.irect.x != s._irect.x or s.irect.y != s._irect.y
                     or s.image != s._image):
                 #w,h can be skipped, image covers that...
                 sprite.updated = True

                 # From old position
                 to_check = self._get_sprite_removal_list(sprite._irect)
                 for x, y in to_check:
                     if not self.alayer[y][x]:
                         self.updates.extend((x,y))
                     self.alayer[y][x] = 1

                 # from new position
                 to_check = self._get_sprite_removal_list(sprite.irect)
                 for x, y in to_check:
                     if not self.alayer[y][x]:
                         self.alayer[y][x] = 2
                         self.updates.extend((x,y))

        #mark sprites that are not being updated that need to be updated because
        #they are being overwritte by sprites / tiles
        for sprite in self.sprites:
            if not sprite.updated:
                 to_check = self._get_sprite_removal_list(sprite.irect)
                 for x, y in to_check:
                     if self.alayer[x][y] == 1:
                         sprite.updated = True

    def blit_sprites(self, screen):
        us = []
        for x, y in self.updates:
            xx = x * self.tile_w - self.view.x
            yy = y * self.tile_h - self.view.y
            if self.alayer[y][x] == 1:
                if self.blayer is not None:
                    screen.blit(self.tiles[self.blayer[y][x]].image,(xx,yy))
                screen.blit(self.tiles[self.tlayer[y][x]].image,(xx,yy))
            self.alayer[y][x]=0
            us.append(Rect(xx, yy, self.tile_w, self.tile_h))

        for sprite in self.sprites:
            if sprite.updated:
                screen.blit(sprite.image, (sprite.irect.x - self.view.x,
                            sprite.irect.y - self.view.y))
                sprite.updated=0
                sprite._irect = Rect(sprite.irect)
                sprite._image = sprite.image

        return us  # bit inconsistant with the prior

    def update(self, screen):
        """Update the screen.

        Arguments:
            screen -- a pygame.Rect to update

        Returns a list of updated rectangles.

        """
        sw,sh = screen.get_width(), screen.get_height()
        self.view.w, self.view.h = sw,sh

        self.set_bounds()
        tile_h = self.tiles[0].tile_h
        tile_w = self.tiles[0].tile_w
        my = self.view.bottom - self.view.top / tile_h
#        if (self.view.bottom - self.view.top) % tile_h:
#            my += 1
        mx = (self.view.right - self.view.left) / tile_w

        to_update = [ (x, y) for x in xrange(max( 0, self.view.x / tile_w), min(mx, self.size[0]))
                        for y in xrange(max(0, self.view.y / tile_h), min(my, self.size[1])) ]

        self.remove_sprites(screen)  # set the sprites to be removed

        us = self.paint(screen, to_update)

        return [ Rect(u[0] * tile_w - self.view.x,
                      u[1] * tile_h - self.view.y,
                      tile_w,
                      tile_h,) for u in self.updates]



    def paint(self, screen, to_update=None):
        if to_update is None:
            return self.update(screen)
        us = self.blit_tiles(screen, to_update)

        us.extend(self.blit_sprites(screen))

        return us



class IsoHexVidMixin(TileBasedVidMixin):
    def set_bounds(self):
        w, h = self.size
        if self.bounds != None:
            self.view.clamp_ip(self.bounds)
        else:
            tmp, y1 = self.tile_to_view((0, 0))
            x1, tmp = self.tile_to_view((0, h+1))
            tmp, y2 = self.tile_to_view((w+1, h+1))
            x2, tmp = self.tile_to_view((w+1, 0))
            self.bounds = pygame.Rect(x1, y1, x2-x1, y2-y1)
            print self.bounds
