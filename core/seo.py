"""
SEO utilities for TravelsKe platform
"""
from django.conf import settings
from django.utils.html import strip_tags
from django.urls import reverse
import json


def generate_meta_tags(title, description, keywords=None, image=None, url=None, type='website'):
    """
    Generate comprehensive meta tags for SEO and social media
    """
    meta_tags = {
        'title': title,
        'description': strip_tags(description)[:160] if description else '',
        'keywords': keywords or 'Kenya, travel, tours, events, places, tourism, adventure',
        'image': image or f"{settings.STATIC_URL}images/travelske-default.jpg",
        'url': url or '',
        'type': type,
        'site_name': 'TravelsKe',
        'twitter_handle': '@TravelsKe',
    }
    
    return meta_tags


def generate_structured_data(data_type, **kwargs):
    """
    Generate structured data (Schema.org) markup
    """
    base_schema = {
        "@context": "https://schema.org",
        "@type": data_type,
    }
    
    if data_type == "Organization":
        schema = {
            **base_schema,
            "name": kwargs.get('name', 'TravelsKe'),
            "url": kwargs.get('url', 'https://tourske.com'),
            "logo": kwargs.get('logo', 'https://tourske.com/static/images/travelske-logo.png'),
            "description": kwargs.get('description', 'Your premier destination for discovering Kenya\'s amazing tours, events, and places.'),
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "Kenya",
                "addressLocality": "Nairobi"
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "customer service",
                "email": "info@tourske.com"
            },
            "sameAs": [
                "https://facebook.com/travelske",
                "https://twitter.com/travelske",
                "https://instagram.com/travelske"
            ]
        }
    
    elif data_type == "Tour":
        schema = {
            **base_schema,
            "name": kwargs.get('name', ''),
            "description": kwargs.get('description', ''),
            "image": kwargs.get('image', ''),
            "url": kwargs.get('url', ''),
            "offers": {
                "@type": "Offer",
                "price": str(kwargs.get('price', '0')),
                "priceCurrency": "KES",
                "availability": "https://schema.org/InStock" if kwargs.get('available', True) else "https://schema.org/OutOfStock"
            },
            "location": {
                "@type": "Place",
                "name": kwargs.get('location', 'Kenya')
            },
            "startDate": kwargs.get('start_date', ''),
            "endDate": kwargs.get('end_date', ''),
            "organizer": {
                "@type": "Organization",
                "name": kwargs.get('organizer_name', 'TravelsKe')
            }
        }
    
    elif data_type == "Event":
        schema = {
            **base_schema,
            "name": kwargs.get('name', ''),
            "description": kwargs.get('description', ''),
            "image": kwargs.get('image', ''),
            "url": kwargs.get('url', ''),
            "startDate": kwargs.get('start_date', ''),
            "endDate": kwargs.get('end_date', ''),
            "location": {
                "@type": "Place",
                "name": kwargs.get('location', 'Kenya'),
                "address": kwargs.get('address', '')
            },
            "organizer": {
                "@type": "Organization",
                "name": kwargs.get('organizer_name', 'TravelsKe')
            },
            "offers": {
                "@type": "Offer",
                "price": str(kwargs.get('price', '0')),
                "priceCurrency": "KES"
            }
        }
    
    elif data_type == "Place":
        schema = {
            **base_schema,
            "name": kwargs.get('name', ''),
            "description": kwargs.get('description', ''),
            "image": kwargs.get('image', ''),
            "url": kwargs.get('url', ''),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": kwargs.get('street_address', ''),
                "addressLocality": kwargs.get('city', ''),
                "addressRegion": kwargs.get('region', ''),
                "addressCountry": kwargs.get('country', 'Kenya')
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": kwargs.get('latitude', ''),
                "longitude": kwargs.get('longitude', '')
            },
            "telephone": kwargs.get('phone', ''),
            "email": kwargs.get('email', ''),
            "openingHours": kwargs.get('opening_hours', '')
        }
    
    elif data_type == "Review":
        schema = {
            **base_schema,
            "itemReviewed": {
                "@type": kwargs.get('item_type', 'Thing'),
                "name": kwargs.get('item_name', '')
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": kwargs.get('rating', 0),
                "bestRating": 5
            },
            "author": {
                "@type": "Person",
                "name": kwargs.get('author_name', 'Anonymous')
            },
            "reviewBody": kwargs.get('review_text', ''),
            "datePublished": kwargs.get('date_published', '')
        }
    
    else:
        schema = base_schema
    
    return schema


