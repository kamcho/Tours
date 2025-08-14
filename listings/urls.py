from django.urls import path
from . import views

urlpatterns = [
    # Place URLs
    path('place/create/', views.PlaceCreateWizard.as_view(), name='place_create_step'),
    path('place/create/step/<int:step>/', views.PlaceCreateWizard.as_view(), name='place_create_step'),
    path('place/create/success/', views.place_create_success, name='place_create_success'),
    path('places/', views.PublicPlaceListView.as_view(), name='public_place_list'),
    path('place/<int:pk>/', views.PublicPlaceDetailView.as_view(), name='public_place_detail'),
    path('place/<int:pk>/page/', views.PublicPlaceDetailPageView.as_view(), name='public_place_detail_page'),
    path('all-places/', views.AllPlacesTemplateView.as_view(), name='all_places_templateview'),
    
    # User Place URLs
    path('my-places/', views.UserPlaceListView.as_view(), name='user_place_list'),
    path('my-place/<int:pk>/', views.UserPlaceDetailView.as_view(), name='user_place_detail'),
    path('my-place/<int:pk>/edit/', views.UserPlaceUpdateView.as_view(), name='user_place_update'),
    path('my-place/<int:pk>/delete/', views.UserPlaceDeleteView.as_view(), name='user_place_delete'),
    
    # Travel Group URLs
    path('travel-groups/', views.TravelGroupListView.as_view(), name='travelgroup_list'),
    path('travel-group/<int:pk>/', views.TravelGroupDetailView.as_view(), name='travelgroup_detail'),
    path('travel-group/create/', views.TravelGroupCreateView.as_view(), name='travelgroup_create'),
    path('travel-group/<int:pk>/edit/', views.TravelGroupUpdateView.as_view(), name='travelgroup_update'),
    path('travel-group/<int:pk>/delete/', views.TravelGroupDeleteView.as_view(), name='travelgroup_delete'),
    path('my-travel-groups/', views.UserTravelGroupListView.as_view(), name='user_travelgroup_list'),
    
    # Group Tours URLs
    path('group-tours/', views.GroupToursListView.as_view(), name='grouptours_list'),
    path('group-tour/<int:pk>/', views.GroupToursDetailView.as_view(), name='grouptours_detail'),
    path('group-tour/create/', views.GroupToursCreateView.as_view(), name='grouptours_create'),
    path('group-tour/<int:pk>/edit/', views.GroupToursUpdateView.as_view(), name='grouptours_update'),
    path('group-tour/<int:pk>/delete/', views.GroupToursDeleteView.as_view(), name='grouptours_delete'),
    path('my-group-tours/', views.UserGroupToursListView.as_view(), name='user_grouptours_list'),
    path('group-tour/<int:pk>/public/', views.PublicGroupToursDetailView.as_view(), name='public_grouptours_detail'),
    
    # Enhanced Booking URL
    path('group-tour/<int:pk>/book/', views.EnhancedTourBookingView.as_view(), name='enhanced_tour_booking'),
    path('group-tour/<int:pk>/book-payment/', views.TourBookingWithPaymentView.as_view(), name='tour_booking_payment'),
    path('payment/status/<str:transaction_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    path('mpesa/webhook/', views.MPesaWebhookView.as_view(), name='mpesa_webhook'),
    
    # Agency URLs
    path('agencies/', views.AgencyListView.as_view(), name='agency_list'),
    path('agency/<int:pk>/', views.AgencyDetailView.as_view(), name='agency_detail'),
    path('agency/create/', views.AgencyCreateView.as_view(), name='agency_create'),
    path('agency/<int:pk>/edit/', views.AgencyUpdateView.as_view(), name='agency_update'),
    path('agency/<int:pk>/delete/', views.AgencyDeleteView.as_view(), name='agency_delete'),
    path('my-agencies/', views.UserAgencyListView.as_view(), name='user_agency_list'),
    path('agency/<int:pk>/public/', views.PublicAgencyDetailView.as_view(), name='public_agency_detail'),
    
    # Event URLs
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('event/create/', views.EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('my-events/', views.UserEventListView.as_view(), name='user_event_list'),
    path('event/<int:pk>/public/', views.PublicEventDetailView.as_view(), name='public_event_detail'),
    path('event/<int:pk>/book-payment/', views.EventBookingWithPaymentView.as_view(), name='event_booking_payment'),
    path('event/<int:pk>/book-simple/', views.SimpleEventBookingView.as_view(), name='simple_event_booking'),
    
    # Feature URLs
    path('place/<int:place_id>/feature/create/', views.FeatureCreateView.as_view(), name='feature_create'),
    path('feature/<int:pk>/edit/', views.FeatureUpdateView.as_view(), name='feature_update'),
    path('feature/<int:pk>/delete/', views.FeatureDeleteView.as_view(), name='feature_delete'),
    
    # User Dashboard URLs
    path('my-bookings/', views.UserBookingsView.as_view(), name='user_bookings'),
    path('my-bookmarks/', views.UserBookmarksView.as_view(), name='user_bookmarks'),
    
    # API URLs for AJAX
    path('tour/<int:tour_id>/like/', views.like_tour, name='like_tour'),
    path('event/<int:event_id>/like/', views.like_event, name='like_event'),
    path('tour/<int:tour_id>/bookmark/', views.bookmark_tour, name='bookmark_tour'),
    path('event/<int:event_id>/bookmark/', views.bookmark_event, name='bookmark_event'),
    path('tour/<int:tour_id>/comment/', views.add_tour_comment, name='add_tour_comment'),
    path('event/<int:event_id>/comment/', views.add_event_comment, name='add_event_comment'),
    path('tour/<int:tour_id>/book/', views.book_tour, name='book_tour'),
    path('event/<int:event_id>/book/', views.book_event, name='book_event'),

    # Menu Management URLs
    path('place/<int:place_pk>/menu/category/create/', views.MenuCategoryCreateView.as_view(), name='menu_category_create'),
    path('menu/category/<int:pk>/edit/', views.MenuCategoryUpdateView.as_view(), name='menu_category_update'),
    path('menu/category/<int:pk>/delete/', views.MenuCategoryDeleteView.as_view(), name='menu_category_delete'),
    
    path('place/<int:place_pk>/menu/item/create/', views.MenuItemCreateView.as_view(), name='menu_item_create'),
    path('menu/item/<int:pk>/edit/', views.MenuItemUpdateView.as_view(), name='menu_item_update'),
    path('menu/item/<int:pk>/delete/', views.MenuItemDeleteView.as_view(), name='menu_item_delete'),
    
    # Menu Display URLs
    path('place/<int:pk>/menu/', views.PlaceMenuView.as_view(), name='place_menu'),
    path('my-place/<int:pk>/menu/', views.UserPlaceMenuView.as_view(), name='user_place_menu'),
    
    # Rating and Review URLs
    path('place/<int:place_id>/rate/', views.submit_place_rating, name='submit_place_rating'),
    path('agency/<int:agency_id>/rate/', views.submit_agency_rating, name='submit_agency_rating'),
    path('rating/<str:rating_type>/<int:rating_id>/helpful/', views.mark_rating_helpful, name='mark_rating_helpful'),
    path('rating/<str:rating_type>/<int:rating_id>/delete/', views.delete_rating, name='delete_rating'),
    path('place/<int:place_id>/ratings/', views.PlaceRatingListView.as_view(), name='place_ratings'),
    path('agency/<int:agency_id>/ratings/', views.AgencyRatingListView.as_view(), name='agency_ratings'),

    # Agency Services
    path('agency/<int:agency_id>/services/', views.AgencyServiceListView.as_view(), name='agency_service_list'),
    path('agency/service/<int:pk>/', views.AgencyServiceDetailView.as_view(), name='agency_service_detail'),
    path('agency/<int:agency_id>/service/create/', views.AgencyServiceCreateView.as_view(), name='agency_service_create'),
    path('agency/service/<int:pk>/edit/', views.AgencyServiceUpdateView.as_view(), name='agency_service_update'),
    path('agency/service/<int:pk>/delete/', views.AgencyServiceDeleteView.as_view(), name='agency_service_delete'),
    path('agency/service/<int:pk>/toggle-featured/', views.agency_service_toggle_featured, name='agency_service_toggle_featured'),
    path('agency/service/<int:pk>/toggle-active/', views.agency_service_toggle_active, name='agency_service_toggle_active'),
    
    # Search and Discovery URLs
    path('search/', views.AdvancedSearchView.as_view(), name='advanced_search'),
    path('search/quick/', views.QuickSearchView.as_view(), name='quick_search'),
    path('trending/', views.TrendingView.as_view(), name='trending'),
    path('recommendations/', views.RecommendationView.as_view(), name='recommendations'),
] 