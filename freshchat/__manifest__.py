{
    "name": "Freshchat Sync",
    "version": "1.1",
    "category": "Tools",
    "summary": "Sync Freshchat users and channels to Odoo",
    "author": "ChatGPT",
    "depends": ["base", "contacts"],
    "data": [
        "views/freshchat_user_views.xml",
        "views/freshchat_channel_views.xml",
        "views/freshchat_config_views.xml",
        "views/sync_now_wizard_views.xml",
        "data/cron.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": True,
}