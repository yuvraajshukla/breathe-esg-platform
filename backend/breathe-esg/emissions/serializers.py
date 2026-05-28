from rest_framework import serializers

from .models import DataSource, EmissionRecord, RawRecord


class DataSourceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            "company",
            "source_type",
            "uploaded_file",
            "uploaded_by",
        ]


class EmissionRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "source_type",
            "uploaded_by",
            "scope",
            "category",
            "quantity",
            "original_unit",
            "normalized_unit",
            "activity_date",
            "suspicious_flag",
            "review_status",
            "created_at",
        ]

    def get_source_type(self, obj):
        try:
            return obj.raw_record.data_source.source_type
        except Exception:
            return None

    def get_uploaded_by(self, obj):
        try:
            return obj.raw_record.data_source.uploaded_by
        except Exception:
            return None


class RawRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.SerializerMethodField()

    class Meta:
        model = RawRecord
        fields = [
            "id",
            "source_type",
            "processing_status",
            "error_message",
            "raw_data",
            "created_at",
        ]

    def get_source_type(self, obj):
        try:
            return obj.data_source.source_type
        except Exception:
            return None