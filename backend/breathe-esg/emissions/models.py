from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    SOURCE_TYPES = [
        ("SAP", "SAP"),
        ("UTILITY", "Utility"),
        ("TRAVEL", "Travel"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="data_sources"
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES
    )

    uploaded_file = models.FileField(upload_to="uploads/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    uploaded_by = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.company.name} - {self.source_type}"


class RawRecord(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSED", "Processed"),
        ("FAILED", "Failed"),
    ]

    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="raw_records"
    )

    raw_data = models.JSONField()

    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RawRecord {self.id}"


class EmissionRecord(models.Model):
    SCOPE_CHOICES = [
        ("SCOPE_1", "Scope 1"),
        ("SCOPE_2", "Scope 2"),
        ("SCOPE_3", "Scope 3"),
    ]

    REVIEW_STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="emission_records"
    )

    raw_record = models.ForeignKey(
        RawRecord,
        on_delete=models.CASCADE,
        related_name="emission_records"
    )

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES
    )

    category = models.CharField(max_length=255)

    quantity = models.FloatField()

    original_unit = models.CharField(max_length=50)

    normalized_unit = models.CharField(max_length=50)

    activity_date = models.DateField()

    suspicious_flag = models.BooleanField(default=False)

    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scope} - {self.category}"


class AuditLog(models.Model):
    emission_record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )

    field_changed = models.CharField(max_length=255)

    old_value = models.TextField()

    new_value = models.TextField()

    changed_by = models.CharField(max_length=255)

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AuditLog {self.id}"