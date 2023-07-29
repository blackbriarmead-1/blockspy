import src.BlockSpy.Tile as Tile
import src.BlockSpy.main as Main
import src.BlockSpy.Diff as Diff
import sqlite3
from PIL import Image, ImageFilter
import io
import sys
import time
import gzip
import random

connection = Main.initializeDB()

#tiles = Main.getTiles(-25,-25,-24,-24,5)
#for index, tile in enumerate(tiles):
#    tile.updateImage(tile.image.filter(ImageFilter.CONTOUR))
#    Main.updateTile(tile,connection)

'''start = time.time()
for y in range(-25,25):
    for x in range(-25,25):
        tile = Main.getTile(x,y,5,connection)
        print(tile)
total = time.time()-start

print("time elapsed to query all 2500 tiles from database: {}".format(total))'''

changes = Diff.Diff()
for y in range(512):
    for x in range(512):
        changes.addDiff(x,y,1,2,3,4)

changesPacked = changes.getPackedRepresentation()
with gzip.open("diff_compressed.gz","wb") as f:
    f.write(changesPacked)

with open("diff_uncompressed.diff","wb") as f:
    f.write(changesPacked)


with open("diff_compressed.gz","rb") as f:
    raw = gzip.decompress(f.read())
    decodedChanges = Diff.Diff(packed = raw)
    print(changes)
    print(decodedChanges)
    print(changes.diffarray == decodedChanges.diffarray)#check that the data is the same after decoding
