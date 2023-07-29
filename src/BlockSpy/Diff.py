from io import BytesIO
import struct

class Diff:
    def __init__(self, packed = None):
        self.diffarray = []

        if not packed == None:
            self.diffarray = self.getUnpackedRepresentation(packed)

    def __str__(self):
        return("Diff Object. \nnumber of differences: {}".format(len(self.diffarray)))

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