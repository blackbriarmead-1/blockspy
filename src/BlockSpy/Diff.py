from io import BytesIO
import struct

class Diff:
    def __init__(self):
        self.diffarray = []

    def addDiff(self,x,y,r,g,b,a):
        self.diffarray.append((x,y,r,g,b,a))

    # Define a function to pack a diff into 8 bytes
    def pack_diff(self, x, y, r, g, b, a):
        # Use the '>HHBBBB' format to pack two unsigned shorts (16 bits each) and four unsigned chars (8 bits each) in big-endian order
        # The first short will store the x coordinate
        # The second short will store the y coordinate
        # The four chars will store the r, g, b, and a values
        return struct.pack('>HHBBBB', x, y, r, g, b, a)

    #get packed representation for storage purposes - return a byte array
    def getPackedRepresentation(self):
        output = BytesIO()
        for item in self.diffarray:
            x,y,r,g,b,a = item
            output.write(self.pack_diff(x,y,r,g,b,a))
        return(output.getvalue())
