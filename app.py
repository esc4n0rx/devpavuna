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
from reportlab.lib.colors import HexColor
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
def create_pdf(store, material, description, quantity, authorized_by='Formulário Automatizado', motivo_devolucao='Envio errado'):
    # Configurações iniciais
    project_root_dir = '.'  
    filename = f'devolucao_{store}.pdf'
    file_path = os.path.join(project_root_dir, filename)
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter 


    #Configurar cor de fundo
    background_color = HexColor('#875742')  
    c.setFillColor(background_color)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Adicionar marca d'água
    c.setFont("Helvetica-Bold", 60)
    c.setFillAlpha(0.1)  # Torna a marca d'água menos opaca
    c.setFillColorRGB(0, 0, 0)  # Cor da marca d'água: preto
    c.drawCentredString(width / 2.0, height / 2.0, "PROIBIDO ALTERAR")

    
    # Restaurar a opacidade para o restante do texto
    c.setFillAlpha(1)
    c.setFillColorRGB(1, 1, 1) 


    # Adicionar logo
    #logo_path = os.path.join(project_root_dir, 'static/img/logo.png') 
    #c.drawImage(logo_path, 100, height - 100, width=2*inch, height=0.5*inch)

    # Configurar o título e subtitulo
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2.0, height - 120, "AUTORIZAÇÃO DE DEVOLUÇÃO DE MERCADORIA EM EXCEÇÃO")
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2.0, height - 140, "(Anexar junto à Nota Fiscal)")

    # Configurar informações da autorização
    today = datetime.now()
    max_date = today + timedelta(days=3)  
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 160, f'LOJA/UNIDADE: {store}')
    c.drawString(400, height - 160, f'DATA DA AUTORIZAÇÃO: {today.strftime("%d/%m/%Y")}')
    c.drawString(100, height - 180, f'DATA MÁXIMA PARA ENVIO: {max_date.strftime("%d/%m/%Y")}')

    # Configurar detalhes do produto
    c.drawString(100, height - 220, f'DESCRICÃO DO PRODUTO: {description}')
    c.drawString(100, height - 240, f'QUANTIDADE: {quantity}')
    c.drawString(400, height - 240, f'VALIDADE: {"-"}')  
    c.drawString(100, height - 260, f'LOTE: {"-"}')  #

    # Configurar autorização e motivo da devolução
    c.drawString(100, height - 280, f'DEVOLUÇÃO COM O FÍSICO: {"Sim"}')  
    c.drawString(100, height - 300, f'NOME DE QUEM AUTORIZOU: {authorized_by}')
    c.drawString(100, height - 320, f'QUEM AUTORIZOU CD OU COMERCIAL: {"CD"}')  
    c.drawString(100, height - 340, f'MOTIVO DEVOLUÇÃO: {motivo_devolucao}')

    # Configurar validação do documento
    c.setFont("Helvetica-Oblique", 10)
    footer_start_y_position = 100  
    c.drawString(50, footer_start_y_position, "1° O formulário deve seguir anexo.")
    c.drawString(50, footer_start_y_position - 15, "2° A quantidade informada deverá ser exata ao que constar no formulário.")
    c.drawString(50, footer_start_y_position - 30, "3° A mercadoria só poderá retornar ao CD se estiver íntegra.")

    # Finalizar e salvar o PDF
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