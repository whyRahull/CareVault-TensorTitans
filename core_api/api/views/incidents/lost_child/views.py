import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from api.models.incidents import MLServiceConfig, MissingPerson

class LostChildImageSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('file')
        person_id = request.data.get('person_id')
        if not image_file:
            return Response({'error': 'Image file is required'}, status=400)

        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}/api/lost_child/search"
        if person_id:
            ml_url = f"{ml_url}?person_id={person_id}"

        try:
            files = {'file': (image_file.name, image_file.read(), image_file.content_type)}
            resp = requests.post(ml_url, files=files, timeout=config.timeout_seconds)
            resp.raise_for_status()
            return Response(resp.json())
        except Exception as e:
            return Response({'error': f"ML Service error: {str(e)}"}, status=503)
