
# CRON SAMPLE ------------------------------------------------------------------- 
# /usr/bin/python /var/scripts/poller.py                            
# CRON SAMPLE -------------------------------------------------------------------


# LIBRARIES
import DB_OIDS as dev_list
import subprocess,os
from cryptography.fernet import Fernet

# ENCRYPTION KEY
fernet = Fernet(b'dzi31zMj3HqfNuHYW2a8rU8g66Ahtzno-Lc6BZweTpg=')

# CLEAR THE CMD
subprocess.run(['bash', '-c', 'clear'])

# DATABASE 
DB_ORG = dev_list.OIDS("192.168.33.1", "lemon", "frqAIRNAV", "snmp_monitoring", '192.168.34.1')


# GET ALL THE DEVICE LIST
for x in range(len(DB_ORG.DEVICES_LIST())):
    
    # THIS IS WHERE WE STORE THE LIST OF DEVICES
    DB_LISTER =     DB_ORG.DEVICES_LIST()[x]

    # STORE DEVICE CREDENTIALS 
    MODE = 1
    IP_ADD          = DB_LISTER['ip_address']
    USERNAME        = DB_LISTER['username']
    try:   # DECRYPT PASSWORD
        PASSWORD        = str(fernet.decrypt(DB_LISTER['snmp_password']).decode())
        AES_PASSWORD    = str(fernet.decrypt(DB_LISTER['snmp_aes_passwd']).decode())
        subprocess.run(['bash', '-c', "/usr/bin/python /var/scripts/indexv3.py '"+IP_ADD+"' '"+USERNAME+"' '"+PASSWORD+"' '"+AES_PASSWORD+"' "+str(MODE)+" &"])
    except:
           # PRINT IF THERE IS AN ERROR IN DECRYPTION PROCESS
           # DO NOTING
        print("Encryption ERROR for a Device with an IP Address of "+IP_ADD+"! Please Check the Database if there is a data that wasn't encrypted")
   
