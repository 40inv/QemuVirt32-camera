# import the Flask class from the flask module
import os
import hashlib
from pprint import pprint
import urllib
import sys
import queue
import gpiod
import threading
import time
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory, send_file, Response
from werkzeug.utils import secure_filename
from functools import wraps
from camera import VideoCamera

#reload(sys)
#sys.setdefaultencoding('utf8')

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'dir//'))

# create the application object
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
com_queue = queue.Queue();
modeCh = True # if true detect mode if false live stream
# config
app.secret_key = 'my precious'
# To list the current directory of the script, use os.path.dirname(os.path.abspath(__file__))
base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'dir//'))
# These directories will not be listed
ignored_dirs = ["venv"]
ignore_dotfiles = True
ignore_dollarfiles = True
omit_folders = True
omit_files = False



# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# use decorators to link the function to a url
@app.route('/uploadfile', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded'))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
      <p>Click <a href="/content">here</a> to go to content.</p>
    </form>
    '''

""" The base route with the file list """
@app.route("/")
@login_required
def home():
    files = []
    dirs = []
    meta = {
        "current_directory": base_directory
    }
    for (dirpath, dirnames, filenames) in os.walk(base_directory):
        for name in filenames:
            if omit_files == True:
                break

            for ign in ignored_dirs:
                if ign in dirnames:
                    dirnames.remove(ign)
            nm = os.path.join(dirpath, name).replace(base_directory, "").strip("/").split("/")
            fullpath = os.path.join(dirpath, name)
            if os.path.isfile(fullpath) == False:
                continue
            size = os.stat(fullpath).st_size
            if len(nm) == 1:
                name_s = name.split(".")
                if ignore_dotfiles == True:
                    if name_s[0] == "" or name_s[0] == None:
                        continue
                files.append({
                    "name": name,
                    "size": str(size) + " B",
                    "fullname": urllib.parse.quote_plus(fullpath)
                })
        for dirname in dirnames:
            if omit_folders == True:
                break
            fullpath = os.path.join(dirpath, dirname)
            if ignore_dotfiles == True:
                name_split = dirname.split(".")
                if name_split[0] == "" or name_split[0] == None:
                    continue
            if ignore_dollarfiles == True:
                name_split = dirname.split("$")
                if name_split[0] == "" or name_split[0] == None:
                    continue
            dirs.append({
                "name": dirname,
                "size": "0b"
            })
    return render_template("index.html", files=sorted(files, key=lambda k: k["name"].lower()), folders=dirs, meta=meta)

@app.route("/download/<filename>")
@login_required
def download(filename):
    filename = urllib.parse.unquote(filename)
    if os.path.isfile(filename):
        if os.path.dirname(filename) == base_directory.rstrip("/"):
            return send_file(filename, as_attachment=True)
        else:
            return render_template("no_permission.html")
    else:
        return render_template("not_found.html")
    return None

@app.route('/uploaded')
@login_required
def uploaded():
    return render_template('uploaded.html') 

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            flash('You were logged in.')
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.')
    return redirect(url_for('welcome'))

@app.route('/video',methods=["GET", "POST"])
@login_required
def video():
    global modeCh
    if request.method == "POST":
        com_queue.put(2)
        if modeCh == True:
            modeCh = False
        else:
            modeCh = True
            return redirect(url_for('home'))
    return render_template('video.html')

def gen(camera):
    global modeCh
    while True:
        try:
            mode = com_queue.get(timeout=0)
            if mode == 0:
                modeCh = True
                camera.video.release()
                print("cam server rel")
                break
        except queue.Empty:
             pass
        modeCh = False
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def serverStart(_com_queue):
    threading.Thread(target=q2q, args=(com_queue,_com_queue)).start()
    app.run(host='0.0.0.0', port=8810)

def q2q(server_com_queue,_com_queue):
    while(1):
        try:
            mode = _com_queue.get(timeout=0)
            if mode == 0:
                server_com_queue.put(mode)
            else:
                _com_queue.put(mode)
        except queue.Empty:
                pass
        try:
            mode = server_com_queue.get(timeout=0)
            if mode == 2:
                _com_queue.put(mode)
        except queue.Empty:
                pass
