import pymysql, subprocess, time
from datetime import datetime

#subprocess.run(['bash', '-c', 'clear'])

class OIDS:
    def __init__(self, host_ip, user, passwd, db, ip):
        self.host = host_ip
        self.user = user
        self.passwd = passwd
        self.db = db
        self.ip = ip
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=self.db, cursorclass=pymysql.cursors.DictCursor)
        
        self.OID_MASTER = {}
        self.TIMEDATE = datetime.now()


        # GET ALL THE LIST OF OIDS FROM DATABASE OID TABLE
        # LIST OF OID WILL DEPENDS ON IP ADDRESS
        try:
            with self.conn.cursor() as cursor:
                sql = "SELECT model_id FROM snmp_monitoring.monitoring_device WHERE ip_address= '" + str(self.ip) + "';"
                cursor.execute(sql)
                self.result = cursor.fetchone()["model_id"]

                sql_OID = "SELECT oid,metric_id FROM snmp_monitoring.monitoring_oidmap where model_id= "+ str(self.result) +"; "
                cursor.execute(sql_OID)
                self.OID_LIST = cursor.fetchall()

                    
                for OIDS in self.OID_LIST:
                    
                    if OIDS['metric_id'] == 1 :                                                 # CPU
                        self.OID_MASTER['CPU'] = OIDS['oid']
                    elif OIDS['metric_id'] == 2:                                                # USED MEM
                         self.OID_MASTER['USED_MEM'] = OIDS['oid']
                    elif OIDS['metric_id'] == 3:                                                # FREE MEM
                         self.OID_MASTER['FREE_MEM'] = OIDS['oid']
                    elif OIDS['metric_id'] == 4:                                                # DESC
                         self.OID_MASTER['DESC'] = OIDS['oid']
                    elif OIDS['metric_id'] == 16:                                               # IP ADD
                        self.OID_MASTER['IP_ADD'] = OIDS['oid']
                    elif OIDS['metric_id'] == 6:                                                # ADMIN
                         self.OID_MASTER['ADMIN'] = OIDS['oid']
                    elif OIDS['metric_id'] == 17:                                               # SUBNET MASK
                         self.OID_MASTER['SMASK'] = OIDS['oid']
                    elif OIDS['metric_id'] == 8:                                                # OPER
                         self.OID_MASTER['OPER'] = OIDS['oid']
                    elif OIDS['metric_id'] == 18:                                               # HOSTNAME
                         self.OID_MASTER['HOSTNAME'] = OIDS['oid']
                    elif OIDS['metric_id'] == 19:                                               # PORT NAME
                         self.OID_MASTER['PORT_N'] = OIDS['oid']
                    elif OIDS['metric_id'] == 20:                                               # PORT TYPE
                         self.OID_MASTER['PORT_T'] = OIDS['oid']
                    elif OIDS['metric_id'] == 12:                                               # BW IN
                        self.OID_MASTER['BW_IN'] = OIDS['oid']
                    elif OIDS['metric_id'] == 13:                                               # BW OUT
                        self.OID_MASTER['BW_OUT'] = OIDS['oid']
                    else: 
                        print("ERROR OID NOT VALID:" + OIDS['oid'])

        except:
             print(" No Device Detected!")       

        
        # KEEP DATABASE OPEN!


    # THIS FUNCTION IS RESPONSIBLE FOR INSERTING DATA INSIDE THE DATABASE HISTORY
    def INSERT_NOW(self, VAL, OID_TYPE, INT_TYPE="NULL"):
      #  try:
            with self.conn.cursor() as cursor:
                #METRIC ID
                OID_TYPE_TABLE = {
                    "CPU": 1,
                    "USED_MEM": 2,
                    "FREE_MEM": 3,
                    "DESC": 4,
                    "IP_ADD": 16,
                    "ADMIN": 6,
                    "SMASK": 17,
                    "OPER": 8,
                    "HOSTNAME": 18,
                    "PORT_N": 19,
                    "PORT_T": 20,
                    "BW_IN": 12,
                    "BW_OUT": 13, 

                    "TOTAL_PORT": 5
                }

                #print(VAL, OID_TYPE_TABLE[str(OID_TYPE)])
                sql = "SELECT model_id FROM snmp_monitoring.monitoring_device WHERE ip_address= '" + str(self.ip) + "';"
                cursor.execute(sql)
                self.INSERTER_MODEL_ID = cursor.fetchone()["model_id"]
                sql = "SELECT id FROM snmp_monitoring.monitoring_device WHERE model_id="+str(self.INSERTER_MODEL_ID)+";"
                cursor.execute(sql)
                self.INSERTER_DEVICE_ID = cursor.fetchone()["id"]
                
                sql = "INSERT INTO snmp_monitoring.monitoring_history (value, `timestamp`, device_id, interface_id, metric_id) VALUES('" + str(VAL) + "', '" + str(self.TIMEDATE) + "', "+ str(self.INSERTER_DEVICE_ID) + ", "+str(INT_TYPE)+", "+ str(OID_TYPE_TABLE[OID_TYPE]) +");"
                stat = cursor.execute(sql)
                self.conn.commit()
                #print(stat)

       # finally:
           # print("DB STILL RUNNING")
            #self.conn.close()

    # DEVICE 
    def DEVICES_LIST(self):
        with self.conn.cursor() as cursor:
            sql = "SELECT ip_address, snmp_aes_passwd, username, snmp_password FROM snmp_monitoring.monitoring_device;"        
            cursor.execute(sql)

            self.DEVICES_MOD = cursor.fetchall()
            return self.DEVICES_MOD
            #print(self.DEVICES_MOD)
        




#db_connect = OIDS("192.168.33.1", "lemon", "frqAIRNAV", "snmp_monitoring", '192.168.34.1')



        