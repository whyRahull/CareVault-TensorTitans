import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from api.models.incidents import MLServiceConfig

class HandSOSImageDetectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('file')
        if not image_file:
            return Response({'error': 'Image file is required'}, status=400)

        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}/api/hand_sos/detect"

        try:
            files = {'file': (image_file.name, image_file.read(), image_file.content_type)}
            resp = requests.post(ml_url, files=files, timeout=config.timeout_seconds)
            resp.raise_for_status()
            return Response(resp.json())
        except Exception as e:
            return Response({'error': f"ML Service error: {str(e)}"}, status=503)
