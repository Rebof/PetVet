from django.urls import path
from . import views

app_name = "appointment"

urlpatterns = [
    path("add-schedule/", views.add_schedule, name="add_schedule"),
    path("vets/", views.vet_list, name="vet_list"),  # List of all vets
    path("vets/<int:vet_id>/", views.vet_schedule, name="vet_schedule"),  # Specific vet's schedule
    path("vets/<int:vet_id>/schedule/<int:schedule_id>/book/", views.book_appointment, name="book_appointment"),

    path("appointments/list", views.appointment_list, name="appointment_list"),
    path("appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),

    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="cancel_appointment"),
    path("vet/<int:vet_id>/appointments/pending/", views.vet_pending_appointments, name="vet_pending_appointments"),

    path("vet/<int:vet_id>/appointments/pending/", views.vet_pending_appointments, name="vet_pending_appointments"),
    path("appointments/<int:appointment_id>/accept/", views.accept_appointment, name="accept_appointment"),
    path("appointments/<int:appointment_id>/reject/", views.reject_appointment, name="reject_appointment"),
    path("vet/<int:vet_id>/appointments/accepted/", views.vet_accepted_appointments, name="vet_accepted_appointments"),

    path("appointments/<int:appointment_id>/complete/", views.mark_completed, name="mark_completed"),

    # path("appointments/testing/", views.open_test , name="open_test"),



    # path('verify-payment/<int:appointment_id>/', views.verify_payment, name='verify_payment'),

    # path('verify/<str:appointment_id>/', views.verify_payment, name='verify_payment'),

    path('book/<int:vet_id>/schedule/<int:schedule_id>/', views.book_appointment, name='book_appointment'),


    path('payment/khalti/<int:appointment_id>/', views.initiate_khalti_payment, name='initiate_khalti_payment'),
    path('verify_khalti/<int:appointment_id>/', views.verify_khalti_payment, name='verify_khalti_payment'),
    path('payment/success/<int:appointment_id>/', views.payment_success, name='payment_success'),
    path('payment/failed/<int:appointment_id>/', views.payment_failed, name='payment_failed'),

]
