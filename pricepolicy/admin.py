from django.contrib import admin
from .models import PricePolicy, Transaction


@admin.register(PricePolicy)
class PricePolicyAdmin(admin.ModelAdmin):
    list_filter = ["category"]
    search_fields = ["title"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_filter = ["status", "start_datetime", "end_datetime"]
    search_fields = ["order"]
