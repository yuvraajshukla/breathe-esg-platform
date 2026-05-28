from django.urls import path

from .views import (
    SAPUploadView,
    UtilityUploadView,
    TravelUploadView,
    EmissionRecordListView,
    FailedRawRecordListView,
    ApproveEmissionView,
    RejectEmissionView,
)

urlpatterns = [
    path("upload/sap/", SAPUploadView.as_view(), name="sap-upload"),
    path("upload/utility/", UtilityUploadView.as_view(), name="utility-upload"),
    path("upload/travel/", TravelUploadView.as_view(), name="travel-upload"),
    path("records/", EmissionRecordListView.as_view(), name="records"),
    path("raw-records/failed/", FailedRawRecordListView.as_view(), name="failed-raw-records"),
    path("records/<int:pk>/approve/", ApproveEmissionView.as_view(), name="approve-record"),
    path("records/<int:pk>/reject/", RejectEmissionView.as_view(), name="reject-record"),
]