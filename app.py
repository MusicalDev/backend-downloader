from flask import Flask, request, jsonify, send_file
import os
import requests
from io import BytesIO
from flask_cors import CORS
import zipfile
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/descargar_zip', methods=['POST'])
def descargar_zip():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No se recibieron datos", "success": False}), 400

        # Validar campos requeridos
        campos_requeridos = ['instrumento', 'id', 'music', 'tamaño', 'numero', 'paginas']
        faltantes = [campo for campo in campos_requeridos if not data.get(campo)]
        if faltantes:
            return jsonify({
                "error": f"Faltan los siguientes campos obligatorios: {', '.join(faltantes)}",
                "success": False
            }), 400

        instrumento = "".join(c for c in data['instrumento'] if c.isalnum() or c in (" ", "_", "-")).strip()
        id = data['id']
        music = data['music']
        tamaño = data['tamaño']
        numero = data['numero']
        paginas_str = data['paginas']

        # Procesar las páginas seleccionadas
        paginas = set()
        for parte in paginas_str.split(','):
            parte = parte.strip()
            if '-' in parte:
                try:
                    inicio, fin = map(int, parte.split('-'))
                    paginas.update(range(inicio, fin + 1))
                except ValueError:
                    return jsonify({
                        "error": f"Formato de página incorrecto: '{parte}'",
                        "success": False
                    }), 400
            else:
                try:
                    paginas.add(int(parte))
                except ValueError:
                    return jsonify({
                        "error": f"Formato de página incorrecto: '{parte}'",
                        "success": False
                    }), 400

        if not paginas:
            return jsonify({
                "error": "No se ingresaron páginas válidas",
                "success": False
            }), 400

        # Crear archivo ZIP en memoria
        zip_filename = f"{instrumento}_partituras.zip"
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for page in sorted(paginas):
                x_str = f"{page:03d}"
                link = f"https://archives.nyphil.org/index.php/jp2/|{music}|{numero}|{id}|{music}_{id}_{x_str}.jp2/portrait/{tamaño}"
                logger.info(f"Generando enlace para la página {x_str}: {link}")

                try:
                    response = requests.get(link, stream=True, timeout=15)
                    if response.status_code == 200:
                        # zipf.writestr(f"{music}_{id}_{x_str}.jp2", response.content)
                        zipf.writestr(f"{instrumento}_{music}_{id}_{x_str}.jpg", response.content)

                        logger.info(f"Página {page} descargada exitosamente")
                    else:
                        logger.warning(f"Página {page} no encontrada (Error {response.status_code})")
                except requests.RequestException as e:
                    logger.error(f"Error al descargar página {page}: {str(e)}")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer) as check_zip:
            if not check_zip.namelist():
                return jsonify({
                    "error": "No se pudieron descargar partituras. Verifique los parámetros ingresados.",
                    "success": False
                }), 404

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            "error": "Ocurrió un error en el servidor",
            "success": False
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

