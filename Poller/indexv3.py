#------------------------------------------------------------------------------
# TEMPLATE FOR CALLING THIS SCRIPT
#------------------------------------------------------------------------------
#   $ /usr/bin/python /var/scripts/indexv3.py ARG1 ARG2 ARG3 ARG4 ARG5       
#
#   ARG1 = IP address of Device
#   ARG2 = SNMP Username
#   ARG3 = SNMP Password
#   ARG4 = SNMPv3 AES Password
#   ARG5 = Mode 0 | 1
#   MODE: 
#   0 - Insert and show only Basic System Desc (CPU, Memory, IP Address etc.)
#   1 - Insert complete Data (Basic System Desc and Interfaces Status)
#------------------------------------------------------------------------------


# LIBRARIES AND FRAMEWORKS
import subprocess, time, sys
from datetime import datetime
import DB_OIDS as dbs



# 1ST COUNTER TO MEASURE TOTAL THE TOTAL TIME FOR PROCCESING
t1 = time.perf_counter()



class SNMP_GET_DAT:
    def __init__(self, IP_ADD_, USERNAMES_, PASSWORD_, AES_PASS_, BASICS_ONLY=0):
       
        
        self.priv_ip      =   IP_ADD_               
        self.priv_user    =   USERNAMES_
        self.priv_pass    =   PASSWORD_
        self.priv_passAES =   AES_PASS_
        self.BASIC_DAT    =   BASICS_ONLY

        


         # TEMPORARY ------------- OIDS // DEFAULT
        self.D_ARR = [

            #--------------------------------------------------------------------------------------------
            #                       SINGLE CALL FUNCTION OID
            #--------------------------------------------------------------------------------------------               
            
            #           OID                     NAMES                   INDEX/POSITION

            ".1.3.6.1.4.1.9.9.109.1.1.1.1.5",      #CPU                    0
            ".1.3.6.1.4.1.9.9.48.1.1.1.5.1 ",      #USED MEM               1
            ".1.3.6.1.4.1.9.9.48.1.1.1.6.1 ",      #FREE MEM               2


            "1.3.6.1.2.1.4.20.1.1",                #IP ADDRESS             3
            "1.3.6.1.2.1.4.20.1.3",                #MASK                   4
            "1.3.6.1.2.1.1.5.0   ",                #HOST                   5


            ".1.3.6.1.2.1.1.1.0",                   #DESCRIPTION            6

            
            #---------------------------------------------------------------------------------------------
            #                        ARRAY TYPE OR HAVE SOME INDEXES
            #---------------------------------------------------------------------------------------------


            "1.3.6.1.2.1.2.2.1.2 ",                #PORT NAMES             7
            "1.3.6.1.2.1.2.2.1.2 ",                #PORT TYPE              8
            "1.3.6.1.2.1.2.2.1.7 ",                #ADMIN STATS            9
            "1.3.6.1.2.1.2.2.1.8 ",                #OPER STATS             10
            "1.3.6.1.2.1.2.2.1.10",                #BW IN                  11
            "1.3.6.1.2.1.2.2.1.16"                 #BW OUT                 12
                    
        ]

        # CONNECT TO DATABASE
        self.db_connect = dbs.OIDS("192.168.33.1", "lemon", "frqAIRNAV", "snmp_monitoring", self.priv_ip)
        try:
            # OIDS LIST 
            print(" OID ARE AVAILABLE AT " + self.priv_ip + " \n" )
            # print("CPU:                 " + self.db_connect.OID_MASTER['CPU'])
            # print("USED MEMORY:         " + self.db_connect.OID_MASTER['USED_MEM'])        
            # print("FREE MEMORY:         " + self.db_connect.OID_MASTER['FREE_MEM'])        

            # print("IP ADDRESS:          " + self.db_connect.OID_MASTER['IP_ADD'])        
            # print("SUBNET MASK:         " + self.db_connect.OID_MASTER['SMASK'])        
            # print("HOSTNAME:            " + self.db_connect.OID_MASTER['HOSTNAME'])        

            # print("DESCRIPTION:         " + self.db_connect.OID_MASTER['DESC'])        

            # print("PORTNAMES:           " + self.db_connect.OID_MASTER['PORT_N'])        
            # print("PORT TYPE:           " + self.db_connect.OID_MASTER['PORT_T'])        
            # print("ADMIN STATUS:        " + self.db_connect.OID_MASTER['ADMIN'])        
            # print("OPERATIONAL STATUS:  " + self.db_connect.OID_MASTER['OPER'])        
            # print("BANDWIDTH IN:        " + self.db_connect.OID_MASTER['BW_IN'])        
            # print("BANDWIDTH OUT:       " + self.db_connect.OID_MASTER['BW_OUT'])        
            

            # IDENTIFIER FOR DICTIONARY
            OID_LIST_DC = ["CPU", "USED_MEM", "FREE_MEM", "IP_ADD", "SMASK", "HOSTNAME", "DESC", "PORT_N", "PORT_T", "ADMIN", "OPER", "BW_IN", "BW_OUT"]

            # REPLACING THE DEFAULT OID FROM  DATABASE OID TABLES 
            for x in range(len(self.D_ARR)):
                res = str(self.db_connect.OID_MASTER[str(OID_LIST_DC[x])])
                self.D_ARR[x] = res
        

        except:
            # SENT A MESSAGE THAT THIS IP HAS MISSING OIDs AT DATABASE OID TABLE 
            print("\nWARNING: Some OIDs are missing at IP: "+str(self.priv_ip)+". Please complete them for the device.\n")        
            

        # GET THE TOTAL PORT FROM INDEXV2.SH
        self.TOTAL_PORTS =    int(self.BASH_Proccessor(1, self.priv_user, self.priv_pass, self.priv_passAES, self.priv_ip, self.D_ARR[7]).decode('utf-8'))   
        
        # IDENTIFIER FOR DICTIONARY
        self.dat_int_pointer_name = ["INT_NAME", "INT_TYPE", "INT_ADMIN", "INT_OPER", "INT_BW_IN", "INT_BW_OUT"]
        

        # EMPTY ARRAY (THIS IS WHERE WE STORE ALL THE BASIC SYSTEM DESC AND INTERFACE STATUS)
        self.SYSDESC_ARR = []

        # GET THE BASIC SYSTEM DESC BY CALLING THIS FUNCTION.
        self.SIMPLE_DESC()
        
        # DICTIONARY FOR THE DATA GATHERED
        self.dat = {
            "CPU": int(self.SYSDESC_ARR[0]),                            # CPU
            "USED_MEM": int(self.SYSDESC_ARR[1]),                       # USED MEMORY
            "FREE_MEM": int(self.SYSDESC_ARR[2]),                       # FREE MEMORY
            "IP_ADD": str(self.SYSDESC_ARR[3]).replace("\n"," "),        # IP ADDRESS
            "MASK": str(self.SYSDESC_ARR[4]).replace("\n"," "),          # SUBNET MASK
            "HOST": str(self.SYSDESC_ARR[5]).replace("\n"," "),          # HOSTNAME
            "DESC": str(self.SYSDESC_ARR[6]).replace("\n",""),          # COMPLETE DESCRIPTION
            "TOTAL_PORT": int(self.TOTAL_PORTS)                         # TOTAL NUMBER OF INTERFACE
            #"TIMESTAMP": str(datetime.now())
        }, {            
            "INT_NAME": [                                               # NAME OF INTERFACE
            ],
            "INT_TYPE": [                                               # TYPE OF INTERFACE
            ],
            "INT_ADMIN": [                                              # ADMIN STATUS
            ],
            "INT_OPER": [                                               # OPERATIONAL STATUS
            ],
            "INT_BW_IN": [                                              # BANDWIDTH IN
            ],
            "INT_BW_OUT": [                                             # BANDWIDTH OUT
            ]
        }
    
        # SETTER IF WE ONLY WANT TO SHOW BASIC SYSTEM DESC OR (SYSTEM DESC WITH INTERFACES STATUS)
        if self.BASIC_DAT != 0:                                         
           self.PORT_FUNC(self.TOTAL_PORTS)
        
       #/var/scripts/indexv2.sh 0 ADMIN '!frqAIRNAV' '!frqAIRNAV' 192.168.34.1 .1.3.6.1.2.1.1.1.0

        # 2ND COUNTER TO MEASURE TOTAL THE TOTAL TIME FOR PROCCESING
        t2 = time.perf_counter()
        print(str(self.SYSDESC_ARR[5]).replace("\n","") + ": Total Fetch Data 100 % ")
        print(str(self.SYSDESC_ARR[5]).replace("\n","") + ": Total time to complete: " + str(t2 - t1) + " seconds")

    # A FUNCTION WHICH CALLS THE BASH SCRIPT    
    def BASH_Proccessor(self, MODE_INT, USER_INT, PASS_INT, AES_PASS_INT, IP_ADD_INT, POS, INDEXED = ''):
        SCRIPT_INT  = str('/var/scripts/indexv2.sh '+ str(MODE_INT) + ' ' + USER_INT + ' ' + PASS_INT + ' ' + AES_PASS_INT + ' ' + IP_ADD_INT) 
        return subprocess.check_output(['bash', '-c', SCRIPT_INT + ' ' + POS + ' ' + INDEXED + ' &'])

    # FUNCTION - FETCH TO DATA FROM INTERFACES
    def PORT_FUNC(self, TOTAL_P):
        for PORTS_POS in range(int(TOTAL_P)):
            for HANDLER in range(7, 13):
                PORT_ = str(self.BASH_Proccessor(1, self.priv_user, self.priv_pass, self.priv_passAES, self.priv_ip, str(self.D_ARR[HANDLER]), str(PORTS_POS)).decode('utf-8')).replace("\n", "")
                self.dat[1][self.dat_int_pointer_name[HANDLER-7]].append(PORT_)
            print(str(self.SYSDESC_ARR[5]).replace("\n","")  +  ": Total Fetch Data " + str( int(float(float(PORTS_POS) / float(self.TOTAL_PORTS)) * 100) ) + " " + str() + " %                                      ", end="\r")
            
    #  GETTING FOF THE BASIC SYSTEM DESC. FROM BASH SCRIPT
    def SIMPLE_DESC(self):
        for i in range(7):
            self.SYSDESC_ARR.append(self.BASH_Proccessor(0, self.priv_user, self.priv_pass, self.priv_passAES, self.priv_ip, self.D_ARR[i]).decode('utf-8'))
      

