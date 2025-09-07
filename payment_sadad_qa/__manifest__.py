# -*- coding: utf-8 -*-
{
    'name': 'SADAD QA Payment Provider',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Integrate SADAD (Qatar) Web Checkout with Odoo 17',
    'description': """
This module provides a fully integrated payment provider for the SADAD (Qatar) Web Checkout service.
It includes support for:
- Redirect payment flow
- Dynamic settings for Merchant ID, Secrets, and Environment (Test/Live)
- Secure signature verification for requests, callbacks, and webhooks
- Transaction status mapping
- A reconciliation tool to match Odoo transactions with SADAD statements.
    """,
    'author': 'Jules - AI Engineer',
    'website': 'https://www.minbeyti.com',
    'depends': [
        'payment',
        'website_sale',
    ],
    'data': [
        # Security must be loaded after the models' views are defined.
        # Views first, to ensure models are known and actions are created.
        'views/sadad_settings_views.xml',
        'views/payment_provider_views.xml',
        'views/payment_sadad_templates.xml',
        'views/sadad_recon_views.xml',
        # Menu items depend on actions in the views above.
        'views/menuitems.xml',
        # Data files can depend on views (e.g., for `redirect_form_view_id`).
        'data/payment_provider_data.xml',
        # Security file last is the safest approach.
        'security/ir.model.access.csv',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
