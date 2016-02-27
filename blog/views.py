from flask_blog import app, db, uploaded_images
from flask import render_template, redirect, flash, url_for, session, abort, request
from blog.form import SetupForm, PostForm, CommentForm
from author.models import Author
from blog.models import Blog, Post, Category, Comment
from author.decorators import login_required, author_required
import bcrypt
from slugify import slugify

POST_PER_PAGE = 5

@app.route('/')
@app.route('/index')
@app.route('/index/<int:page>')
def index(page=1): #if no page given it goes ti page 1
    #gets the first blog
    blog = Blog.query.first()
    #if there are no blogs redirect user to setup page to make blog
    if not blog:
        return redirect(url_for('setup'))
    #if there are blogs display all posts
    #goes to page specified in url and sets max pages to 5
    #false: returns empty list if specified page does not exist
    #filter by live articles
    posts = Post.query.filter_by(live=True).order_by(Post.publish_date.desc()).paginate(page, POST_PER_PAGE, False)
    return render_template('blog/index.html', blog=blog, posts=posts)
    
@app.route('/admin')
@app.route('/admin/<int:page>')
@author_required
def admin(page=1):
    #go to admin page only if is_author is true
    if session.get('is_author'):
        #get all posts in descending order
        posts = Post.query.order_by(Post.publish_date.desc()).paginate(page, POST_PER_PAGE, False)
        return render_template('blog/admin.html', posts=posts)
    else:
        abort(403)
    
@app.route('/setup', methods=('GET','POST'))
def setup():
    #set form to blog setup form
    form = SetupForm()
    error = ""
    
    #checks if input fields are valid
    if form.validate_on_submit():
        # generates password hash    
        salt = bcrypt.gensalt()
        # creates hashed password by using the salt to hash the pw given in the form
        hashed_password = bcrypt.hashpw(form.password.data, salt)
        
        author = Author(
            form.fullname.data,
            form.email.data,
            form.username.data,
            hashed_password,
            True
            )
        #add the new author to the session
        db.session.add(author)
        
        #simulate that the author was written and will return an id to test 
        db.session.flush()
        #if an id was created by flush, set blog name and author ID
        if author.id:
            blog = Blog(
                form.name.data,
                author.id
                )
            
            #add new blog to session
            db.session.add(blog)
            #simulate that the blog was  written and will return an id to test 
            db.session.flush()
        else:
            #if the author ID was not created, cancel this input and give error
            db.session.rollback()
            error = "Error creating user"
            
        #if flush sucessfully created an author ID and blog ID
        #commit both to the database
        if author.id and blog.id:
            db.session.commit()
            flash("Blog created")
            
            #and redirect to the admin page
            return redirect(url_for('index'))
        
        #if author and blog were not created, cancel and give error
        else:
            db.session.rollback()
            error = "Error creating blog"
    
    #render setup template/forms/errors                
    return render_template('blog/setup.html', form=form, error=error)
    
@app.route('/post', methods = ('GET','POST'))
@author_required
def post():
    form = PostForm()
    if form.validate_on_submit():
        #get image from request
        image = request.files.get('image')
        filename = None
        try:
            #save the image to the static images folder
            filename = uploaded_images.save(image)
        except:
            flash('The image was not uploaded')
        #if user is creating new category, add category to database
        if form.new_category.data:
            new_category = Category(form.new_category.data)
            db.session.add(new_category)
            db.session.flush()
            category = new_category
        # if user selects existing category
        elif form.category.data:
            #get primary key from category
            category_id = form.category.get_pk(form.category.data)
            category = Category.query.filter_by(id = category_id).first()
        else:
            category = None
        #assuming each application has only 1 blog
        blog = Blog.query.first()
        author = Author.query.filter_by(username = session['username']).first()
        title = form.title.data
        body = form.body.data
        slug = slugify(title)
        post = Post(blog, author,title,body, category, filename, slug)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('article', slug=slug))
    return render_template('blog/post.html', form=form, action="new")
  
#<slug> looks up url based on slug from database  
@app.route('/article/<slug>', methods = ('GET','POST'))
def article(slug):
    form = CommentForm()
    #get posts by slug ID
    #first_or_404: if post found returns post if not returns 404
    post = Post.query.filter_by(slug=slug).first_or_404()
    if form.validate_on_submit():
        author = Author.query.filter_by(username = session['username']).first()
        body = form.body.data
        comment = Comment(post, author, body)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('article', slug=slug))
    comments = Comment.query.filter_by(live=True).filter_by(post_id=post.id)
    return render_template('blog/article.html', post=post, form=form, comments = comments, action="new")
    
@app.route('/delete_post/<int:post_id>')
@author_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    post.live=False
    db.session.commit()
    flash('Article deleted')
    return redirect('admin')
    
@app.route('/delete_comment/<int:comment_id>')
@author_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first_or_404()
    comment.live=False
    db.session.commit()
    flash('Comment deleted')
    return redirect(url_for('article', slug = comment.post.slug))
    
@app.route('/edit_post/<int:post_id>', methods=('GET','POST'))
@author_required
def edit_post(post_id):
    #get post
    post = Post.query.filter_by(id=post_id).first_or_404()
    #assign all fields from post to the form
    form = PostForm(obj=post)
    if form.validate_on_submit():
        original_image = post.image
        #loads post object with contents of form aka edited information
        form.populate_obj(post)
        #if the user submitted a new image
        if form.image.has_file():
            image = request.files.get('image')
            #try to saeve image
            try:
                filename = uploaded_images.save(image)
            except:
                flash("The image was not uploaded")
            #if saved set post image to the file
            if filename:
                post.image = filename
        #if no image submitted make sure the image stays
        else:
            post.image = original_image
        #if new category
        if form.new_category.data:
            new_category = Category(form.new_category.data)
            db.session.add(new_category)
            db.session.flush()
            post.category = new_category
        db.session.commit()
        return redirect(url_for('article', slug=post.slug))
    return render_template('blog/post.html', form=form, post=post, action='edit')
    
@app.route('/edit_comment/<int:comment_id>', methods=('GET','POST'))
@author_required
def edit_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first_or_404()
    form = CommentForm(obj = comment)
    if form.validate_on_submit():
        form.populate_obj(comment)
        db.session.commit()
        return redirect(url_for('article', slug = comment.post.slug)) 
    return render_template('blog/article.html', form = form, post = comment.post, comment = comment, action='edit')
        
        
    
    