#print(hello.OID_MASTER['DESC'])


# CHECK IF THERE IS AN ARGUMENTS
if len(sys.argv) > 1:
        CMD_IP          = sys.argv[1]
        CMD_USER        = sys.argv[2]
        CMD_PASS        = sys.argv[3]
        CMD_PASS_AES    = sys.argv[4]
        CMD_MODES       = int(sys.argv[5])         
          #SNMP_GET_DAT("10.11.1.1",  "admin", "frqAIRNAV", "frqAIRNAV")
        CALLER = SNMP_GET_DAT(CMD_IP, CMD_USER,CMD_PASS, CMD_PASS_AES, CMD_MODES)
        
        TIME_DELIVER = str(datetime.now().time())[:5]

        

        DEV_OWNER = str(CALLER.dat[0]["HOST"])
        print("\n\n")

        print(DEV_OWNER + " - Connection:")
        print(DEV_OWNER + " - UP TIME:         " + str(TIME_DELIVER))

        print(DEV_OWNER + " - IP:              " + CMD_IP)
        print(DEV_OWNER + " - USERNAME:        " + CMD_USER)
        print(DEV_OWNER + " - PASSWORD:        " + len(CMD_PASS)*"*")
        print(DEV_OWNER + " - AES PASSWORD:    " + len(CMD_PASS_AES)*"*")
      
        CALLER.db_connect.INSERT_NOW(str(TIME_DELIVER), "UP_TIME", 9999)

        # PRINT AND INSERT INTO DATABASE (SYSTEM DESC)
      #  print("---------------------------------------------------------------------------")
        print(DEV_OWNER + " - CPU Usage:       " + str(CALLER.dat[0]["CPU"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["CPU"], "CPU", 9999)

        print(DEV_OWNER + " - Uses Memory:     " + str(CALLER.dat[0]["USED_MEM"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["USED_MEM"], "USED_MEM", 9999)
        
        print(DEV_OWNER + " - Free Memory:     " + str(CALLER.dat[0]["FREE_MEM"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["FREE_MEM"], "FREE_MEM", 9999)
        
        print(DEV_OWNER + " - IP Address:      " + str(CALLER.dat[0]["IP_ADD"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["IP_ADD"], "IP_ADD", 9999)
        
        print(DEV_OWNER + " - Subnet Mask:     " + str(CALLER.dat[0]["MASK"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["MASK"], "SMASK", 9999)
        
        print(DEV_OWNER + " - Hostname:        " + str(CALLER.dat[0]["HOST"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["HOST"], "HOSTNAME", 9999)
        
        print(DEV_OWNER + " - Total Interface: " + str(CALLER.dat[0]["TOTAL_PORT"]))
        CALLER.db_connect.INSERT_NOW(str(CALLER.dat[0]["TOTAL_PORT"]), "TOTAL_PORT", 9999)
        
        print(DEV_OWNER + " - Description:     " + str(CALLER.dat[0]["DESC"]))
        CALLER.db_connect.INSERT_NOW(CALLER.dat[0]["DESC"], "DESC", 9999)
        print("\n\n")
     #   print("---------------------------------------------------------------------------")
        
        # PRINT AND INSERT INTO DATABASE (INTERFACES DATA)
        #print(DEV_OWNER + " - INTERFACES: ")
        if CMD_MODES == 1:
            for x in range(CALLER.TOTAL_PORTS):
                interface_name      = CALLER.dat[1]["INT_NAME"][x]
                interface_type      = CALLER.dat[1]["INT_TYPE"][x][:4]
                interface_admin     = CALLER.dat[1]["INT_ADMIN"][x]
                interface_OPER      = CALLER.dat[1]["INT_OPER"][x]
                interface_BW_IN     = CALLER.dat[1]["INT_BW_IN"][x]
                interface_BW_OUT    = CALLER.dat[1]["INT_BW_OUT"][x]
                CALLER.db_connect.INSERT_NOW(interface_type, "PORT_T", x)
                CALLER.db_connect.INSERT_NOW(interface_admin, "ADMIN", x)
                CALLER.db_connect.INSERT_NOW(interface_OPER, "OPER", x)
                CALLER.db_connect.INSERT_NOW(interface_name, "PORT_N", x)
                CALLER.db_connect.INSERT_NOW(interface_BW_IN, "BW_IN", x)
                CALLER.db_connect.INSERT_NOW(interface_BW_OUT, "BW_OUT", x)
                
       
                #print(DEV_OWNER + " - " + interface_name, interface_type, interface_admin, interface_OPER, interface_BW_IN, interface_BW_OUT, " -- PORT : " + str(x))
         #   print("---------------------------------------------------------------------------")
else:
    #/usr/bin/python /var/scripts/indexv3.py 'IP ADDRESS' 'USERNAME' 'PASSWORD' 'AES PASSWORD' 'MODE (0 = BASIC | 1 = COMPLETE)'
    subprocess.run(['bash', '-c', 'clear'])
    print("\n\n\n ERROR: Please Complete the prompt: ")        
    print(" SAMPLE: /usr/bin/python /var/scripts/indexv3.py ARG1 ARG2 ARG3 ARG4 ARG5\n")       
    print(" ARG1 = IP address of Device")
    print(" ARG2 = SNMP Username")
    print(" ARG3 = SNMP Password")
    print(" ARG4 = SNMPv3 AES Password")
    print(" ARG5 = Mode 0 | 1")
    print("\n MODE: ")
    print(" 0 - Insert and show only Basic System Desc (CPU, Memory, IP Address etc.)")
    print(" 1 - Insert complete Data (Basic System Desc and Interfaces Status)\n\n\n")