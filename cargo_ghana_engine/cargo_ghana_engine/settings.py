INSTALLED_APPS = [
    'jazzmin',
    // ... existing code ...
]

# Jazzmin Settings
JAZZMIN_SETTINGS = {
    "site_title": "CargoGhana Admin",
    "site_header": "CargoGhana",
    "site_brand": "CargoGhana",
    "welcome_sign": "Welcome to CargoGhana Admin",
    "copyright": "CargoGhana Ltd",
    
    # Custom Menu
    "order_with_respect_to": [
        "bookings",
        "agents",
        "referrals",
        "tracking",
        "accounts",
    ],
    
    # Custom Icons
    "icons": {
        "bookings.Booking": "fas fa-box",
        "agents.AgentApplication": "fas fa-user-tie",
        "referrals.Referral": "fas fa-share-alt",
        "tracking.ContainerProgress": "fas fa-shipping-fast",
    },
    
    # Dashboard customization
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
}