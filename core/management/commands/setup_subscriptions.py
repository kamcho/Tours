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
                'features': ['Verification Badge', 'Basic Support', 'Profile Enhancement'],
                'is_active': True,
                'is_popular': False
            },
            {
                'name': 'Pro User',
                'plan_type': 'premium',
                'target_type': 'user',
                'description': 'Premium package for power users',
                'price': 1200.00,
                'duration_days': 30,
                'features': ['Verification Badge', 'AI Chat Assistant', 'WhatsApp API', 'Feature Advertising', 'Priority Support'],
                'is_active': True,
                'is_popular': True
            },
            {
                'name': 'Premium User',
                'plan_type': 'premium',
                'target_type': 'user',
                'description': 'Ultimate package for individual users',
                'price': 2500.00,
                'duration_days': 30,
                'features': ['Everything in Pro', 'Custom AI Training', 'Priority Placement', 'Dedicated Support', 'Advanced Analytics'],
                'is_active': True,
                'is_popular': False
            },
            
            # Place Plans
            {
                'name': 'Basic Place',
                'plan_type': 'verification',
                'target_type': 'place',
                'description': 'Basic verification for places and businesses',
                'price': 1000.00,
                'duration_days': 30,
                'features': ['Business Verification', 'Enhanced Listing', 'Basic Analytics'],
                'is_active': True,
                'is_popular': False
            },
            {
                'name': 'Pro Place',
                'plan_type': 'premium',
                'target_type': 'place',
                'description': 'Premium package for places and businesses',
                'price': 2500.00,
                'duration_days': 30,
                'features': ['Business Verification', 'AI Chat Assistant', 'WhatsApp Integration', 'Feature Advertising', 'Advanced Analytics'],
                'is_active': True,
                'is_popular': True
            },
            {
                'name': 'Premium Place',
                'plan_type': 'premium',
                'target_type': 'place',
                'description': 'Ultimate package for places and businesses',
                'price': 5000.00,
                'duration_days': 30,
                'features': ['Everything in Pro', 'Custom AI Training', 'Priority Placement', 'Dedicated Support', 'API Access'],
                'is_active': True,
                'is_popular': False
            },
            
            # Agency Plans
            {
                'name': 'Basic Agency',
                'plan_type': 'verification',
                'target_type': 'agency',
                'description': 'Basic verification for travel agencies',
                'price': 2000.00,
                'duration_days': 30,
                'features': ['Agency Verification', 'Enhanced Listings', 'Basic Support'],
                'is_active': True,
                'is_popular': False
            },
            {
                'name': 'Pro Agency',
                'plan_type': 'premium',
                'target_type': 'agency',
                'description': 'Premium package for travel agencies',
                'price': 5000.00,
                'duration_days': 30,
                'features': ['Agency Verification', 'AI Chat Assistant', 'WhatsApp API', 'Feature Advertising', 'Advanced Analytics', 'Multi-User Access'],
                'is_active': True,
                'is_popular': True
            },
            {
                'name': 'Premium Agency',
                'plan_type': 'premium',
                'target_type': 'agency',
                'description': 'Ultimate package for travel agencies',
                'price': 10000.00,
                'duration_days': 30,
                'features': ['Everything in Pro', 'Custom AI Training', 'Priority Placement', 'Dedicated Support', 'Full API Access', 'White-label Solutions'],
                'is_active': True,
                'is_popular': False
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