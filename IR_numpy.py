import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
import numpy as np
import time

async def getImageFromCoordinates(x,y,zoom, session, sem):
    async with sem:
        for i in range(3):
            try:
                async with session.get("https://map.castiamc.com/tiles/minecraft_overworld/{}/{}_{}.png".format(zoom,y,x)) as response:
                    if response.status == 200:
                        img = Image.open(BytesIO(await response.read()))
                        #print(img.size)
                        return img
                    else:
                        print("error: status code not 200")
                        #print(response.status)
            except Exception as e:
                print(e)
                await asyncio.sleep(1)
        return None

async def getImages(l, h, zoom):
    sem = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for x in range(l,h+1):
            for y in range(l,h+1):
                tasks.append(getImageFromCoordinates(x,y,zoom, session, sem))
        return await asyncio.gather(*tasks)
    
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
    combined_image.save("fullmap-7-27.png")

#accquire array of all images
l = -25
h = 24
start_time = time.time()
images = asyncio.run(getImages(l, h, 5))
end_time = time.time()
download_time = end_time - start_time
print(f"Downloaded {len(images)} tiles in {download_time:.2f} seconds ({len(images)/download_time:.2f} tiles/second)")

start_time = time.time()
combine_images(images, l, h)
end_time = time.time()
combine_time = end_time - start_time
print(f"Combined {len(images)} images in {combine_time:.2f} seconds ({len(images)/combine_time:.2f} images/second)")

'''

tilewidth = images[0].size[0]
tileheight = images[0].size[1]

total_width = (h-l+1)*tilewidth
print("total_width:", total_width)

total_height = (h-l+1)*tileheight
print("total_height:", total_height)

combinedImage = Image.new('RGB', (total_width,total_height))
for i, img in enumerate(images):
    if img is not None:
        x = i // (h-l+1)
        y = i % (h-l+1)
        combinedImage.paste(img,(y*tilewidth,x*tileheight))

combinedImage.save("quartermap.png")'''