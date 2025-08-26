from django.core.management.base import BaseCommand
from core.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Set up default subscription plans'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default subscription plans...')
        
        # User Plans
        plans_data = [
            # Individual User Plans
            {
                'name': 'Basic User',
                'plan_type': 'verification',
                'target_type': 'user',
                'description': 'Basic verification for individual users',
                'price': 500.00,
                'duration_days': 30,
                'features': ['verification'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'AI Chat User',
                'plan_type': 'ai_chat',
                'target_type': 'user',
                'description': 'AI chat assistant for individual users',
                'price': 800.00,
                'duration_days': 30,
                'features': ['ai_chat'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 100,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'AI Insights User',
                'plan_type': 'ai_insights',
                'target_type': 'user',
                'description': 'AI insights and analytics for individual users',
                'price': 1200.00,
                'duration_days': 30,
                'features': ['ai_insights'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 10,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'Date Builder User',
                'plan_type': 'date_builder',
                'target_type': 'user',
                'description': 'AI-powered date planning for individual users',
                'price': 1000.00,
                'duration_days': 30,
                'features': ['date_builder'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 3,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'Pro User',
                'plan_type': 'premium',
                'target_type': 'user',
                'description': 'Premium package for power users',
                'price': 2000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': True,
                'max_ai_chats_per_month': 200,
                'max_insights_reports': 20,
                'date_builder_priority': 2,
                'max_places': 2,
                'max_agencies': 1
            },
            {
                'name': 'Premium User',
                'plan_type': 'premium',
                'target_type': 'user',
                'description': 'Ultimate package for individual users',
                'price': 3500.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 500,
                'max_insights_reports': 50,
                'date_builder_priority': 1,
                'max_places': 5,
                'max_agencies': 2
            },
            
            # Place Plans
            {
                'name': 'Basic Place',
                'plan_type': 'verification',
                'target_type': 'place',
                'description': 'Basic verification for places and businesses',
                'price': 1000.00,
                'duration_days': 30,
                'features': ['verification'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'AI Chat Place',
                'plan_type': 'ai_chat',
                'target_type': 'place',
                'description': 'AI chat assistant for places and businesses',
                'price': 1500.00,
                'duration_days': 30,
                'features': ['ai_chat'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 200,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'AI Insights Place',
                'plan_type': 'ai_insights',
                'target_type': 'place',
                'description': 'AI insights and analytics for places and businesses',
                'price': 2000.00,
                'duration_days': 30,
                'features': ['ai_insights'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 25,
                'date_builder_priority': 0,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'Date Builder Place',
                'plan_type': 'date_builder',
                'target_type': 'place',
                'description': 'Inclusion in date builder suggestions for places',
                'price': 1800.00,
                'duration_days': 30,
                'features': ['date_builder'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 2,
                'max_places': 1,
                'max_agencies': 0
            },
            {
                'name': 'Pro Place',
                'plan_type': 'premium',
                'target_type': 'place',
                'description': 'Premium package for places and businesses',
                'price': 4000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': True,
                'max_ai_chats_per_month': 300,
                'max_insights_reports': 40,
                'date_builder_priority': 2,
                'max_places': 2,
                'max_agencies': 0
            },
            {
                'name': 'Premium Place',
                'plan_type': 'premium',
                'target_type': 'place',
                'description': 'Ultimate package for places and businesses',
                'price': 7000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 1000,
                'max_insights_reports': 100,
                'date_builder_priority': 1,
                'max_places': 5,
                'max_agencies': 0
            },
            
            # Agency Plans
            {
                'name': 'Basic Agency',
                'plan_type': 'verification',
                'target_type': 'agency',
                'description': 'Basic verification for travel agencies',
                'price': 2000.00,
                'duration_days': 30,
                'features': ['verification'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 0,
                'max_agencies': 1
            },
            {
                'name': 'AI Chat Agency',
                'plan_type': 'ai_chat',
                'target_type': 'agency',
                'description': 'AI chat assistant for travel agencies',
                'price': 3000.00,
                'duration_days': 30,
                'features': ['ai_chat'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 500,
                'max_insights_reports': 0,
                'date_builder_priority': 0,
                'max_places': 0,
                'max_agencies': 1
            },
            {
                'name': 'AI Insights Agency',
                'plan_type': 'ai_insights',
                'target_type': 'agency',
                'description': 'AI insights and analytics for travel agencies',
                'price': 4000.00,
                'duration_days': 30,
                'features': ['ai_insights'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 50,
                'date_builder_priority': 0,
                'max_places': 0,
                'max_agencies': 1
            },
            {
                'name': 'Date Builder Agency',
                'plan_type': 'date_builder',
                'target_type': 'agency',
                'description': 'Inclusion in date builder suggestions for agencies',
                'price': 3500.00,
                'duration_days': 30,
                'features': ['date_builder'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 0,
                'max_insights_reports': 0,
                'date_builder_priority': 2,
                'max_places': 0,
                'max_agencies': 1
            },
            {
                'name': 'Pro Agency',
                'plan_type': 'premium',
                'target_type': 'agency',
                'description': 'Premium package for travel agencies',
                'price': 8000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': True,
                'max_ai_chats_per_month': 800,
                'max_insights_reports': 80,
                'date_builder_priority': 2,
                'max_places': 0,
                'max_agencies': 2
            },
            {
                'name': 'Premium Agency',
                'plan_type': 'premium',
                'target_type': 'agency',
                'description': 'Ultimate package for travel agencies',
                'price': 15000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat', 'ai_insights', 'date_builder', 'whatsapp_api', 'feature_ads'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 2000,
                'max_insights_reports': 200,
                'date_builder_priority': 1,
                'max_places': 0,
                'max_agencies': 5
            },
            
            # Custom Plans
            {
                'name': 'Custom Business',
                'plan_type': 'custom',
                'target_type': 'business',
                'description': 'Custom subscription package for businesses',
                'price': 5000.00,
                'duration_days': 30,
                'features': ['verification', 'ai_chat'],
                'is_active': True,
                'is_popular': False,
                'max_ai_chats_per_month': 300,
                'max_insights_reports': 30,
                'date_builder_priority': 3,
                'max_places': 3,
                'max_agencies': 2
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                target_type=plan_data['target_type'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created plan: {plan.name}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated plan: {plan.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up subscription plans. Created: {created_count}, Updated: {updated_count}'
            )
        ) 