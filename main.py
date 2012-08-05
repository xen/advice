# -*- coding: utf-8 -*-
from __future__ import with_statement
from consoleargs import command
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

# create our little application :)
app = Flask(__name__)
app.config.from_object('config')
app.config.from_pyfile('local.cfg', silent=True)

def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def show_entries():
    # SELECT * FROM table ORDER BY RANDOM() LIMIT 1;
    cur = g.db.execute('select text, id from entries order by random() limit 1;')
    #entries = [dict(text=row[0]) for row in cur.fetchall()]
    text = cur.fetchone()
    if text:
        return render_template('advices.html', text=text[0])
    else:
        return render_template('advices.html', text="No entries")


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (text) values (?)',
                 [request.form['text'],])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def init_db():
    """ Creates the database tables. """
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

@command
def main(host='0.0.0.0', port=5000, command='run'):
    """
    :param host: listen to ip address
    :param port: listen to port, default 5000
    :param config: configuration file
    :param command: default 'run', for db init use 'init'
    """
    if command == 'init':
        print("Database init %s" % app.config['DATABASE'])
        init_db()
    else:
        app.run(host=host, port=port)

if __name__ == '__main__':
    main()
