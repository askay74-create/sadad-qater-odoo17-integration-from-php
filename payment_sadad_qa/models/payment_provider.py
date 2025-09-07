# -*- coding: utf-8 -*-

import hashlib
import logging
from urllib.parse import urljoin
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SadadPaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sadad_qa', 'SADAD (Qatar)')],
        ondelete={'sadad_qa': 'set default'}
    )

    def _get_sadad_secret(self):
        """Return the secret key for the current environment."""
        self.ensure_one()
        config_sudo = self.env['ir.config_parameter'].sudo()
        environment = config_sudo.get_param('payment_sadad_qa.environment', 'test')
        key = 'live_secret' if environment == 'prod' else 'test_secret'
        secret = config_sudo.get_param(f'payment_sadad_qa.{key}')
        if not secret:
            _logger.warning(
                "SADAD: The secret key is not set for the '%s' environment.", environment
            )
        return secret

    def _get_sadad_urls(self):
        """Return the SADAD URLs for the current environment.

        Note: The prompt only provides one URL, so we use it for both test and prod.
        This can be updated if a separate test URL is provided by SADAD.
        """
        return {
            'sadad_form_url': 'https://sadadqa.com/webpurchase',
        }

    def _sadad_generate_signature(self, payload, is_notification=False):
        """Generate or verify the SADAD signature.

        :param dict payload: The data to sign.
        :param bool is_notification: If True, the payload is from a notification
                                     and the key 'checksumhash' should be excluded.
        :return: The generated SHA256 signature.
        :rtype: str
        """
        self.ensure_one()
        secret_key = self._get_sadad_secret()
        if not secret_key:
            raise ValidationError(_("SADAD: Secret key is not set for the current environment."))

        # For notifications, the signature key is 'checksumhash'. For requests, it's not present.
        # Array fields like 'productdetail' are also excluded.
        excluded_keys = ['checksumhash', 'signature']

        filtered_payload = {
            key: value for key, value in payload.items()
            if key not in excluded_keys and not key.startswith('productdetail[')
        }

        # Sort keys alphabetically (ASCII order)
        sorted_keys = sorted(filtered_payload.keys())

        # Concatenate the values of the sorted keys
        concatenated_values = "".join(str(filtered_payload[key]) for key in sorted_keys)

        # Prepend the secret key
        string_to_hash = secret_key + concatenated_values

        # Compute the SHA256 hash
        signature = hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()

        if self.env['ir.config_parameter'].sudo().get_param('payment_sadad_qa.debug'):
            _logger.info(
                "SADAD Signature Generation:\nString to Hash: %s\nGenerated Signature: %s",
                string_to_hash,
                signature
            )
        return signature

    def _get_rendering_context(self, transaction, render_spec=None):
        base_url = self.get_base_url()
        sadad_urls = self._get_sadad_urls()

        config_sudo = self.env['ir.config_parameter'].sudo()
        merchant_id = config_sudo.get_param('payment_sadad_qa.merchant_id')
        if not merchant_id:
            raise ValidationError(_("SADAD: Merchant ID is not configured."))

        # Use configured domain or fall back to base_url
        website_domain = config_sudo.get_param('payment_sadad_qa.website_domain')
        if not website_domain:
            website_domain = self.get_base_url().replace('https://', '').replace('http://', '')

        # Use partner phone or fall back to configured default
        default_mobile = config_sudo.get_param('payment_sadad_qa.default_mobile')
        mobile_no = transaction.partner_phone or default_mobile or ''

        product_details = []
        for line in transaction.sale_order_ids.order_line:
            product_details.append({
                'order_id': transaction.reference,
                'amount': "%.2f" % line.price_unit,
                'quantity': int(line.product_uom_qty),
                'itemname': line.name.replace("'", "").replace('"', ''), # Remove quotes from item names
            })

        payload = {
            'merchant_id': merchant_id,
            'ORDER_ID': transaction.reference,
            'WEBSITE': website_domain,
            'TXN_AMOUNT': "%.2f" % transaction.amount,
            'CALLBACK_URL': urljoin(base_url, '/payment/sadad/return'),
            'EMAIL': transaction.partner_email,
            'MOBILE_NO': mobile_no,
            'txnDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'SADAD_WEBCHECKOUT_PAGE_LANGUAGE': config_sudo.get_param('payment_sadad_qa.language', 'eng'),
            'productdetail': product_details,
        }

        payload['checksumhash'] = self._sadad_generate_signature(payload)

        return {
            'sadad_form_url': sadad_urls['sadad_form_url'],
            'payload': payload,
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the transaction from the notification data."""
        if provider_code != 'sadad_qa':
            # This check is redundant, Odoo already filters by provider.
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        tx_ref = notification_data.get('ORDERID') or notification_data.get('websiteRefNo')
        if not tx_ref:
            raise ValidationError("SADAD: Notification data did not contain a transaction reference (ORDERID or websiteRefNo).")

        tx = self.env['payment.transaction'].search([('reference', '=', tx_ref), ('provider_code', '=', 'sadad_qa')])
        if not tx:
            raise ValidationError(f"SADAD: Could not find transaction with reference '{tx_ref}'.")

        return tx
