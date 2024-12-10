
from django.urls import path
from . import views
app_name = "appointment"

urlpatterns = [
    path("make-appointment", views.make_appointment ,name="make-appointment"),
    

]