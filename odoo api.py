from queue import Empty
import xmlrpc
from xmlrpc import client
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ssl import SSLCertVerificationError, SSLContext
from re import search
from datetime import date
import datetime
import json


production_api_key = "bf4fd965a1f8e2da56f62162d790d06cd5360620"
stg_api_key = "446e6350f18b7454ad9e9a5b14d869b22c8a7b1f"
url_stg = "https://sbx-nksgroup.odoo.com"
db_stg = 'sbx-6699871'
username = 'waldemar.lusiak@nksgroup.pl'
password = ''

serial_number = '76901T21600050'
status_pass = 'PASS'
status_fail = 'FAIL'


def fail_log_email(*serial_scrapped, raspi_softer_number):
    passed_record = serial_scrapped
    raspi_softer_number = "Raspisofter 001"
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "waldemar.lusiak@nksgroup.pl"  # Enter your address
    receiver_email = "waldemar.lusiak@nksgroup.pl"  # Enter receiver address , admin@onservice.pl, remigiusz.zerbst@nksgroup.pl
    password = ''
    subject = 'Error occured during software update on {}'.format(raspi_softer_number)
    message = """
    <Subject: {}>
    This is automatically generated message please do not answer to it.
    
    The problem occured in: {} or it is related to it.""".format(subject, passed_record) #w nawiasach zamieniamy na zmienną którą chcemy przekazać w emailu

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email.split(','), message, subject)


common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_stg))
uid = common.authenticate(db_stg, username, password, {})
#print("UID ", uid)

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_stg))


#create_record = models.execute_kw(db_stg, uid, password, 'res.partner', 'create', [{'name': 'testowy insert'}])
#print(create_record)
#write_record = models.execute_kw(db_stg, uid, password, 'stock.production.lot', 'write', [[58278], {'name': '76901T21600050'}])
# write powyzej zmienia nazwe w rekordzie modelu stock.production.lot nazwę lot/serial number
#print(write_record)
#fail_log_email()


def get_odoo_id(serial_scrapped): 
    try:
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_stg))
        uid = common.authenticate(db_stg, username, password, {})
        #print("UID ", uid)
        search_odoo_record = models.execute_kw(db_stg, uid, password, 'stock.production.lot', 'search_read', [[
            ['name', '=', serial_scrapped]]], 
            {'fields': ['name', 'id', 'product_qty']})
        for dictionary in search_odoo_record:
            serial_odoo_id = dictionary.get('id')
            return serial_odoo_id 
       
    except Exception as e:
        raise(fail_log_email(e.__class__))
    
    finally:
        common.logout()

#serial_scrapped = '64601T0260040'
#serial_odoo_id = get_odoo_id(serial_scrapped)
#print(serial_odoo_id)


def create_log_in_LogsCollector(odoo_serial, test_result,software_information, raspi_softer_number,log_date):
    try:
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_stg))
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_stg))
        uid = common.authenticate(db_stg, username, password, {})
        #print("UID ", uid)
        create_record = models.execute_kw(db_stg, uid, password, 'logs.collector', 'create', [{
            'x_log_serial': odoo_serial,
            'x_log_datein': log_date,
            'x_log_testresult': test_result,
            'x_log_testdetails': software_information,
            'x_log_subuser': raspi_softer_number                  
            }])    
        
        
    except Exception as e:
        raise(fail_log_email(e.__class__))
    
    finally:
        common.logout()
    
test_result = "FALSE"
odoo_serial = 'RAZ DWA TRZY'
software_information = "software_ver=ST6840_VTX_1.0.0.008"
raspi_softer_number = "Raspisofter 001"
now = datetime.datetime.now()
log_date = now.strftime("%d/%m/%Y")

#create_log_in_LogsCollector(odoo_serial, test_result,software_information, raspi_softer_number,log_date)


def veryfi_odoo_serial(odoo_serial):
    try:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_stg))
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_stg))
        uid = common.authenticate(db_stg, username, password, {})
        print("UID ", uid)
        list_record = models.execute_kw(db_stg, uid, password, 'logs.collector', 'search_read', [[['x_log_serial', '=', odoo_serial] and ['x_log_testresult', '=', test_result]]], {'fields': ['x_log_serial', 'x_log_datein','x_log_testresult', 'x_log_testdetails','x_log_subuser']})
        print(list_record)
        
        return odoo_serial
    except Exception as e:
        raise(fail_log_email(e.__class__))
    
    finally:
        common.logout()

    

#odoo_serial = '64601T0260040'

#veryfi_odoo_serial(odoo_serial)



# Funkcja szuka w mrp.production produktów z state done, gdzie product id równy jest PC0 oraz lot_producing_id jest przyjetym numerem seryjnym jako argument funkcji.
# W return dostajemy 

def get_odoo_MO_value(odoo_serial): 
    try:
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_stg))
        uid = common.authenticate(db_stg, username, password, {})
        search_odoo_record = models.execute_kw(db_stg, uid, password, 'mrp.production', 'search_read', [['&',
            ['state', '!=', 'done'], ['product_id', 'like', 'PC0'], ['lot_producing_id', '=', odoo_serial]]], 
            {'fields': ['name', 'id', 'bom_id', 'move_raw_ids']})

        for item in search_odoo_record:
            move_raw_ids = item.get('move_raw_ids')
            first_id = move_raw_ids[0]
            second_id = move_raw_ids[1]   
            
            return first_id, second_id 
        
    except Exception as e:
        print(e)
        
    finally:
        common.logout()



odoo_serial = 'LM65T22470197'
get_tuple = get_odoo_MO_value(odoo_serial)
print(type(get_tuple))