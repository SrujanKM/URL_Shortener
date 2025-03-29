# shortener/api_views.py

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import ShortURL
from .serializers import ShortURLSerializer
from .views import generate_short_code, ensure_minimum_length
from django.utils import timezone

class ShortURLCreateAPIView(generics.CreateAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        original_url = serializer.validated_data['original_url']
        custom_alias = self.request.data.get('custom_alias')
        expiration_date_str = self.request.data.get('expiration_date')

        expiration_date = None
        if expiration_date_str:
            expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M:%S')

        if custom_alias:
            custom_alias = ensure_minimum_length(custom_alias)
            if ShortURL.objects.filter(short_code=custom_alias).exists():
                return Response("Custom alias already in use. Please choose another one.", status=400)
            short_code = custom_alias
        else:
            short_code = generate_short_code()

        serializer.save(short_code=short_code, user=self.request.user, expiration_date=expiration_date)

class ShortURLRetrieveAPIView(generics.RetrieveAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer
    lookup_field = 'short_code'
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_expired():
            return Response("Link Expired", status=404)
        if not instance.is_active:
            return Response("Link Deactivated", status=404)
        return super().retrieve(request, *args, **kwargs)
