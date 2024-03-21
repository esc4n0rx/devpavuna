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



app = Flask(__name__)



AUTHORIZED_MATERIALS = ['100000']


def send_email_with_attachment(send_to, subject, body, file_path):

    #ALTERAR
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



def get_encoding(file_path):
    with open(file_path, 'rb') as file:
        return chardet.detect(file.read())['encoding']

    

def update_excel(store, material,description, quantity):
    filename = 'devolucao.xlsx' 
    wb = load_workbook(filename)
    ws = wb.active  

    ws['G7'] = store
    ws['C14'] = material
    ws['D14'] = description
    ws['H14'] = quantity
    ws['L14'] = "Robo"


    ws.protection = SheetProtection(sheet=True, password='thivi8090#', objects=True, scenarios=True)

   
    new_filename = f'devolucao_{store}.xlsx'
    wb.save(new_filename)
    


    #ALTERAR
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

    
    status = "Atenção Devolver com o Físico"

    if request.method == 'POST':
        store = request.form.get('store')
        material = request.form.get('material')
        quantity = request.form.get('quantity')
        description = request.form.get('description')
        print(f"Received description: {description}")

        new_filename = update_excel(store, material, description, quantity) 
        return send_file(new_filename, as_attachment=True, download_name=new_filename)

    return render_template('index.html', message=message, stores=stores, status=status)


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=5000)
