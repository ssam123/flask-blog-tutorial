from flask_wtf import Form
from wtforms import StringField, validators, TextAreaField
from author.form import RegisterForm
from blog.models import Category
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed

#setupform inherits from the registerform
class SetupForm(RegisterForm):
    #add new blogname fields
    name = StringField('Blog name', [
        validators.Required(),
        validators.Length(max=80)
        ])
        
def categories():
    return Category.query

class PostForm(Form):
    image = FileField('Image', validators=[
        FileAllowed(['jpg','png'], 'Images only!')
        ])
    title = StringField('Title', [
        validators.Required(),
        validators.Length(max=80),
        ])
    #body where text is input
    body = TextAreaField('Content', validators =[validators.Required()])
    #field that allows user to select
    #query_factory points to defined function
    category = QuerySelectField('Category', query_factory=categories, allow_blank=True)
    new_category = StringField('New Category')
        