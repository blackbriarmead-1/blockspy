import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
import numpy as np
import time
import sqlite3
import gzip

import requests

from . import Tile
from . import Diff

if __name__ == '__main__':
    print("hello from util")


#Get connection to database and create neccessary tables
def initializeDB(dbname):
    connection = sqlite3.connect("{}.db".format(dbname))
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tile_images (x INTEGER, y INTEGER, zoom INTEGER, tile_image BLOB, image_hash STRING, latest_hash STRING, PRIMARY KEY (x,y,zoom))")
    cursor.execute("CREATE TABLE IF NOT EXISTS diffs (x INTEGER, y INTEGER, zoom INTEGER, packed_diffs BLOB, map_refresh_timestamp INTEGER, previous_refresh_timestamp INTEGER, tile_refresh_index INTEGER, previous_refresh_index INTEGER, image_hash STRING, PRIMARY KEY (x,y,zoom,tile_refresh_index,previous_refresh_index))")
    cursor.execute("CREATE TABLE IF NOT EXISTS map_refresh (refresh_time INTEGER, PRIMARY KEY (refresh_time))")
    connection.commit()
    return(connection)

def imageToBytes(image):
    byteIO = BytesIO()
    image.save(byteIO, format='PNG')
    return(byteIO.getvalue())

def getMSB(n):
    n |= n>>1
    n |= n>>2  
    n |= n>>4 
    n |= n>>8
    n |= n>>16
    n = n + 1
  
    # Return original MSB after shifting.
    # n now becomes 100000000
    return (n >> 1)

#this function returns the diffs that need to be generated based on the new index
def getDiffsToGenerate(new_index):
    output = []
    n = 1
    while(n <= new_index):
        if(new_index % n == 0):
            output.append(new_index - n)
        n *= 2
    return(output)

#returns a list of tuples. Each tuple is a pair of indexes where a diff should be traversed.
def getDiffsToTraverse(index):
    tempindex = index
    previndex = 0
    output = []
    while(tempindex > 0):
        msb = getMSB(tempindex)
        target = previndex + msb
        output.append((previndex, target))
        previndex = target
        tempindex -= msb
    return(output)

#Gets the highest current refresh index from the diffs table
def getHighestRefreshIndex(x,y,zoom,connection):
    cursor = connection.cursor()
    statement = """SELECT tile_refresh_index FROM diffs WHERE x = ? AND y = ? and zoom = ? ORDER BY tile_refresh_index DESC LIMIT 1"""
    data_tuple = (x,y,zoom)#the second tile.hash is for the latest hash (derived image from latest diff)
    res = cursor.execute(statement, data_tuple)
    result = res.fetchone()
    if(result == None):
        return(0)#if no index exists, that means it is 0
    else:
        #print(result)
        return(result[0])

#insert a png - to be used if there is no png for that tile
def insertTile(tile,connection):
    cursor = connection.cursor()
    statement = """INSERT INTO tile_images (x, y, zoom, tile_image, image_hash, latest_hash) VALUES (?, ?, ?, ?, ?, ?)"""
    data_tuple = (tile.x,tile.y,tile.zoom,imageToBytes(tile.image), tile.hash, tile.hash)#the second tile.hash is for the latest hash (derived image from latest diff)
    res = cursor.execute(statement, data_tuple)
    #print(res.fetchone())
    connection.commit()

#get the original tile png
def getTile(x,y,zoom,connection):
    cursor = connection.cursor()
    statement = """SELECT tile_image, image_hash, latest_hash FROM tile_images WHERE x = ? AND y = ? AND zoom = ? LIMIT 1"""
    data_tuple = (x,y,zoom)
    cursor.execute(statement,data_tuple)
    result = cursor.fetchone()
    if(result is None):
        return(None)
    else:
        return(Tile.Tile(Image.open(BytesIO(result[0])), x, y, zoom, hash = result[1], latest_hash=result[2]))

#gets the desired diff by x, y, zoom, as well as start and stop indices
def getDiffByIndex(x, y, zoom, start_index, stop_index, connection):
    cursor = connection.cursor()
    statement = """SELECT packed_diffs FROM diffs WHERE x = ? AND y = ? AND zoom = ? AND tile_refresh_index = ? AND previous_refresh_index = ?"""
    data_tuple = (x,y,zoom,stop_index,start_index)
    cursor.execute(statement,data_tuple)
    result = cursor.fetchone()
    if(result is None):
        return(None)
    else:
        #print(result)
        #print(result[0])
        return(Diff.Diff(packed = result[0]))

#apply a diff to an image and return the new image
def applydiff(diff,image):
    array = np.array(image)
    for x,y,r,g,b,a in diff.diffarray:
        array[y][x] = (r,g,b,a)
    return(Image.fromarray(array))


