import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .discover_device import discover_device # Import the function from the new script file

@csrf_exempt # Allows POST requests from the React frontend without a CSRF token
@require_http_methods(["POST"])
def device_discovery_api(request):
    """
    Receives SNMPv3 credentials and IP, executes the Python discovery script, 
    and returns the JSON result.
    """
    print("Received device discovery request.")
    # 1. Check the request type
    if request.content_type != 'application/json':
        return JsonResponse(
            {"status": "error", "message": "Invalid Content-Type. Must be application/json."}, 
            status=415 # Unsupported Media Type
        )

    try:
        # 2. Parse incoming JSON data
        data = json.loads(request.body.decode('utf-8'))
        
        ip_address = data.get('ipAddress')
        username = data.get('username')
        auth_password = data.get('authPassword')
        priv_password = data.get('privPassword')

        # Basic input validation
        if not all([ip_address, username, auth_password, priv_password]):
            return JsonResponse(
                {"status": "error", "message": "Missing required credentials or IP address."}, 
                status=400
            )

        # 3. Execute the discovery script function
        discovery_results = discover_device(
            username, 
            auth_password, 
            priv_password, 
            ip_address
        )

        # 4. Return results to the frontend
        if discovery_results.get("status") == "error":
            # If the script returned an error, return a server-side error status
            return JsonResponse(discovery_results, status=500)
        
        return JsonResponse(discovery_results, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format in request body."}, status=400)
    except Exception as e:
        # Catch any unexpected Python errors during script execution
        print(f"Error during device discovery: {e}")
        return JsonResponse({"status": "error", "message": f"Server processing error: {e}"}, status=500)