from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    patient = serializers.CharField(max_length=100)
    receiver = serializers.CharField(max_length=100, required=False, allow_null=True) # Aded this in encase we want alternative receivers in the future
    message = serializers.ListField(
        child=serializers.CharField(max_length=1000)
    )