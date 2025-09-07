# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sadad_merchant_id = fields.Char(
        string="SADAD Merchant ID",
        config_parameter='payment_sadad_qa.merchant_id',
        help="The Merchant ID provided by SADAD."
    )
    sadad_test_secret = fields.Char(
        string="SADAD Test Secret Key",
        config_parameter='payment_sadad_qa.test_secret',
        help="The Test Secret Key from the SADAD merchant panel."
    )
    sadad_live_secret = fields.Char(
        string="SADAD Live Secret Key",
        config_parameter='payment_sadad_qa.live_secret',
        help="The Live Secret Key from the SADAD merchant panel."
    )
    sadad_environment = fields.Selection(
        [('test', 'Test'), ('prod', 'Production')],
        string="Environment",
        config_parameter='payment_sadad_qa.environment',
        default='test',
        required=True,
        help="Set to Test for development and testing, or Production for live transactions."
    )
    sadad_language = fields.Selection(
        [('eng', 'English'), ('arb', 'Arabic')],
        string="Checkout Language",
        config_parameter='payment_sadad_qa.language',
        default='eng',
        required=True,
        help="The default language for the SADAD checkout page."
    )
    sadad_debug = fields.Boolean(
        string="Debug Mode",
        config_parameter='payment_sadad_qa.debug',
        help="Enable to log detailed API requests and responses for debugging purposes."
    )

    sadad_website_domain = fields.Char(
        string="Website Domain",
        config_parameter='payment_sadad_qa.website_domain',
        help="The domain name to be sent as the WEBSITE parameter. If blank, Odoo's base URL will be used."
    )
    sadad_default_mobile = fields.Char(
        string="Default Mobile Number",
        config_parameter='payment_sadad_qa.default_mobile',
        help="A fallback mobile number to use if the customer does not have one on their record."
    )
