""" This script discovers a network device via ICMP and SNMP
    using the system's commands via subprocess """

# ----- How to use -----
# Go to the directory where the script is located
# Run the command below using the appropriate IP ADDRESS and SNMPv3 credentials
# python3 discover_device.py <SNMP_USER> <AUTH_PASS> <PRIV_PASS> <IP_ADDRESS>
# ----- Examples -----
# Router A
# python3 discover_device.py ADMIN '!frqAIRNAV' '!frqAIRNAV' 192.168.34.1
# Router B
# python3 discover_device.py admin '!frqAIRNAV' '!frqAIRNAV' 192.168.33.254
# Switch A
# python3 discover_device.py admin 'frqAIRNAV' 'frqAIRNAV' 10.11.1.1
# Switch B
# python3 discover_device.py switchB '!frqAIRNAV' '!frqAIRNAV' 192.168.32.2

# Import necessary libraries
import subprocess
import re
import json
import sys

# --- CONFIGURATION ---
SNMP_USER = "ADMIN"
AUTH_PASS = "!frqAIRNAV"   # The actual, plaintext Auth Password
PRIV_PASS = "!frqAIRNAV"   # The actual, plaintext Priv Password
AUTH_PROTO = "sha"
PRIV_PROTO = "aes"
SEC_LEVEL = "authPriv"
# ---------------------------------------------------------------------------------

def run_ping(ip_address):
    """Pings the IP address using the native Linux 'ping' command."""
    # Output: (success: bool, message: str)

    print(f"Pinging {ip_address}...")
    # Ping 3x (-c 3) and wait 10 second for timeout (-w 10)
    command = ['ping', '-c', '3', '-w', '10', ip_address]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        
        # Check for 0% packet loss (or similar success message)
        if "0 received" in result.stdout or result.returncode != 0:
            return False, "Device is unreachable via ICMP (ping failed)."
        
        return True, "Device is reachable."
    except Exception as e:
        return False, f"Ping command execution error: {e}"

