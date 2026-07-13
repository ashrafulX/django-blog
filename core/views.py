from django.shortcuts import render

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class AboutView(TemplateView):
    """About Us page"""
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'আমাদের সম্পর্কে'
        return context


class ContactView(TemplateView):
    """Contact Us page"""
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'যোগাযোগ করুন'
        return context


class PrivacyPolicyView(TemplateView):
    """Privacy Policy page"""
    template_name = 'core/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'গোপনীয়তা নীতি'
        return context


class TermsConditionsView(TemplateView):
    """Terms & Conditions page"""
    template_name = 'core/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'শর্তাবলী'
        return context


class DisclaimerView(TemplateView):
    """Disclaimer page"""
    template_name = 'core/disclaimer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'দায়মুক্তি'
        return context
