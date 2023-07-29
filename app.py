import src.BlockSpy.Tile as Tile
import src.BlockSpy.main as Main
import src.BlockSpy.Diff as Diff
import sqlite3
from PIL import Image, ImageFilter
import io
import sys

connection = Main.initializeDB()

tiles = Main.getTiles(-25,-25,-24,-24,5)
for index, tile in enumerate(tiles):
    tile.updateImage(tile.image.filter(ImageFilter.CONTOUR))
    Main.updateTile(tile,connection)