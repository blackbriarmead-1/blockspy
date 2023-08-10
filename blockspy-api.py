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

from flask import Flask, make_response, request, send_file
from flask_restful import Resource, Api, reqparse
import pandas as pd
import ast
app = Flask(__name__)
api = Api(app)

currentdb = "switchedtest"

class Tile(Resource):
    
    def get(self):
        dbConnection = util.initializeDB(currentdb)
        print("request gotten")
        print(request.content_type)
        args = request.args.to_dict()
        '''
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('x', required=True)  # add args
        parser.add_argument('y', required=True)
        parser.add_argument('zoom', required=True)
        parser.add_argument('index', required=True)
        args = parser.parse_args(request)  # parse arguments to dictionary
        '''
        print("made it past")
        x = int(args['x'])
        y = int(args['y'])
        zoom = int(args['zoom'])
        index = int(args['index'])
        byteIO = io.BytesIO()
        #index == -1 means latest image
        if(index == -1):
            util.getLatestImage(x-25, y-25, zoom, dbConnection).save(byteIO, format='PNG')
        elif(index >= 0):
            #0 means earliest image
            util.getImageFromDiffIndex(x-25, y-25, zoom, index, dbConnection).save(byteIO, format='PNG')

        response = make_response(byteIO.getvalue())
        response.headers.set('Content-Type', 'image/png')
        response.headers.set('Content-Disposition', 'attachment', filename='{}/{}_{}.png'.format(zoom,x,y))

        dbConnection.close()

        return response
    
class LiveTile(Resource):
    
    def get(self):
        dbConnection = util.initializeDB(currentdb)
        print("request gotten")
        print(request.content_type)

        args = request.args.to_dict()

        '''
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('x', required=True)  # add args
        parser.add_argument('y', required=True)
        parser.add_argument('zoom', required=True)
        parser.add_argument('index_into_database', required=False)

        args = parser.parse_args(request)  # parse arguments to dictionary'''
        print("made it past")
        x = int(args['x'])
        y = int(args['y'])
        zoom = int(args['zoom'])
        index_into_database = args['index_into_database']

        if(index_into_database == "True"):
            index_into_database = True
        else:
            index_into_database = False

        print("index into database:", index_into_database)
        byteIO = io.BytesIO()

        #tile = util.getTiles(x, y, x, y, zoom)[0]
        tile = util.getRemoteTile(x,y,zoom)
        tile.image.save(byteIO, format='PNG')
        print(tile)
        
        if(index_into_database):
            util.updateTile(tile,round(time.mktime(datetime.now().timetuple()) * 1000),dbConnection)
        
        response = make_response(byteIO.getvalue())
        response.headers.set('Content-Type', 'image/png')
        response.headers.set('Content-Disposition', 'attachment', filename='{}/{}_{}.png'.format(zoom,x,y))
        
        dbConnection.close()
        return response
    


api.add_resource(Tile, '/tile')
api.add_resource(LiveTile, '/live_tile')


if __name__ == '__main__':
    app.run()  # run our Flask app