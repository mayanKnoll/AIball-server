from distutils.log import debug
from flask import Flask, render_template, url_for, request, redirect
import server
app = Flask(__name__)
#check
@app.route('/', methods=['POST', 'GET'])
def home_page():
    flag_team = True
    if request.method == 'POST':
        
        try:
            return server.http_server(request.form['code'],request.form['content'])
        except Exception as e:
            return e
    else:
        try:
            return server.http_server('200')
        except Exception as e:
            return e 

# connecting to the server

app.run(debug=False,host='0.0.0.0')