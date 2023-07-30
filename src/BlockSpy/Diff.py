from io import BytesIO
import struct
from PIL import Image
import sys
sys.path.append("..")
import numpy as np

class Diff:
    def __init__(self, packed = None):
        self.diffarray = []

        if not packed == None:
            #print("packed is not none - getting upacked representation")
            self.diffarray = self.getUnpackedRepresentation(packed)
            #print(self.diffarray)
        else:
            pass
            #print("no packed diff, initializing with empty array")

    def __str__(self):
        return("Diff Object. \nnumber of differences: {}".format(len(self.diffarray)))

    def getDiffImage(self,x,y):
        #print("x",x)
        #print("y",y)
        image = Image.new(mode="RGBA", size=(x,y),color=(0,0,0,0))
        return(self.applydiff(image))
        
    #apply a diff to an image and return the new image
    def applydiff(self,image):
        array = np.array(image)
        for x,y,r,g,b,a in self.diffarray:
            array[y][x] = (r,g,b,a)
        return(Image.fromarray(array))

    def addDiff(self,x,y,r,g,b,a):
        self.diffarray.append((x,y,r,g,b,a))

    # Define a function to pack a diff into 8 bytes
    def pack_diff(self, x, y, r, g, b, a):
        # Use the '>HHBBBB' format to pack two unsigned shorts (16 bits each) and four unsigned chars (8 bits each) in big-endian order
        # The first short will store the x coordinate
        # The second short will store the y coordinate
        # The four chars will store the r, g, b, and a values

        return struct.pack('>HHBBBB', x, y, r, g, b, a)
    
    def unpack_diff(self, bytes):
        return struct.unpack('>HHBBBB', bytes)

    #get packed representation for storage purposes - return a byte array
    def getPackedRepresentation(self):
        output = BytesIO()
        for item in self.diffarray:
            x,y,r,g,b,a = item
            output.write(self.pack_diff(x,y,r,g,b,a))
        return(output.getvalue())
    
    def getUnpackedRepresentation(self, bytes):
        output = []
        buffer = BytesIO(bytes)
        #consume BytesIO until end is reached, unpacking 8 bytes into change object
        while(buffer.tell() + 8 <= buffer.getbuffer().nbytes):
            current_diff = buffer.read(8)
            #print("current_diff: ",current_diff)
            output.append(self.unpack_diff(current_diff))
        return(output)