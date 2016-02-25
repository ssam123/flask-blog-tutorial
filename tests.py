# set the path
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy

from flask_blog import app, db

#models
from author.models import *
from blog.models import *

class UserTest(unittest.TestCase):
    def setUp(self):
        #setting up the test db
        db_username = app.config['DB_USERNAME']
        db_password = app.config['DB_PASSWORD']
        db_host = app.config['DB_HOST']
        self.db_uri = DB_URI = "mysql+pymysql://%s:%s@%s/" % (db_username, db_password, db_host)
        #so flask knows that testing is happening
        app.config['TESTING'] = True
        #since we are checking we want to allow mock requests without checking csrf
        app.config['WTF_CSRF_ENABLED'] = False
        
        app.config['BLOG_DATABASE_NAME'] = 'test_blog'
        app.config['SQLALCHEMY_DATABASE_URI'] = self.db_uri + app.config['BLOG_DATABASE_NAME']
        #create sqlalchemy instance we can talk to
        engine = sqlalchemy.create_engine(self.db_uri)
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("CREATE DATABASE " + app.config['BLOG_DATABASE_NAME'])
        #so all tables are created
        db.create_all()
        conn.close()
        #instantiate app
        self.app = app.test_client()
    
    #delete database    
    def tearDown(self):
        db.session.remove()
        engine = sqlalchemy.create_engine(self.db_uri)
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("DROP DATABASE " + app.config['BLOG_DATABASE_NAME'])
        conn.close()
        
    def create_blog(self):
        #simulate creation of blog through a post to setup
        #pass required fields in a dictionary
        return self.app.post('/setup', data=dict(
            name='My Test Blog',
            fullname='Test Name',
            email='test@email.com',
            username='samuel',
            password='test',
            confirm='test',
            ),
        #necessary to execute
        follow_redirects=True)
        
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
            ),
        follow_redirects=True)
        
    def logout(self):
        return self.app.get('/logout', follow_redirects = True)
        
    #tests always start with test_
    def test_create_blog(self):
        rv = self.create_blog()
        #since in views creating a blog redirects and flashes 'blog created'
        assert 'Blog created' in str(rv.data)
        
    def test_login_logout(self):
        self.create_blog()
        rv = self.login('samuel', 'test')
        assert 'User samuel logged in' in str(rv.data)
        
        rv = self.logout()
        assert 'User logged out' in str(rv.data)
        
        rv = self.login('samuel','wrong')
        assert "Incorrect username or password" in str(rv.data)
        
        
if __name__ == '__main__':
    unittest.main()