def getImageFromDiffIndex(x,y,zoom,index,connection):
    #get index of diffs to traverse
    toTraverse = getDiffsToTraverse(index)

    #get original png
    originalTile = getTile(x,y,zoom,connection)
    newimage = originalTile.image
    print("toTraverse:",toTraverse)
    for start,stop in toTraverse:
        print("applying diff to image: {} to {}.".format(start,stop))
        diff = getDiffByIndex(x, y, zoom, start, stop, connection)
        #diffimg = diff.getDiffImage(newimage.size[0],newimage.size[1])
        #diffimg.show()
        #print(diff.diffarray)
        #for item in diff.diffarray:
            #print(item)
        #apply this diff to the original png
        newimage = applydiff(diff,newimage)
    return(newimage)

def getLatestImage(x,y,zoom,connection):
    highestIndex = getHighestRefreshIndex(x,y,zoom,connection)
    return(getImageFromDiffIndex(x,y,zoom,highestIndex,connection))

def generateDiffNew(previous_image,current_image):
    #print("generating diff")
    width, height = previous_image.size
    array1 = np.array(previous_image)
    array2 = np.array(current_image)
    #print("array1",array1)
    #print("array2",array2)
    #print("are arrays the same? ",np.array_equal(array1,array2))
    output = Diff.Diff()
    # Use vectorized operations to find the pixels that changed
    diff = array1 != array2 # Get a boolean array that indicates which pixels are different
    #print("nonzero: ",diff.nonzero())
    y, x, _ = diff.nonzero() # Get the indices of the non-zero elements (y, x coordinates of changed pixels)
    rgba = array2[y, x] # Get the RGBA values of those pixels from the second array
    # Loop over the changed pixels and add them to the output
    for i in range(len(y)):
        r, g, b, a = rgba[i]
        output.addDiff(x[i], y[i], r, g, b, a)
        #print("x: {}, y: {} image not the same. new color: {}".format(x[i],y[i],(r,g,b,a)))
    return(output)

def generateDiff(previous_image,current_image):
    #print("generating diff")
    width, height = previous_image.size
    array1 = np.array(previous_image)
    array2 = np.array(current_image)
    #print("array1",array1)
    #print("array2",array2)
    #print("are arrays the same? ",np.array_equal(array1,array2))
    output = Diff.Diff()
    i = 0
    for y in range(height):
        for x in range(width):
            #print("{}".format((x,y,array1[y][x],array2[y][x])))
            if(not (array1[y][x] == array2[y][x]).all()):
                r,g,b,a = array2[y][x]
                output.addDiff(x,y,r,g,b,a)
                #print("x: {}, y: {} image not the same. new color: {}".format(x,y,(r,g,b,a)))
            i += 1
    return(output)

#updates the latest_hash field of a tile to reflect 
def updateTileHash(tile, new_hash, connection):
    cursor = connection.cursor()

    statement = """UPDATE tile_images SET latest_hash = ? WHERE x = ? AND y = ? AND zoom = ?"""

    data_tuple = (new_hash, tile.x, tile.y, tile.zoom)
    res = cursor.execute(statement,data_tuple)
    return(res)

