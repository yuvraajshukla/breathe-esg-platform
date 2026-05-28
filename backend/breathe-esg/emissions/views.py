import csv
import io
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog, DataSource, EmissionRecord, RawRecord
from .serializers import (
    DataSourceUploadSerializer,
    EmissionRecordSerializer,
    RawRecordSerializer,
)


def first_value(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        value = str(value).strip()
        if value != "":
            return value
    return None


def parse_float(value):
    if value is None:
        raise ValueError("Missing numeric value")
    cleaned = str(value).replace(",", "").strip()
    return float(cleaned)


def parse_date(value):
    if not value:
        return timezone.now().date()

    value = str(value).strip()
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y-%m",
        "%m/%Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt in ("%Y-%m", "%m/%Y"):
                return parsed.date().replace(day=1)
            return parsed.date()
        except ValueError:
            continue

    return timezone.now().date()


def ingest_csv(
    request,
    *,
    source_type,
    scope,
    category_resolver,
    quantity_keys,
    unit_keys,
    date_keys,
    normalized_unit,
    suspicious_threshold,
    success_message,
):
    serializer = DataSourceUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data_source = serializer.save()

    decoded_file = data_source.uploaded_file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded_file))

    created = 0
    failed = 0

    for row in reader:
        try:
            quantity = parse_float(first_value(row, *quantity_keys))
            activity_date = parse_date(first_value(row, *date_keys))
            category = category_resolver(row)
            original_unit = first_value(row, *unit_keys) or normalized_unit
            suspicious_flag = quantity >= suspicious_threshold

            raw_record = RawRecord.objects.create(
                data_source=data_source,
                raw_data=row,
                processing_status="PROCESSED",
            )

            EmissionRecord.objects.create(
                company=data_source.company,
                raw_record=raw_record,
                scope=scope,
                category=category,
                quantity=quantity,
                original_unit=original_unit,
                normalized_unit=normalized_unit,
                activity_date=activity_date,
                suspicious_flag=suspicious_flag,
                review_status="PENDING",
            )

            created += 1

        except Exception as exc:
            RawRecord.objects.create(
                data_source=data_source,
                raw_data=row,
                processing_status="FAILED",
                error_message=str(exc),
            )
            failed += 1

    return Response(
        {
            "message": success_message,
            "created": created,
            "failed": failed,
        },
        status=status.HTTP_201_CREATED,
    )


class SAPUploadView(APIView):
    def post(self, request):
        return ingest_csv(
            request,
            source_type="SAP",
            scope="SCOPE_1",
            category_resolver=lambda row: first_value(
                row,
                "category",
                "material",
                "MATNR",
                "description",
                "text",
            ) or "Fuel",
            quantity_keys=("quantity", "qty", "QTY", "MENGE", "amount", "value"),
            unit_keys=("unit", "MEINS", "UOM", "uom"),
            date_keys=("activity_date", "date", "BUDAT", "posting_date"),
            normalized_unit="liters",
            suspicious_threshold=10000,
            success_message="SAP data uploaded successfully",
        )


class UtilityUploadView(APIView):
    def post(self, request):
        return ingest_csv(
            request,
            source_type="UTILITY",
            scope="SCOPE_2",
            category_resolver=lambda row: "Electricity",
            quantity_keys=("kwh_used", "kwh", "quantity", "usage", "consumption"),
            unit_keys=("unit", "uom", "UOM"),
            date_keys=("billing_date", "billing_period", "date"),
            normalized_unit="kWh",
            suspicious_threshold=50000,
            success_message="Utility data uploaded successfully",
        )


class TravelUploadView(APIView):
    def post(self, request):
        return ingest_csv(
            request,
            source_type="TRAVEL",
            scope="SCOPE_3",
            category_resolver=lambda row: first_value(
                row,
                "category",
                "trip_type",
                "travel_type",
                "purpose",
            ) or "Business Travel",
            quantity_keys=("distance_km", "distance", "km", "trip_distance"),
            unit_keys=("unit", "uom", "UOM"),
            date_keys=("travel_date", "date"),
            normalized_unit="km",
            suspicious_threshold=10000,
            success_message="Travel data uploaded successfully",
        )


class EmissionRecordListView(APIView):
    def get(self, request):
        records = EmissionRecord.objects.all().order_by("-id")
        serializer = EmissionRecordSerializer(records, many=True)
        return Response(serializer.data)


class FailedRawRecordListView(APIView):
    def get(self, request):
        raw_records = RawRecord.objects.filter(
            processing_status="FAILED"
        ).order_by("-id")
        serializer = RawRecordSerializer(raw_records, many=True)
        return Response(serializer.data)


class ApproveEmissionView(APIView):
    def patch(self, request, pk):
        record = get_object_or_404(EmissionRecord, pk=pk)
        changed_by = request.data.get("changed_by", "Analyst")

        old_status = record.review_status
        record.review_status = "APPROVED"
        record.save(update_fields=["review_status"])

        AuditLog.objects.create(
            emission_record=record,
            field_changed="review_status",
            old_value=old_status,
            new_value="APPROVED",
            changed_by=changed_by,
        )

        return Response(EmissionRecordSerializer(record).data)


class RejectEmissionView(APIView):
    def patch(self, request, pk):
        record = get_object_or_404(EmissionRecord, pk=pk)
        changed_by = request.data.get("changed_by", "Analyst")

        old_status = record.review_status
        record.review_status = "REJECTED"
        record.save(update_fields=["review_status"])

        AuditLog.objects.create(
            emission_record=record,
            field_changed="review_status",
            old_value=old_status,
            new_value="REJECTED",
            changed_by=changed_by,
        )

        return Response(EmissionRecordSerializer(record).data)