from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.incidents import MissingPerson
from api.serializers.incidents.missing_person.serializers import MissingPersonSerializer

class MissingPersonListCreateView(generics.ListCreateAPIView):
    serializer_class    = MissingPersonSerializer
    permission_classes  = [permissions.AllowAny]
    def get_queryset(self):
        qs = MissingPerson.objects.all()
        status_filter = self.request.query_params.get('status', 'open')
        if status_filter == 'found': qs = qs.filter(is_found=True)
        elif status_filter == 'open': qs = qs.filter(is_found=False)
        return qs
    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reported_by=user)

class MissingPersonDetailView(generics.RetrieveAPIView):
    queryset            = MissingPerson.objects.all()
    serializer_class    = MissingPersonSerializer
    permission_classes  = [permissions.AllowAny]

class MarkFoundView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request, pk):
        try: person = MissingPerson.objects.get(pk=pk)
        except MissingPerson.DoesNotExist: return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        person.is_found = True
        person.found_at = timezone.now()
        person.save()
        return Response(MissingPersonSerializer(person, context={'request': request}).data)

class MissingPersonPhotoView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, pk):
        from django.http import FileResponse
        try: person = MissingPerson.objects.get(pk=pk)
        except MissingPerson.DoesNotExist: return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(person.photo.open('rb'), content_type='image/jpeg')
