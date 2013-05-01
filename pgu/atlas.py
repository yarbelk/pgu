# encoding: utf-8

import pygame
import yaml
import tarfile


"""
Atlas yaml format

sheets:
    - image: sheet1.png
      name: characters
      sprites:
        - name: hero
          pos: [0, 0, 16, 16]
        - name: villian
          pos: [0, 16, 16, 16]
      masks:
        - name: hero
          pos: [0, 0, 16, 16]
        - name: villian
          pos: [0, 16, 16, 16]

"""


class Atlas(object):
    def __init__(self, atlas_file):
        _atlas = {}
        with tarfile.open(atlas_file, 'r:*') as atlas:
            atlas_data = yaml.safe_dump(atlas.extractfile('atlas.yaml'))
            for sheet in atlas_data:
                

