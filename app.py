from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date
from forms import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///list.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# secret key for sessions (signed cookies). Flask uses it to protect the contents of the user session against tampering.
app.config["SECRET_KEY"] = '\xfc\x1a\x1b\x91G\x97E\xceb\xaa\x15\xa8u\x86\xaf\x13\x9fm\x1e\xbb\x85\t'
# token for csrf protection of forms.
app.config["WTF_CSRF_SECRET_KEY"] = '\xfc\x1a\x1b\x91G\x97E\xceb\xaa\x15\xa8u\x86\xaf\x13\x9fm\x1e\xbb\x85\t'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

'''
Den xerw an tha exoume xrono na to exigisoume auto alla tha mporousame na
ylopiisoume tin klasi mprosta tous kai na tous poume na kanoun autoi ta crud commands me tin lista
px gia to spiti i kt na exikiothoune 
kai dld tous dixnoume pws doulevoun ta migrations as well 
class TodoListModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    todos = db.relationship('TodoModel', backref='list', lazy=True)

    def __repr__(self):
        return f"<TodoList {self.id}: {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'todos': [todo.to_dict() for todo in self.todos]
        }
'''

# To-do model


class ListModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_by = db.Column(db.Date, default=date.today())
    tasks = db.relationship('TasksModel', backref='list', lazy=True)

    def __repr__(self):
        return f"<List {self.id}: {self.title}>"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed
        }


class TasksModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey(
        ListModel.id), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"

    def to_dict(self):
        return {
            'id': self.id,
            'list_id': self.list_id,
            'title': self.title,
            'completed': self.completed
        }


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# Route to get a specific todo ( as to see the database )


@app.route('/lists/<int:list_id>', methods=['GET'])
def get_list(list_id):
    with app.app_context():
        list = ListModel.query.get(list_id)
        if list:
            return jsonify(list.to_dict())
        else:
            return jsonify({'message': 'To-do not found'}), 404

# Route to create a new todo


# Route to update an existing todo
@app.route('/lists/<int:list_id>', methods=['PUT', 'POST'])
def update_list(list_id):
    with app.app_context():
        list = ListModel.query.get(list_id)
        if list:
            list.title = request.form.get('title', list.title)
            list.description = request.form.get(
                'description', list.description)
            completed = request.form.get('completed', '')
            if completed == 'on':
                list.completed = True
            else:
                list.completed = False
            db.session.add(list)
            db.session.commit()
            return '', 204

# Route to delete a specific todo


@app.route('/lists/delete/<int:list_id>', methods=['DELETE', 'POST'])
def delete_list(list_id):
    with app.app_context():
        tasks = TasksModel.query.filter_by(list_id=list_id)
        list = ListModel.query.get(list_id)
        try:
            for task in tasks:
                db.session.delete(task)
            db.session.delete(list)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            flash(str(e), "danger")
            return 'Error: List not found'

# Home route


@app.route('/', methods=['GET'])
def lists():
    with app.app_context():
        lists = ListModel.query.all()
        return render_template('lists.html', lists=lists)

# Route to display the new to-do form


@app.route('/lists/new', methods=['GET', 'POST'])
def new_list():
    listform = ListForm()
    try:
        if (request.method == 'POST' and listform.validate_on_submit()):
            newlist = listform.__dict__
            list = ListModel(
                title=newlist['title'].data, description=newlist['description'].data, due_by=newlist['due_by_date'].data)
            db.session.add(list)
            db.session.commit()
            return redirect(url_for('lists'))
        return render_template('new_list.html', form=listform)
    except Exception as e:
        flash(str(e), "danger")
        return render_template('new_list.html', form=listform)

# Route to display the edit to-do form


@app.route('/lists/<int:list_id>/edit', methods=['GET', 'POST'])
def edit_list_form(list_id):
    listform = ListForm()
    try:
        if (request.method == 'POST' and listform.validate_on_submit()):
            newlist = listform.__dict__
            list = ListModel.query.get(list_id)
            list.title = newlist['title'].data
            list.description = newlist['description'].data
            list.due_by=newlist['due_by_date'].data
            list.completed = newlist['completed'].data
            db.session.add(list)
            db.session.commit()
            return redirect(url_for('lists'))
        
        list = ListModel.query.get(list_id)
        listform.title.data = list.title
        listform.description.data = list.description
        listform.due_by_date.data = list.due_by
        listform.completed.data = list.completed
        return render_template('edit_list.html', form=listform)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('lists'))


@app.route('/<list_title>', methods=['GET'])
def print_list(list_title):
    with app.app_context():
        list = db.one_or_404(db.select(ListModel).filter_by(title=list_title))
        tasks = db.session.scalars(TasksModel.query.filter_by(list_id=list.id))
        return render_template('list.html', list=list, tasks=tasks.all())


@app.route('/<list_id>/add', methods=['POST'])
def add_task(list_id):
    task = TasksModel(title=request.form['title'], list_id=list_id)
    print(list_id)
    print(task)
    db.session.add(task)
    db.session.commit()
    list = db.one_or_404(db.select(ListModel).filter_by(id=list_id))
    return redirect(url_for('print_list', list_title=list.title))

@app.route('/<task_id>',methods=['POST'])
def check_task(task_id):
    try:
        task = TasksModel.query.get(task_id)
        if request.form.get('completed', '') == "on":
            print(request.form.get('completed', ''))
            task.completed = True
        else:
            task.completed = False
        db.session.add(task)
        db.session.commit()
        return '',204
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('lists'))