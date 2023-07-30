import src.BlockSpy.Tile as Tile
import src.BlockSpy.util as util
import src.BlockSpy.Diff as Diff
import sqlite3
from PIL import Image, ImageFilter
import io
import sys
import time
from datetime import datetime
import gzip
import random

connection = util.initializeDB("switchedtest")

ms = datetime.now()
unix_timestamp = round(time.mktime(datetime.now().timetuple()) * 1000)
print(unix_timestamp)
if(True):
    tiles = util.getRemoteTiles(-25,-25,24,24,5)
    print("tiles have been retrieved")
    
    
    for index, tile in enumerate(tiles):
        '''highestDiffIndex = util.getHighestRefreshIndex(tile.x,tile.y,tile.zoom,connection)
        old_tile = Tile.Tile(util.getImageFromDiffIndex(tile.x,tile.y,tile.zoom,highestDiffIndex,connection),tile.x,tile.y,tile.zoom)
        print("old hash", old_tile.hash)
        print("new hash", tile.hash)
        if(old_tile.hash != tile.hash):
            #old_tile.image.show()
            #tile.image.show()
            diff = util.generateDiff(old_tile.image,tile.image)
            print("generated diff",diff.diffarray)'''
        
        print("updating tile:",index)
        #tile.updateImage(tile.image.filter(ImageFilter.CONTOUR))
        util.updateTile(tile,unix_timestamp,connection)
        #highestDiffIndex = Main.getHighestRefreshIndex(tile.x,tile.y,tile.zoom,connection)
        #image = Main.getImageFromDiffIndex(tile.x,tile.y,tile.zoom,highestDiffIndex,connection)
        #image.show()

'''
highestDiffIndex = util.getHighestRefreshIndex(0,0,5,connection)
for i in range(highestDiffIndex):
    print(i)
    image = util.getImageFromDiffIndex(0,0,5,i,connection)
    image.show()'''

#image = util.getImageFromDiffIndex(0,0,5,index,connection)
#image.show()

def outputimage(l,h,file_name, latest = True):
    all_tiles = []
    for y in range(l,h+1):
        for x in range(l,h+1):
            highest = 0
            if(latest):
                highest = util.getHighestRefreshIndex(x,y,5,connection)
            image = util.getImageFromDiffIndex(x,y,5,highest,connection)
            new_tile = Tile.Tile(image,x,y,5)
            all_tiles.append(new_tile)

    combined = util.combine_tiles(all_tiles,l,h)
    with open(file_name,"wb") as f:
        byteIO = io.BytesIO()
        combined.save(byteIO, format='PNG')
        f.write(byteIO.getvalue())
    #combined.show()

#outputimage(-25,24,"aaaoriginal.png",latest=False)
outputimage(-25,24,"aaanew3.png",latest=True)
