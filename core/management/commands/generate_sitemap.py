"""
Django management command to generate sitemaps
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from core.sitemaps import sitemaps
from django.contrib.sitemaps.views import sitemap
from django.http import HttpRequest
from django.test import RequestFactory
import os


class Command(BaseCommand):
    help = 'Generate static sitemap files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='static/sitemaps',
            help='Output directory for sitemap files'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a mock request for sitemap generation
        factory = RequestFactory()
        request = factory.get('/')
        
        # Generate main sitemap
        main_sitemap = sitemap(request, sitemaps=sitemaps)
        main_sitemap_content = main_sitemap.content.decode('utf-8')
        
        # Write main sitemap
        main_sitemap_path = os.path.join(output_dir, 'sitemap.xml')
        with open(main_sitemap_path, 'w', encoding='utf-8') as f:
            f.write(main_sitemap_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated main sitemap: {main_sitemap_path}')
        )
        
        # Generate individual sitemaps
        for name, sitemap_class in sitemaps.items():
            try:
                sitemap_instance = sitemap_class()
                items = sitemap_instance.items()
                
                if items:
                    # Create individual sitemap content
                    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
                    
                    for item in items:
                        location = sitemap_instance.location(item)
                        lastmod = sitemap_instance.lastmod(item) if hasattr(sitemap_instance, 'lastmod') else None
                        changefreq = getattr(sitemap_instance, 'changefreq', 'weekly')
                        priority = getattr(sitemap_instance, 'priority', 0.5)
                        
                        sitemap_content += f"""  <url>
    <loc>https://tourske.com{location}</loc>
"""
                        
                        if lastmod:
                            sitemap_content += f"""    <lastmod>{lastmod.strftime('%Y-%m-%d')}</lastmod>
"""
                        
                        sitemap_content += f"""    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
"""
                    
                    sitemap_content += """</urlset>"""
                    
                    # Write individual sitemap
                    individual_sitemap_path = os.path.join(output_dir, f'sitemap-{name}.xml')
                    with open(individual_sitemap_path, 'w', encoding='utf-8') as f:
                        f.write(sitemap_content)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Generated sitemap for {name}: {individual_sitemap_path}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'No items found for sitemap: {name}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error generating sitemap for {name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Sitemap generation completed!')
        )
