from flask import Flask, render_template, request, redirect, url_for,jsonify
from flask import send_file
from werkzeug.utils import secure_filename, safe_join
import csv
import os
from openpyxl import load_workbook
from openpyxl.worksheet.protection import SheetProtection
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import chardet
from base import lojas
from materials import materials
from flask_socketio import SocketIO, emit
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


app = Flask(__name__)
socketio = SocketIO(app)


AUTHORIZED_MATERIALS = []  
status = "" 



@app.route('/config', methods=['GET'])
def configurations():
   
    return render_template('config.html', authorized_materials=', '.join(AUTHORIZED_MATERIALS), status=status)

@app.route('/check-password', methods=['POST'])
def check_password():
    password = request.form.get('password')
    if password == '2024': 
        return redirect(url_for('configurations')) 
    else:
        return redirect(url_for('index', message='Senha incorreta!'))

@app.route('/update-settings', methods=['POST'])
def update_settings():
    global AUTHORIZED_MATERIALS
    global status
    authorized_materials = request.form.get('authorized_materials').split(',')
    status = request.form.get('status')

    AUTHORIZED_MATERIALS = [material.strip() for material in authorized_materials]
    status = status
    socketio.emit('update_notification', {'message': 'Configurações atualizadas!'})
    return redirect(url_for('configurations'))

@app.route('/clear-settings', methods=['POST'])
def clear_settings():
    global AUTHORIZED_MATERIALS
    global status
    AUTHORIZED_MATERIALS = []  
    status = ""  
    return redirect(url_for('configurations')) 


def send_email_with_attachment(send_to, subject, body, file_path):

    
    msg = MIMEMultipart()
    msg['From'] = 'contato.paulooliver9@outlook.com'
    msg['To'] = send_to
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

   
    with open(file_path, "rb") as attachment:
        part = MIMEApplication(
            attachment.read(),
            Name=os.path.basename(file_path)
        )
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)

  
    server = smtplib.SMTP('smtp.office365.com', 587)
    server.starttls()
   
    server.login(msg['From'], 'Thivi8090p')  
    text = msg.as_string()
    server.sendmail(msg['From'], msg['To'], text)
    server.quit()



def create_pdf(store, material, description, quantity, authorized_by='Formulario Automizado'):
    temp_dir = '/tmp'
    filename = f'devolucao_{store}.pdf'
    file_path = os.path.join(temp_dir, filename)

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, "Autorização de Devolução")

    
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f'Loja: {store}')
    c.drawString(100, 730, f'Material: {material}')
    c.drawString(100, 710, f'Descrição: {description}')
    c.drawString(100, 690, f'Quantidade: {quantity}')
    c.drawString(100, 670, f'Autorizado por: {authorized_by}')

    
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2.0, 30, "Este documento é válido para a devolução dos materiais listados acima.")

   
    c.save()

    return file_path



def get_encoding(file_path):
    with open(file_path, 'rb') as file:
        return chardet.detect(file.read())['encoding']

    

def update_excel(store, material, description, quantity):
   
    source_filename = 'devolucao.xlsx'
    
   
    wb = load_workbook(source_filename)
    ws = wb.active
    
   
    ws['G7'] = store
    ws['C14'] = material
    ws['D14'] = description
    ws['H14'] = quantity
    ws['L14'] = "Robo"
    
    
    ws.protection = SheetProtection(sheet=True, password='thivi8090#', objects=True, scenarios=True)
    
    
    temp_dir = '/tmp'
    new_filename = os.path.join(temp_dir, f'devolucao_{store}.xlsx')
    wb.save(new_filename)
    
    send_to = 'paulo.cunha@hortifruti.com.br'
    subject = 'Planilha de Devolução'
    body = 'Aqui está a planilha de devolução solicitada.'
    send_email_with_attachment(send_to, subject, body, new_filename)
    
    return new_filename


    
@app.route('/get-description')
def get_description():
    material = request.args.get('material')
    description = ''
    authorized = material in AUTHORIZED_MATERIALS 

    if material:
        material = int(material)  
        description = materials.get(material, '')  

    return jsonify(description=description, authorized=authorized)



def get_stores():
    stores = []

    for store_name in lojas:
        stores.append(store_name)
    
    return stores



@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    stores = get_stores()

    if request.method == 'POST':
        store = request.form.get('store')
        material = request.form.get('material')
        quantity = request.form.get('quantity')
        description = request.form.get('description')

        new_filename = create_pdf(store, material, description, quantity)
        return send_file(new_filename, as_attachment=True, download_name=os.path.basename(new_filename))

    return render_template('index.html', message=message, stores=stores, status=status)







if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)