from io import BytesIO
import hashlib

class Tile:
    #construct an image object
    def __init__(self,image,x,y,zoom, hash = None, latest_hash = None):
        self.image = image
        self.x = x
        self.y = y
        self.zoom = zoom
        if(hash == None):
            #calculate image hash if not supplied
            byteIO = BytesIO()
            image.save(byteIO, format='PNG')
            self.hash = hashlib.md5(byteIO.getvalue()).hexdigest()
            self.latest_hash = self.hash
        else:
            #use provided hash
            self.hash = hash
            if not latest_hash == None:
                self.latest_hash = latest_hash
            else:
                self.latest_hash = self.hash

    def __str__(self):
        return "TileObject:\nx: {}\ny: {}\nzoom: {}\nhash (md5): {}".format(self.x,self.y,self.zoom,self.hash)

    def toBytes(self):
        byteIO = BytesIO()
        self.image.save(byteIO, format='PNG')
        return(byteIO.getvalue())
    
    def saveTileImage(self, path):
        with open(path,"wb") as file:
            file.write(self.toBytes())
    
    def updateImage(self,new_image):
        self.image = new_image
        byteIO = BytesIO()
        new_image.save(byteIO, format='PNG')
        self.hash = hashlib.md5(byteIO.getvalue()).hexdigest()