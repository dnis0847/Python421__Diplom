# admin.py
from django.contrib import admin
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ

@admin.register(HeroBlock)
class MainPageContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'btn_to_action')

@admin.register(JoinOurCommunity)
class JoinOurCommunityAdmin(admin.ModelAdmin):
    list_display = ('title_block', 'subtitle_block')

@admin.register(SubscriptionBenefit)
class SubscriptionBenefitAdmin(admin.ModelAdmin):
    list_display = ('title_benefit', 'description_benefit')
    readonly_fields = ('benefit_svg_preview',)  # Предпросмотр SVG

    def benefit_svg_preview(self, obj):
        """
        Отображение SVG в админке (если файл загружен).
        """
        if obj.benefit_svg:
            return f'<img src="{obj.benefit_svg.url}" alt="{obj.title_benefit}" style="max-height: 100px;">'
        return "SVG файл не загружен"

    benefit_svg_preview.allow_tags = True
    benefit_svg_preview.short_description = "Предпросмотр SVG"

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question',)