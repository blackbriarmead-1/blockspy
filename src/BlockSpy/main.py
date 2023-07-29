import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
import numpy as np
import time
import sqlite3

from . import Tile
from . import Diff

#Get connection to database and create neccessary tables
def initializeDB():
    connection = sqlite3.connect("blockspy.db")
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tile_images (x INTEGER, y INTEGER, zoom INTEGER, tile_image BLOB, image_hash STRING, UNIQUE(x,y,zoom))")
    connection.commit()
    return(connection)

def imageToBytes(image):
    byteIO = BytesIO()
    image.save(byteIO, format='PNG')
    return(byteIO.getvalue())

def insertTile(tile,connection):
    cursor = connection.cursor()
    statement = """ INSERT INTO tile_images (x, y, zoom, tile_image, image_hash) VALUES (?, ?, ?, ?, ?)"""
    data_tuple = (tile.x,tile.y,tile.zoom,imageToBytes(tile.image), tile.hash)
    res = cursor.execute(statement, data_tuple)
    print(res.fetchone())
    connection.commit()

def getTile(x,y,zoom,connection):
    cursor = connection.cursor()
    statement = """SELECT tile_image, image_hash FROM tile_images WHERE x = ? AND y = ? AND zoom = ? LIMIT 1"""
    data_tuple = (x,y,zoom)
    cursor.execute(statement,data_tuple)
    result = cursor.fetchone()
    if(result is None):
        return(None)
    else:
        return(Tile.Tile(Image.open(BytesIO(result[0])), x, y, zoom, result[1]))

def generateDiff(previous_image: Image.Image,current_image: Image.Image):
    width, height = previous_image.size
    array1 = np.array(previous_image)
    array2 = np.array(current_image)
    print(array1)
    print(array2)
    output = Diff.Diff()
    i = 0
    for y in range(height):
        for x in range(width):
            if(array1[y][x].all() !=array2[y][x].all()):
                r,g,b,a = array2[y][x]
                output.addDiff(x,y,r,g,b,a)
            i += 1
    return(output)

#this function updates a tile. It will create a new tile if one does not already exist
#if one does exist, it will compare hashes. If hash is same, create diffs. Else, do nothing    
def updateTile(new_tile, connection):
    cursor = connection.cursor()
    db_tile = getTile(new_tile.x,new_tile.y,new_tile.zoom,connection)
    if(db_tile == None):
        #insertTile should only be used for the very first scan
        print("tile does not exist - inserting tile into database")
        insertTile(new_tile,connection)
    else:
        if(db_tile.hash == new_tile.hash):
            print("hash has not changed - do nothing")
            pass
        else:
            print("hash has changed - do the fancy stuff")
            print(generateDiff(db_tile.image,new_tile.image))

#calls map.castiamc.com and retrieves desired tile by modifying params
#takes a semaphore for concurrency
async def getTileFromCoordinates(x,y,zoom, session, sem):
    async with sem:
        for i in range(3):
            try:
                async with session.get("https://map.castiamc.com/tiles/minecraft_overworld/{}/{}_{}.png".format(zoom,y,x)) as response:
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
    sem = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for x in range(x1,x2+1):
            for y in range(y1,y2+1):
                tasks.append(getTileFromCoordinates(x,y,zoom, session, sem))
        return await asyncio.gather(*tasks)
    
def getTiles(x1,y1,x2,y2,zoom):
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