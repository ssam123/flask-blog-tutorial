from flask_blog import db

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(80))
    email = db.Column(db.String(35), unique=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(60))
    is_author = db.Column(db.Boolean)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    #first call (constructor)?
    def __init__(self, fullname, email, username, password, is_author):
        self.fullname = fullname
        self.email = email
        self.username = username
        self.password = password
        self.is_author = is_author
    
    #how will info be displayed when called    
    def __repr__(self):
        return '<Author %r>' % self.username
        
    