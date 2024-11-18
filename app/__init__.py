from flask import Flask
# from markupsafe import escape

# app = Flask(__name__)

# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"

# @app.route("/<name>")
# def hello(name):
#     return f"Hello, {escape(name)}!"

# @app.route('/')
# def index():
#     return 'Index Page'

# @app.route('/hello')
# def hello():
#     return 'Hello, World'

def create_app():
    app = Flask(__name__)
    # Configurações adicionais (se houver)
    
    # Importar rotas
    from .routes import main
    app.register_blueprint(main)

    return app