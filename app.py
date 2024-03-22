from flask import Flask, render_template, request, redirect, url_for,jsonify
from flask import send_file
from werkzeug.utils import secure_filename, safe_join
import os
import smtplib
from datetime import datetime, timedelta
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
from configs import EMAIL_SETTINGS


app = Flask(__name__)
socketio = SocketIO(app)


AUTHORIZED_MATERIALS = []  
status = "" 



#ROTA DE CONFIGURAÇOES
@app.route('/config', methods=['GET'])
def configurations():
   
    return render_template('config.html', authorized_materials=', '.join(AUTHORIZED_MATERIALS), status=status)


#FUNção DE VERIFICAR SENHA
@app.route('/check-password', methods=['POST'])
def check_password():
    password = request.form.get('password')
    if password == '2024': 
        return redirect(url_for('configurations')) 
    else:
        return redirect(url_for('index', message='Senha incorreta!'))


#FUNção DE ATUALIZAR CONFIGURAÇOES DE ITENS E STATUS
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


#FUNÇÃO DE LIMPAR CONFIGURAÇOES
@app.route('/clear-settings', methods=['POST'])
def clear_settings():
    global AUTHORIZED_MATERIALS
    global status
    AUTHORIZED_MATERIALS = []  
    status = ""  
    return redirect(url_for('configurations')) 



#FUNção DE ENVIO DE E-MAIL
def send_email_with_attachment(send_to, subject, body, file_path):
    email_user = EMAIL_SETTINGS['EMAIL_USER']
    email_password = EMAIL_SETTINGS['EMAIL_PASSWORD']
    smtp_server = EMAIL_SETTINGS['SMTP_SERVER']
    smtp_port = EMAIL_SETTINGS['SMTP_PORT']

    msg = MIMEMultipart()
    msg['From'] = email_user
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

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, msg['To'], text)
    server.quit()


#FUNÇÃO PARA CRIAR O PDF DE AUTORIZAÇÃO DA LOJA
def create_pdf(store, material, description, quantity, authorized_by='Formulário Automatizado'):
    project_root_dir = '.'  
    filename = f'devolucao_{store}.pdf'
    file_path = os.path.join(project_root_dir, filename)
    
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    
    logo_path = os.path.join(project_root_dir, 'static/img/basepdf.png')
    logo_size = 50
    c.drawImage(logo_path, 100, height - 40, width=logo_size, height=logo_size, preserveAspectRatio=True)

   
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 70, "AUTORIZAÇÃO DE DEVOLUÇÃO DE MERCADORIA EM EXCEÇÃO")
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2.0, height - 90, "(Anexar junto à Nota Fiscal)")

    
    today = datetime.now()
    max_date = today + timedelta(days=3)
    date_format = "%d/%m/%Y"
    
    
    content_start_y_position = height - 130
    line_spacing = 18  

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2.0, content_start_y_position, f'Loja: {store}')
    c.drawCentredString(width / 2.0, content_start_y_position - line_spacing, f'Material: {material}')
    c.drawCentredString(width / 2.0, content_start_y_position - 2 * line_spacing, f'Descrição: {description}')
    c.drawCentredString(width / 2.0, content_start_y_position - 3 * line_spacing, f'Quantidade: {quantity}')
    c.drawCentredString(width / 2.0, content_start_y_position - 4 * line_spacing, f'Autorizado por: {authorized_by}')
    c.drawCentredString(width / 2.0, content_start_y_position - 5 * line_spacing, f'Data da Autorização: {today.strftime(date_format)}')
    c.drawCentredString(width / 2.0, content_start_y_position - 6 * line_spacing, f'Data Máxima para Envio: {max_date.strftime(date_format)}')

   
    c.setFont("Helvetica-Oblique", 10)
    footer_y_position = 30
    c.drawCentredString(width / 2.0, footer_y_position, "Este documento é válido para a devolução dos materiais listados acima.")

    
    c.save()

    print(f"Arquivo PDF gerado: {file_path}")
    return file_path

  
#FUNÇÃO QUE RETORNA A DESCRISÃO DO MATERIAL 
@app.route('/get-description')
def get_description():
    material = request.args.get('material')
    description = ''
    authorized = material in AUTHORIZED_MATERIALS 

    if material:
        material = int(material)  
        description = materials.get(material, '')  

    return jsonify(description=description, authorized=authorized)


#FUNção QUE RETORNA AS LOJAS
def get_stores():
    stores = []

    for store_name in lojas:
        stores.append(store_name)
    
    return stores


#ROTA PRINCIPAL
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