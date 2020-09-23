from flask import Flask, request, jsonify, Response, send_file, make_response
from Bookmark import Bookmark
from sqlitedict import SqliteDict
import json
import random
import qrcode
import os


app = Flask(__name__)

@app.route('/api/bookmarks', methods = ['POST'])
def save_bookmark():
    
    with SqliteDict('./my_db.sqlite') as mydict:

        data = request.get_json()
        for key in mydict:
            print(mydict[key])
            if mydict[key].url == data['url']:
                resp = {"reason": "The given URL already existed in the system."}
                return Response(response = json.dumps(resp), status = 400)
        
        id = "abc" + str(random.randint(0, 1000)) 
        while id in mydict.keys():
            id = "abc" + str(random.randint(0, 1000)) 
        
        mydict[id] = Bookmark(id, data['name'], data['url'], data['description'])
        mydict.commit()
        response = {"id":id}

    return Response(response=json.dumps(response), status=202)


@app.route('/api/bookmarks/<id>', methods = ['GET'])
def return_bookmark(id):
    with SqliteDict('./my_db.sqlite') as mydict:
        if id in mydict.keys():
            temp = mydict[id]
            temp.etag += 1
            mydict[id] = temp
            print(mydict[id].etag)
            resp = mydict[id].__dict__
            del resp['etag']
            mydict.commit()
            return Response(response=json.dumps(resp), status=200)
        else:
            return Response(status=404)


@app.route('/api/bookmarks/<id>/qrcode', methods = ['GET'])
def get_qrcode(id):
    with SqliteDict('./my_db.sqlite') as mydict:
        if id in mydict.keys():
            img = qrcode.make(mydict[id].url)
            loc = './qrcodes/qrcode_'+id+'.png'
            img.save(loc)
            resp = send_file(loc)
            os.remove(loc)
            return resp
        else:
            return Response(status=404)


@app.route('/api/bookmarks/<id>', methods = ['DELETE'])
def delete_bookmark(id):
    with SqliteDict('./my_db.sqlite') as mydict:
        if id in mydict.keys():
            del mydict[id]
            mydict.commit()
            return Response(status=204)
        else:
            return Response(status=404)


@app.route('/api/bookmarks/<id>/stats', methods = ["GET"])
def etag_check(id):
    with SqliteDict('./my_db.sqlite') as mydict:
        if id in mydict.keys():
            if (request.if_none_match.contains(str(mydict[id].etag))):
                return Response(status = 304)
                
            else:
                resp = Response(response=str(mydict[id].etag), status=200)
                resp.headers['Etag'] = str(mydict[id].etag)
                return resp
        else:
            return Response(status=404)
          

if __name__ == "__main__":
    app.run(debug=True)