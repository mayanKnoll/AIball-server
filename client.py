from distutils.log import debug
from flask import Flask, render_template, url_for, request, redirect
import socket
import server
import threading
server_th = threading.Thread(target=server.main,args=() )
server_th.start()
app = Flask(__name__)
PORT = 3000

@app.route('/', methods=['POST', 'GET'])
def home_page():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(10)
    if request.method == 'POST':
        try:
            team_name = request.form['content']
            if len(team_name) > 0:
                s.sendto(("300:"+team_name).encode(), ("127.0.0.1", 3000))
            else:
                s.sendto("200:all groups".encode(), ("127.0.0.1", 3000))
            teams = s.recv(1024).decode()
        except socket.error as e:
            teams=e
    else:
        try:
            s.sendto("200:all groups".encode(), ("127.0.0.1", 3000))
            teams = s.recv(1024).decode()
            # teams = "mayan"
        except socket.error as e:
            teams=e
    s.close()   

# connecting to the server
    return render_template('index.html', text=teams)

app.run(debug=False,host='0.0.0.0')