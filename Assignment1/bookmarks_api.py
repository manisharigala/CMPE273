from flask import Flask, request, jsonify, Response, send_file
from Bookmark import Bookmark
from sqlitedict import SqliteDict
import json
import random

app = Flask(__name__)

@app.route('/api/bookmarks', methods = ['POST'])
def save_bookmark():
    
    with SqliteDict('./my_db.sqlite') as mydict:

        data = request.get_json()
        print(data)
        for key in mydict:
            print(mydict[key])
            if mydict[key].url == data['url']:
                resp = {"reason": "The given URL already existed in the system."}
                return Response(response = json.dumps(resp), status = 400)
        
        id = "abc" + str(random.randint(0, 101)) 
        while id in mydict.keys():
            id = "abc" + str(random.randint(0, 101)) 
        
        
        mydict[id] = Bookmark(id, data['name'], data['url'], data['description'])
        mydict.commit()
        response = {"id":id}

    return Response(response=json.dumps(response), status=202)

@app.route('/api/bookmarks/<id>', methods = ['GET'])
def return_bookmark(id):
    with SqliteDict('./my_db.sqlite') as mydict:
        if id in mydict.keys():
            resp = mydict[id].__dict__
            del resp['etag']
            return Response(response=json.dumps(resp), status=200)
        else:
            return Response(status=404)



if __name__ == "__main__":
    app.run(debug=True)