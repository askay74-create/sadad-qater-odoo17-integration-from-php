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
        'base_setup',
    ],
    'data': [
        # Views must be loaded before the data and security files that depend on them.
        'views/sadad_settings_views.xml',
        'views/payment_sadad_templates.xml',
        'views/sadad_recon_views.xml',
        'views/menuitems.xml',
        'data/payment_provider_data.xml',
        # Security file in XML format for more robust dependency handling.
        'security/sadad_security.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
