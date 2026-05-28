
import csv
import io
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView



from .models import (
    Company,
    DataSource,
    RawRecord,
    EmissionRecord,
    AuditLog,
)

from .serializers import (
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

    uploaded_file = request.FILES.get("uploaded_file")

    if not uploaded_file:
        return Response(
            {"error": "No file uploaded"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # AUTO CREATE COMPANY
    company, created = Company.objects.get_or_create(
        name="Breathe ESG Demo Company"
    )

    # CREATE DATASOURCE MANUALLY
    data_source = DataSource.objects.create(
        company=company,
        source_type=source_type,
        uploaded_file=uploaded_file,
        uploaded_by="Admin",
    )

    decoded_file = uploaded_file.read().decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(decoded_file))

    created_count = 0
    failed_count = 0

    for row in reader:

        try:

            quantity = parse_float(
                first_value(row, *quantity_keys)
            )

            activity_date = parse_date(
                first_value(row, *date_keys)
            )

            category = category_resolver(row)

            original_unit = (
                first_value(row, *unit_keys)
                or normalized_unit
            )

            suspicious_flag = quantity >= suspicious_threshold

            raw_record = RawRecord.objects.create(
                data_source=data_source,
                raw_data=row,
                processing_status="PROCESSED",
            )

            EmissionRecord.objects.create(
                company=company,
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

            created_count += 1

        except Exception as exc:

            RawRecord.objects.create(
                data_source=data_source,
                raw_data=row,
                processing_status="FAILED",
                error_message=str(exc),
            )

            failed_count += 1

    return Response(
        {
            "message": success_message,
            "created": created_count,
            "failed": failed_count,
        },
        status=status.HTTP_201_CREATED,
    )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd

from .models import EmissionRecord


class SAPUploadView(APIView):
    def post(self, request):

        file = request.FILES.get("uploaded_file")

        if not file:
            return Response(
                {"error": "No file uploaded"},
                status=400
            )

        try:
            df = pd.read_csv(file)

            created = []

            for _, row in df.iterrows():

                quantity = float(
                    row.get("quantity", 0)
                )

                suspicious = quantity > 10000

                record = EmissionRecord.objects.create(
                   scope=row.get("scope", "SCOPE_1"),
                   category=row.get("category", "Fuel"),
                   quantity=quantity,
                   normalized_unit=row.get("unit", "liters"),

                   activity_date="2026-05-28",

                   review_status="PENDING",
                   suspicious_flag=suspicious,
                )

                created.append(record.id)

            return Response(
                {
                    "message": "Upload successful",
                    "created_records": created,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=500
            )


class UtilityUploadView(APIView):

    def post(self, request):

        return ingest_csv(
            request,
            source_type="UTILITY",
            scope="SCOPE_2",

            category_resolver=lambda row:
                "Electricity",

            quantity_keys=(
                "kwh_used",
                "kwh",
                "usage",
                "quantity",
            ),

            unit_keys=(
                "unit",
                "uom",
            ),

            date_keys=(
                "billing_date",
                "date",
            ),

            normalized_unit="kWh",

            suspicious_threshold=50000,

            success_message="Utility upload successful",
        )


class TravelUploadView(APIView):

    def post(self, request):

        return ingest_csv(
            request,
            source_type="TRAVEL",
            scope="SCOPE_3",

            category_resolver=lambda row:
                first_value(
                    row,
                    "trip_type",
                    "category",
                ) or "Business Travel",

            quantity_keys=(
                "distance_km",
                "distance",
                "km",
            ),

            unit_keys=(
                "unit",
                "uom",
            ),

            date_keys=(
                "travel_date",
                "date",
            ),

            normalized_unit="km",

            suspicious_threshold=10000,

            success_message="Travel upload successful",
        )


class EmissionRecordListView(APIView):

    def get(self, request):

        records = EmissionRecord.objects.all().order_by("-id")

        serializer = EmissionRecordSerializer(
            records,
            many=True
        )

        return Response(serializer.data)


class FailedRawRecordListView(APIView):

    def get(self, request):

        failed = RawRecord.objects.filter(
            processing_status="FAILED"
        ).order_by("-id")

        serializer = RawRecordSerializer(
            failed,
            many=True
        )

        return Response(serializer.data)


class ApproveEmissionView(APIView):

    def patch(self, request, pk):

        record = get_object_or_404(
            EmissionRecord,
            pk=pk
        )

        old_status = record.review_status

        record.review_status = "APPROVED"

        record.save()

        AuditLog.objects.create(
            emission_record=record,
            field_changed="review_status",
            old_value=old_status,
            new_value="APPROVED",
            changed_by="Admin",
        )

        return Response({
            "message": "Approved"
        })


class RejectEmissionView(APIView):

    def patch(self, request, pk):

        record = get_object_or_404(
            EmissionRecord,
            pk=pk
        )

        old_status = record.review_status

        record.review_status = "REJECTED"

        record.save()

        AuditLog.objects.create(
            emission_record=record,
            field_changed="review_status",
            old_value=old_status,
            new_value="REJECTED",
            changed_by="Admin",
        )

        return Response({
            "message": "Rejected"
        })

