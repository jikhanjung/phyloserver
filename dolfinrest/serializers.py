from rest_framework import serializers
from .models import DolfinImage

class DolfinImageSerializer(serializers.ModelSerializer):
    imagefile = serializers.ImageField(use_url=True)
    class Meta:
        model = DolfinImage
        fields = [ 'title', 'filename', 'md5hash', 'imagefile' ]
