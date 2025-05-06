import spacy
import json
import os
from flask import Flask, render_template, request, jsonify

# Cargar el modelo de lenguaje en español de Spacy
nlp = spacy.load('es_core_news_sm')

# Obtener la ruta del directorio actual
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# Ruta al archivo JSON
RUTA_JSON = os.path.join(DIRECTORIO_ACTUAL, 'videojuegos.json')

# Cargar base de datos desde el archivo JSON (ruta interna fija y validada)
def cargar_base_datos():
    try:
        with open(RUTA_JSON, 'r', encoding='utf-8') as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {RUTA_JSON}")
        return {"productos": []}
    except json.JSONDecodeError:
        print(f"Error: El archivo {RUTA_JSON} no tiene un formato JSON válido")
        return {"productos": []}

# Cargar la base de datos
JUEGOS_DB = cargar_base_datos()

class VideojuegosChatbot:
    def __init__(self, database):
        self.database = database

    def procesar_consulta(self, consulta):
        # Preprocesar la consulta con Spacy
        doc = nlp(consulta.lower())
        
        # Extraer intenciones y entidades
        intenciones = self._extraer_intenciones(doc)
        entidades = self._extraer_entidades(doc)
        
        # Generar respuesta basada en intenciones y entidades
        return self._generar_respuesta(intenciones, entidades)

    @staticmethod
    def _extraer_intenciones(doc):
        intenciones = []
        
        # Palabras clave
        palabras_info = ['informacion', 'detalles', 'descripción','trata','de que va']
        palabras_precio = ['precio', 'costo','cuesta','gratis','cuanto']
        palabras_recomendacion = ['recomendar','recomiendas', 'sugerir','sugieres' ,'puntuacion','esta chilo?']
        palabras_saludos = ['hola', 'ola','buenas tardes','buenos dias','buenas noches','que tal']

        for token in doc:
            if token.text in palabras_info:
                intenciones.append('informacion')
            if token.text in palabras_precio:
                intenciones.append('precio')
            if token.text in palabras_recomendacion:
                intenciones.append('recomendacion')
            if token.text in palabras_saludos:
                intenciones.append('saludos')
        
        return intenciones or ['saludos']

    def _extraer_entidades(self, doc):
        entidades = []
        
        # Buscar nombres de juegos en la consulta
        for producto in self.database['productos']:
            if producto['nombre'].lower() in doc.text.lower():
                entidades.append(producto['nombre'])
        
        return entidades

    def _generar_respuesta(self, intenciones, entidades):
        # Si no hay entidades, dar una respuesta general
        if not entidades:
            return "Estoy especializado en información de videojuegos. ¿Sobre qué juego quieres saber?"

        # Buscar el juego en la base de datos
        juego = next((j for j in self.database['productos'] if j['nombre'] in entidades), None)
        
        if not juego:
            return "Lo siento, no encontré información sobre ese juego."

        # Generar respuestas según las intenciones
        if 'informacion' in intenciones:
            return f"Información de {juego['nombre']}: {juego['descripcion']}"
        
        if 'precio' in intenciones:
            return f"El precio de {juego['nombre']} es ${juego['precio']}"
        
        if 'recomendacion' in intenciones:
            if juego['puntuacion'] >= 3.0:
                return f"Te recomiendo {juego['nombre']} con una puntuación de {juego['puntuacion']}/5.0"
            else:
                return f"No te recomiendo {juego['nombre']} con una puntuacion de {juego['puntuacion']}/5.0"
        if 'saludos' in intenciones:
            return "Hola buenas en que puedo ayudarte hoy?"    
        
        # Respuesta por defecto
        return f"Tengo información sobre {juego['nombre']}. ¿Qué te gustaría saber?"

app = Flask(__name__)
chatbot = VideojuegosChatbot(JUEGOS_DB)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("Bienvenido, ¿en que puedo ayudarle?")
    mensaje = request.json['mensaje']
    respuesta = chatbot.procesar_consulta(mensaje)
    return jsonify({'respuesta': respuesta})

if __name__ == '__main__':
    app.run(debug=True)