def run_snmp(snmp_command, snmp_user, auth_pass, priv_pass, ip_address, oid):
    """Runs snmpget with the SNMPv3 credentials to retrieve a value and its type."""
    # Output: (value, type)
    # This relies on AlmaLinux host having the snmpget tool and MIBs configured.

    if snmp_command.lower() not in ['snmpget', 'snmpgetnext', 'snmpwalk']:
        return f"SNMP Error: Invalid SNMP command: {snmp_command}", None

    command = [
        snmp_command, '-v', '3',
        '-l', SEC_LEVEL,
        # '-u', SNMP_USER,
        '-u', snmp_user,
        '-a', AUTH_PROTO,
        # '-A', AUTH_PASS, # Plaintext password
        '-A', auth_pass, # Plaintext password
        '-x', PRIV_PROTO,
        # '-X', PRIV_PASS, # Plaintext password
        '-X', priv_pass, # Plaintext password
        '-r', '3',  # Retry count
        '-t', '5',  # Timeout in seconds
        ip_address,
        oid
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            # Return detailed error for debugging
            return f"SNMP Error: {result.stderr.strip()}", None
        
        # Parsing output if command is SNMPGET
        if command[0] == 'snmpget' or command[0] == 'snmpgetnext':
            # Regex pattern: "=<group1>:<group2>" (e.g., 'OID: cisco2811' or 'STRING: Hostname')
            match = re.search(r'=\s+(.*?):\s+(.*)', result.stdout.strip())
            if match:
                # Group 1 is the type (e.g., STRING), Group 2 is the value
                return match.group(2).strip().strip('"'), match.group(1).strip().strip('"')
            return "SNMP Error: No OID Found", None
        
        # Parsing output if command is SNMPWALK
        elif command[0] == 'snmpwalk':
            output_lines = result.stdout.strip().split('\n')
            extracted_data = []

            # Process each line of the SNMPWALK output
            for line in output_lines:
                if not line.strip() or "No Such Object" in line:
                    continue
                
                # Regex to match the part after the colon and space (e.g., 'STRING: FastEthernet0/0')
                match = re.search(r':\s+(.*)', line.strip())
                if match:
                    value = match.group(1).strip().strip('"')
                    extracted_data.append(value)

            if not extracted_data:
                return "SNMP Error: No values found for OID.", None
             
        return extracted_data, "LIST"

    except subprocess.TimeoutExpired:
        return "Subprocess Error: SNMP Timeout", None
    except Exception as e:
        return f"Subprocess Error: {e}", None

def discover_device(snmp_user, auth_pass, priv_pass, ip_address):
    """Main function to orchestrate ping and SNMP discovery."""
    
    # 1. ICMP Ping Check
    ping_success, ping_message = run_ping(ip_address)
    if not ping_success:
        return {"status": "error", "message": ping_message}

    # 2.  SNMP Data Gathering
    # 2.1 Define OIDs to query
    sys_object_id = "1.3.6.1.2.1.1.2.0"                 # Device Model
    sys_name = "1.3.6.1.2.1.1.5.0"                      # Hostname
    applicable_measurement_oid = {
        # OIDs below are for snmpgetnext
        "cpu_usage": "1.3.6.1.4.1.9.9.109.1.1.1.1.5",  # CPU % usage in the last 5 mins
        "memory_free": "1.3.6.1.4.1.9.9.48.1.1.1.6",   # Free memory in Bytes
        "memory_used": "1.3.6.1.4.1.9.9.48.1.1.1.5",   # Used memory in Bytes
    }
    available_interfaces = "1.3.6.1.2.1.2.2.1.2"       # List of interface names
    if_admin_oid = "1.3.6.1.2.1.2.2.1.7"     # Admin status of interfaces
    if_oper_oid = "1.3.6.1.2.1.2.2.1.8"      # Operational status of interfaces

    # 2.2 SNMP Polling for system info
    print("Gathering SNMP data...")
    model_id_value, _ = run_snmp("snmpget", snmp_user, auth_pass, priv_pass, ip_address, sys_object_id)
    if "Error" in model_id_value:
        return {
            "status": "error",
            "message": "SNMP Error during Model ID retrieval.",
            "details": model_id_value  # Pass the specific error message here
        }
    hostname_value, _ = run_snmp("snmpget", snmp_user, auth_pass, priv_pass, ip_address, sys_name)
    if "Error" in hostname_value:
        return {
            "status": "error",
            "message": "SNMP Error during Hostname retrieval.",
            "details": hostname_value  # Pass the specific error message here
        }
    hostname_value = hostname_value.split(".")[0]  # Get only the first part of the hostname
    
    # 2.3 SNMP Polling for Applicable Measurements
    print("Gathering Applicable Measurements...")
    applicable_measurements = {}
    for measurement, oid in applicable_measurement_oid.items():
        m_value, m_type = run_snmp("snmpgetnext", snmp_user, auth_pass, priv_pass, ip_address, oid)
        applicable_measurements[measurement] = {
            "value": m_value,
            "type": m_type
        }
        if "Error" in m_value:
            applicable_measurements[measurement]["note"] = "Measurement not available or SNMP error."
            break

    # 2.4 SNMP Polling for Available Interfaces
    print("Gathering Available Interfaces...")
    interface_list, _ = run_snmp("snmpwalk", snmp_user, auth_pass, priv_pass, ip_address, available_interfaces)
    interface_admin_status, _ = run_snmp("snmpwalk", snmp_user, auth_pass, priv_pass, ip_address, if_admin_oid)
    interface_oper_status, _ = run_snmp("snmpwalk", snmp_user, auth_pass, priv_pass, ip_address, if_oper_oid)

    # 3. Return Discovery Results
    return {
        "status": "OK",
        "data": {
            "ip_address": ip_address,
            "model_id_raw": model_id_value,
            "hostname": hostname_value,
            "applicable_measurements": applicable_measurements,
            "interfaces": {
                "names": interface_list,
                "admin_status": interface_admin_status,
                "oper_status": interface_oper_status
            }
        }
    }

if __name__ == '__main__':
    # Test execution when run from the command line

    if len(sys.argv) < 5:
        print("Usage: python3 discover_device.py <SNMP_USER> <AUTH_PASS> <PRIV_PASS> <IP_ADDRESS>")
        sys.exit(1)

    snmp_user = sys.argv[1]
    auth_pass = sys.argv[2]
    priv_pass = sys.argv[3]
    target_ip = sys.argv[4]
    results = discover_device(snmp_user, auth_pass, priv_pass, target_ip)
    print("\n--- DISCOVERY RESULTS ---")
    print(json.dumps(results, indent=4))
    print("-------------------------")