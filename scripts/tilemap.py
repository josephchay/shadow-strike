import json

import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTO_TILES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        """
        The id_pairs is a list of id_pair, each id_pair is a tuple of (type, variant).
        The keep parameter determines whether the extracted tiles should be removed from the tilemap.
        """
        matches = []

        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())

                if not keep:
                    self.offgrid_tiles.remove(tile)

        for location in self.tilemap:
            tile = self.tilemap[location]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size

                if not keep:
                    del self.tilemap[location]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_location = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))

        for offset in NEIGHBOR_OFFSETS:
            check_location = str(tile_location[0] + offset[0]) + ';' + str(tile_location[1] + offset[1])
            if check_location in self.tilemap:
                tiles.append(self.tilemap[check_location])

        return tiles

    def solid_check(self, pos):
        """
        Checks if the tile at the given position is solid.
        :param pos: the position to check
        :return: the tile at the given position if it is solid, otherwise None
        """
        tile_location = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_location in self.tilemap:
            if self.tilemap[tile_location]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_location]

    def physics_rects_around(self, pos):
        rects = []

        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))

        return rects

    def autotile(self):
        for location in self.tilemap:
            tile = self.tilemap[location]
            neighbors = set()

            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_location = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_location in self.tilemap:

                    # ensure that the neighbor tile is of the same type as the current tile
                    if self.tilemap[check_location]['type'] == tile['type']:
                        neighbors.add(shift)

            neighbors = tuple(sorted(neighbors))

            if (tile['type'] in AUTO_TILES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def render(self, surface, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surface.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(offset[0] // self.tile_size, (offset[0] + surface.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surface.get_height()) // self.tile_size + 1):
                location = str(x) + ';' + str(y)
                if location in self.tilemap:
                    tile = self.tilemap[location]
                    surface.blit(self.game.assets[tile['type']][tile['variant']], (x * self.tile_size - offset[0], y * self.tile_size - offset[1]))
