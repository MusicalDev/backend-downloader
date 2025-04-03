
from flask import Flask, request, jsonify, send_file
import os
import requests
from io import BytesIO
from flask_cors import CORS
import zipfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/descargar_zip', methods=['POST'])
def descargar_zip():
    data = request.json
    instrumento = data.get('instrumento')
    id = data.get('id')
    music = data.get('music')
    tamaño = data.get('tamaño')
    numero = data.get('numero')
    paginas_str = data.get('paginas', '')

    # Verificación de que el campo 'instrumento' esté presente
    if not instrumento:
        return jsonify({"mensaje": "El campo 'instrumento' es obligatorio", "success": False}), 400

    # Limpiar el nombre del instrumento para evitar caracteres no válidos
    instrumento = "".join(c for c in instrumento if c.isalnum() or c in (" ", "_", "-")).strip()

    # Inicializar el conjunto de páginas a descargar
    paginas = set()
    
    # Procesar las páginas seleccionadas
    if paginas_str:
        for parte in paginas_str.split(','):
            if '-' in parte:  # Rango de páginas (ej: "3-5")
                try:
                    inicio, fin = map(int, parte.split('-'))
                    paginas.update(range(inicio, fin + 1))
                except ValueError:
                    return jsonify({"mensaje": "Formato de página incorrecto", "success": False}), 400
            else:
                try:
                    paginas.add(int(parte))
                except ValueError:
                    return jsonify({"mensaje": "Formato de página incorrecto", "success": False}), 400

    if not paginas:
        return jsonify({"mensaje": "No se ingresaron páginas válidas", "success": False}), 400

    # Crear archivo ZIP en memoria
    zip_filename = f"{instrumento}_partituras.zip" if instrumento else "partituras.zip"
    zip_buffer = BytesIO()

    paginas = set()

    if paginas_str:
        for parte in paginas_str.split(','):
            if '-' in parte:  # Rango de páginas (ej: "3-5")
                try:
                    inicio, fin = map(int, parte.split('-'))
                    paginas.update(range(inicio, fin + 1))
                except ValueError:
                    return jsonify({"mensaje": "Formato de página incorrecto", "success": False}), 400
            else:
                try:
                    paginas.add(int(parte))
                except ValueError:
                    return jsonify({"mensaje": "Formato de página incorrecto", "success": False}), 400

    if not paginas:
        return jsonify({"mensaje": "No se ingresaron páginas válidas", "success": False}), 400



    # Crear el archivo ZIP con las partituras
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for page in sorted(paginas):
            x_str = f"{page:03d}"
            link = f"https://archives.nyphil.org/index.php/jp2/|{music}|{numero}|{id}|{music}_{id}_{x_str}.jp2/portrait/{tamaño}"
            print(f"Generando enlace para la página {x_str}: {link}")
            try:
                response = requests.get(link, stream=True)
                if response.status_code == 200:
                    img_data = response.content
                    zipf.writestr(f"{music}_{id}_{x_str}.jp2", img_data)
                else:
                    print(f"Página {page} no encontrada (Error {response.status_code})")
            except requests.RequestException as e:
                print(f"Error al descargar página {page}: {str(e)}")

    zip_buffer.seek(0)

    # Devolver el archivo ZIP como descarga
    return send_file(zip_buffer, as_attachment=True, download_name=zip_filename, mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
