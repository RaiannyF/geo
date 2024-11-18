from flask import Blueprint, render_template
import leafmap

main = Blueprint('main', __name__)

@main.route('/')
def home():
   # Configuração do mapa interativo
    m = leafmap.Map(center=[47.653287, -117.588070], zoom=16, height="600px")
    m.add_basemap("Satellite")

    # Gera o HTML do mapa
    map_html = m.to_html()

    # Passa o HTML gerado para o template
    return render_template('index.html', map_html=map_html)

