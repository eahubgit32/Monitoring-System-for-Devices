#     MANAGE AND RUN SNMPWALK
#------------------------------------------------------------------------------
# TEMPLATE FOR CALLING THIS SCRIPT
#------------------------------------------------------------------------------
# FUNC_SELECTOR ARG1 ARG2 ARG3 ARG4 ARG5 ARG6 ARG7
# ARG1 - Selection Mode 
#           0 - SINGLE CALL (CPU, MEM, DESC)
#           1 - MULTI ( PORT NAMES, TYPE, BW )
# ARG2 - SNMP Username
# ARG3 - SNMP Password
# ARG4 - SNMP Password for V3
# ARG5 - INDEX 
# ARG6 - IP ADDRESS
# ARG7 - Mode 1 Index (FOR ARG1 = 1)
#------------------------------------------------------------------------------





# FUNCTIONS THAT FETCH CPU, MEM,and NETWORK DETAILS.

sysdesc_func() {
     if [ "$5" = '.1.3.6.1.2.1.1.1.0' ]; then # SEPARATE THE DESCRIPTION SINCE IT HAS VERY LONG STRING/TEXT OUTPUT
        snmpwalk -v3 -l authPriv -u $1 -a sha -A $2 -x AES -X  $3 $4 $5
     else                  # FILTER OUT OR RETRIEVE ONLY THE OUTPUT NUMERICAL DATA
        snmpwalk -v3 -l authPriv -u $1 -a sha -A $2 -x AES -X  $3 $4 $5 | awk '{print $4}'
    fi
}


# TOTAL NUMBER OF PORTS
COUNT=0;

#  THIS IS WHERE WE STORE THE ARRAYS OF DATA OF INTERFACES
GENERAL_ARR=();


port_details() {
    SNMP_WALK_CALLER=$(snmpwalk -v3 -l authPriv -u $1 -a sha -A $2 -x AES -X  $3 $4 $5 | awk '{print $4}' & )
    if [ "$5" = 8 ]; then
        for PORT_N in $SNMP_WALK_CALLER
            do  
                #((COUNT++));
                #FILTER FOR GETTING THE TYPE OF MODE OR INTERFACE 
                GENERAL_ARR+=(${PORT_N:0:4});
            done
    else 
        for PORT_N in $SNMP_WALK_CALLER
            do
                ((COUNT++)); # COUNTS THE NUMBER OF INTERFACES
                GENERAL_ARR+=($PORT_N); # STORE IN THE ARRAY THE GATHERED DATA
            done
    fi
    
    if [ -z "$6" ]; then 
        #IF WE DIDN'T SPECIFY WHAT INDEX OF INTERFACE WE WANT TO GET WE WILL RECEIVE THE NUMBER OF INTERFACES
        echo $COUNT 
    else
        #RETURN THE VALUE OF  
        echo ${GENERAL_ARR["$6"]}
    fi

}



FUNC_SELECTOR() {
    if [ "$1" = 0 ]; then
        sysdesc_func $2 $3 $4 $5 $6
    elif [ "$1" = 1 ]; then
        port_details $2 $3 $4 $5 $6 $7
    else 
        echo "No Function Exist!";
    fi
}

FUNC_SELECTOR $1 $2 $3 $4 $5 $6 $7





