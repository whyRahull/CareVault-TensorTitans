import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class MLServiceHealthView(APIView):
    """
    Check the health of the FastAPI ML Service.
    """
    permission_classes = [] # Allow anyone to check health (or restrict to authenticated if preferred)

    def get(self, request):
        from api.models.incidents import MLServiceConfig
        config = MLServiceConfig.get_solo()
        if not config:
            return Response({"status": "offline", "error": "No ML configuration found"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        ml_url = config.base_url.rstrip('/')
        health_endpoint = f"{ml_url}{config.health_path}"
        
        try:
            # Short timeout to avoid hanging the Django thread
            response = requests.get(health_endpoint, timeout=config.timeout_seconds)
            if response.status_code == 200:
                return Response({
                    "status": "online",
                    "details": response.json()
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "offline",
                    "error": f"ML Service returned status {response.status_code}"
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.RequestException as e:
            return Response({
                "status": "offline",
                "error": str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