def generate_breadcrumb_data(items):
    """
    Generate breadcrumb structured data
    """
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }
    
    for index, item in enumerate(items):
        breadcrumb_schema["itemListElement"].append({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.get('name', ''),
            "item": item.get('url', '')
        })
    
    return breadcrumb_schema


def generate_faq_schema(questions_answers):
    """
    Generate FAQ structured data
    """
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    
    for qa in questions_answers:
        faq_schema["mainEntity"].append({
            "@type": "Question",
            "name": qa.get('question', ''),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": qa.get('answer', '')
            }
        })
    
    return faq_schema


def generate_local_business_schema(business_data):
    """
    Generate LocalBusiness structured data
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business_data.get('name', ''),
        "description": business_data.get('description', ''),
        "image": business_data.get('image', ''),
        "url": business_data.get('url', ''),
        "telephone": business_data.get('phone', ''),
        "email": business_data.get('email', ''),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": business_data.get('street_address', ''),
            "addressLocality": business_data.get('city', ''),
            "addressRegion": business_data.get('region', ''),
            "addressCountry": business_data.get('country', 'Kenya'),
            "postalCode": business_data.get('postal_code', '')
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": business_data.get('latitude', ''),
            "longitude": business_data.get('longitude', '')
        },
        "openingHours": business_data.get('opening_hours', ''),
        "priceRange": business_data.get('price_range', ''),
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": business_data.get('rating', 0),
            "reviewCount": business_data.get('review_count', 0)
        } if business_data.get('rating') else None
    }
    
    # Remove None values
    schema = {k: v for k, v in schema.items() if v is not None}
    
    return schema


def generate_meta_html(meta_tags):
    """
    Generate HTML meta tags from meta_tags dictionary
    """
    html = []
    
    # Basic meta tags
    html.append(f'<title>{meta_tags["title"]}</title>')
    html.append(f'<meta name="description" content="{meta_tags["description"]}">')
    html.append(f'<meta name="keywords" content="{meta_tags["keywords"]}">')
    
    # Open Graph tags
    html.append(f'<meta property="og:title" content="{meta_tags["title"]}">')
    html.append(f'<meta property="og:description" content="{meta_tags["description"]}">')
    html.append(f'<meta property="og:image" content="{meta_tags["image"]}">')
    html.append(f'<meta property="og:url" content="{meta_tags["url"]}">')
    html.append(f'<meta property="og:type" content="{meta_tags["type"]}">')
    html.append(f'<meta property="og:site_name" content="{meta_tags["site_name"]}">')
    
    # Twitter Card tags
    html.append(f'<meta name="twitter:card" content="summary_large_image">')
    html.append(f'<meta name="twitter:site" content="{meta_tags["twitter_handle"]}">')
    html.append(f'<meta name="twitter:title" content="{meta_tags["title"]}">')
    html.append(f'<meta name="twitter:description" content="{meta_tags["description"]}">')
    html.append(f'<meta name="twitter:image" content="{meta_tags["image"]}">')
    
    # Additional meta tags
    html.append('<meta name="robots" content="index, follow">')
    html.append('<meta name="author" content="TravelsKe">')
    html.append('<meta name="language" content="English">')
    html.append('<meta name="revisit-after" content="7 days">')
    
    return '\n    '.join(html)


def generate_structured_data_html(schema_data):
    """
    Generate HTML script tag with structured data
    """
    if isinstance(schema_data, list):
        # Multiple schemas
        html = []
        for schema in schema_data:
            html.append(f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>')
        return '\n    '.join(html)
    else:
        # Single schema
        return f'<script type="application/ld+json">{json.dumps(schema_data, indent=2)}</script>'
