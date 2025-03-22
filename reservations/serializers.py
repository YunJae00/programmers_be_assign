from rest_framework import serializers


class ReservationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    company_customer = serializers.CharField(read_only=True, source='company_customer.name')
    exam_date = serializers.DateField(read_only=True)
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    attendees = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
