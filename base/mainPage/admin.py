# admin.py
from django.contrib import admin
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ, Subscriber

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
    
    
@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'category', 'subscribed_at', 'is_active', 'is_confirmed')
    list_filter = ('is_active', 'is_confirmed', 'category', 'subscribed_at')
    search_fields = ('email', 'ip_address')
    date_hierarchy = 'subscribed_at'
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} подписок активировано.")
    activate_subscriptions.short_description = "Активировать выбранные подписки"
    
    def deactivate_subscriptions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} подписок деактивировано.")
    deactivate_subscriptions.short_description = "Деактивировать выбранные подписки"