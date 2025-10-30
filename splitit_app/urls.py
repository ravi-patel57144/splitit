from django.urls import path
from . import views

urlpatterns = [
    # Occasion URLs
    path('occasions/', views.OccasionListCreateView.as_view(), name='occasion-list-create'),
    path('occasions/<int:pk>/', views.OccasionDetailView.as_view(), name='occasion-detail'),
    path('occasions/<int:occasion_id>/summary/', views.occasion_summary, name='occasion-summary'),
    
    # Event URLs
    path('events/', views.EventListCreateView.as_view(), name='event-list-create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:event_id>/expenditures/', views.event_expenditures, name='event-expenditures'),
    
    # Expenditure URLs
    path('expenditures/', views.ExpenditureListCreateView.as_view(), name='expenditure-list-create'),
    path('expenditures/<int:pk>/', views.ExpenditureDetailView.as_view(), name='expenditure-detail'),
    
    # Payment URLs
    path('payments/', views.PaymentListCreateView.as_view(), name='payment-list-create'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    # New settlement endpoint tied to expenditure splits
    path('expenditure-splits/<int:split_id>/settle/', views.settle_expenditure_split, name='settle-expenditure-split'),
    
    # User balance URL
    path('user/balance/', views.user_balance, name='user-balance'),
]