#adds a diff along with its associated data into the DB
def addDiffToDB(x,y,zoom,diff,start_index,stop_index, connection, map_refresh_timestamp = None, previous_refresh_timestamp = None):
    cursor = connection.cursor()
    statement = """"""
    data_tuple = ()
    packed_diffs = diff.getPackedRepresentation()
    if(not map_refresh_timestamp == None and not previous_refresh_timestamp == None):
        statement = """INSERT INTO diffs (x, y, zoom, packed_diffs, tile_refresh_index, previous_refresh_index, map_refresh_timestamp, previous_refresh_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        data_tuple = (x,y,zoom,packed_diffs,stop_index,start_index, map_refresh_timestamp, previous_refresh_timestamp)
    elif(not map_refresh_timestamp == None and previous_refresh_timestamp == None):
        statement = """INSERT INTO diffs (x, y, zoom, packed_diffs, tile_refresh_index, previous_refresh_index, map_refresh_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)"""
        data_tuple = (x,y,zoom,packed_diffs,stop_index,start_index, map_refresh_timestamp)
    elif(map_refresh_timestamp == None and not previous_refresh_timestamp == None):
        statement = """INSERT INTO diffs (x, y, zoom, packed_diffs, tile_refresh_index, previous_refresh_index, previous_refresh_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)"""
        data_tuple = (x,y,zoom,packed_diffs,stop_index,start_index, previous_refresh_timestamp)
    else:
        statement = """INSERT INTO diffs (x, y, zoom, packed_diffs, tile_refresh_index, previous_refresh_index) VALUES (?, ?, ?, ?, ?, ?)"""
        data_tuple = (x,y,zoom,packed_diffs,stop_index,start_index)
    res = cursor.execute(statement, data_tuple)
    print("add diff to db response:",res)
    connection.commit()
    return(res)

#this function updates a tile. It will create a new tile if one does not already exist
#if one does exist, it will compare hashes. If hash is same, create diffs. Else, do nothing    
def updateTile(new_tile, timestamp, connection):
    cursor = connection.cursor()
    db_tile = getTile(new_tile.x,new_tile.y,new_tile.zoom,connection)
    if(db_tile == None):
        #insertTile should only be used for the very first scan
        print("tile does not exist - inserting tile into database")
        insertTile(new_tile,connection)
    else:
        print("old hash:",db_tile.latest_hash)
        print("new hash:",new_tile.hash)
        if(db_tile.latest_hash == new_tile.hash):
            print("hash has not changed - do nothing")
            pass
        else:
            print("hash has changed - do the fancy stuff")

            #db_tile.image.show()
            #new_tile.image.show()


            #find current highest refresh index in the diffs table
            highest_index = getHighestRefreshIndex(new_tile.x, new_tile.y, new_tile.zoom, connection)

            #new index is this plus one
            new_index = highest_index + 1
            print("new index:",new_index)

            #get list of diffs that need to be generated
            diffs_to_generate = getDiffsToGenerate(new_index)
            print("diffs to generate:",diffs_to_generate)
            for index in diffs_to_generate:
                #get Image generated from old diff
                old_image = getImageFromDiffIndex(new_tile.x,new_tile.y,new_tile.zoom,index,connection)

                #generate a diff from index to new_index
                new_diff = generateDiffNew(old_image,new_tile.image)
                #print("new diff array",new_diff.diffarray)
                #write this diff to the database with the required extra info
                addDiffToDB(new_tile.x,new_tile.y,new_tile.zoom,new_diff,index,new_index,connection,map_refresh_timestamp=timestamp)

            updateTileHash(new_tile, new_tile.hash, connection)#after generating diffs, update latest tile hash for next comparison.

# define a function to get a single tile from the castia server
def getRemoteTile(x, y, zoom):
    # construct the URL for the tile
    url = f"https://map.castiamc.com/tiles/minecraft_overworld/{zoom}/{x}_{y}.png"
    # make a GET request to the URL
    response = requests.get(url)
    # check if the response is OK
    if response.status_code == 200:
        # open the image from the response content
        img = Image.open(BytesIO(response.content))
        # return the image and other information about the tile
        return Tile.Tile(img, x, y, zoom)
    else:
        # handle the error
        print(f"Error: status code not 200 ({response.status_code})")
        return None

#calls map.castiamc.com and retrieves desired tile by modifying params
#takes a semaphore for concurrency
async def getRemoteTileAsync(x,y,zoom, session, sem):
    async with sem:
        for i in range(3):
            try:
                async with session.get("https://map.castiamc.com/tiles/minecraft_overworld/{}/{}_{}.png".format(zoom,x,y)) as response:
                    if response.status == 200:
                        img = Image.open(BytesIO(await response.read()))
                        #print(img.size)
                        #return other information about tile to allow for easier tracking
                        return Tile.Tile(img,x,y,zoom)
                    else:
                        print("error: status code not 200")
                        #print(response.status)
            except Exception as e:
                print(e)
                await asyncio.sleep(1)
        return None

#get many images defined by two points and a zoom level
async def getImagesAsync(x1,y1,x2,y2,zoom):
    sem = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for x in range(x1,x2+1):
            for y in range(y1,y2+1):
                tasks.append(getRemoteTileAsync(x,y,zoom, session, sem))
        return await asyncio.gather(*tasks)
    
def getRemoteTiles(x1,y1,x2,y2,zoom):
    return(asyncio.run(getImagesAsync(x1,y1,x2,y2,zoom)))

#combine images into a single image. Returns a PIL Image object
def combine_images(images, l, h):
    tilewidth = images[0].size[0]
    tileheight = images[0].size[1]

    total_width = (h-l+1)*tilewidth
    total_height = (h-l+1)*tileheight

    combined_array = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    for i, img in enumerate(images):
        if img is not None:
            x = i // (h-l+1)
            y = i % (h-l+1)
            img = img.convert('RGB')
            combined_array[x*tileheight:(x+1)*tileheight, y*tilewidth:(y+1)*tilewidth] = np.array(img)

    combined_image = Image.fromarray(combined_array)
    return(combined_image)

#combine images into a single image. Returns a PIL Image object
def combine_tiles(tiles, l, h):
    tilewidth = tiles[0].image.size[0]
    tileheight = tiles[0].image.size[1]

    total_width = (h-l+1)*tilewidth
    total_height = (h-l+1)*tileheight
    print("total_width:",total_width)

    combined_array = np.zeros((total_height, total_width, 4), dtype=np.uint8)
    for i, tile in enumerate(tiles):
        if tile is not None:
            x = tile.x-l
            y = tile.y-l
            #print("x",x)
            #print("y",y)
            img = tile.image.convert('RGBA')
            combined_array[y*tileheight:(y+1)*tileheight, x*tilewidth:(x+1)*tilewidth] = np.array(img)

    combined_image = Image.fromarray(combined_array)
    return(combined_image)