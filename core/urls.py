from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsConditionsView.as_view(), name='terms'),
    path('disclaimer/', views.DisclaimerView.as_view(), name='disclaimer'),
]
