from flask import Flask, render_template, request, redirect, url_for,jsonify
from flask import send_file
from werkzeug.utils import secure_filename, safe_join
import csv
import os
from openpyxl import load_workbook
from openpyxl.worksheet.protection import SheetProtection


app = Flask(__name__)



AUTHORIZED_MATERIALS = ['100000']



def save_to_csv(data):
    file_exists = os.path.isfile('base.csv')
    entry_exists = False
    new_data = [data['store'], data['material'], data['description'], str(data['quantity'])]  
    if file_exists:
        with open('base.csv', mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                
                if row == new_data:
                    entry_exists = True
                    break

    if not entry_exists:
        with open('base.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['store', 'material', 'description', 'quantity'])  
            writer.writerow(new_data)
        return False  
    else:
        return True 
    

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
    return new_filename  


    
@app.route('/get-description')
def get_description():
    material = request.args.get('material')
    description = ''  
    authorized = material in AUTHORIZED_MATERIALS  
    with open('banco_dados.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0].strip() == material:
                description = row[1]
                break
    return jsonify(description=description, authorized=authorized)

def get_stores():
    stores = []
    with open('loja.csv', mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            stores.append(row[0])
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

        data = {'store': store, 'material': material, 'description': description, 'quantity': quantity}

        if not save_to_csv(data):  
            new_filename = update_excel(store, material, description, quantity)

            return send_file(new_filename, as_attachment=True, download_name=new_filename)
        else:
            message = 'Registro já existente.'

    return render_template('index.html', message=message, stores=stores,status=status)



if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=5000)
