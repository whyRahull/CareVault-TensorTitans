import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from api.models.incidents import MLServiceConfig

class ViolenceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'incidents/dashboard_violence.html'

class ViolenceVideoDetectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        video_file = request.FILES.get('file')
        if not video_file:
            return Response({'error': 'Video file is required'}, status=400)

        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}/api/violence/detect"

        try:
            # We use a larger timeout for full video analysis as it might take time
            files = {'file': (video_file.name, video_file.read(), video_file.content_type)}
            resp = requests.post(ml_url, files=files, timeout=300) 
            resp.raise_for_status()
            return Response(resp.json())
        except Exception as e:
            return Response({'error': f"ML Service error: {str(e)}"}, status=503)
