# -*- coding: utf-8 -*-

import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _process_notification_data(self, notification_data):
        """
        Process notification data from SADAD and update the transaction state.
        This method is called by the controller after a notification is received.
        """
        # Let other providers process their notifications.
        if self.provider_code != 'sadad_qa':
            return super()._process_notification_data(notification_data)

        # --- 1. SIGNATURE VERIFICATION ---
        provider = self.provider_id
        if not provider:
            raise ValidationError("SADAD: The provider could not be found for transaction %s.", self.reference)

        received_signature = notification_data.get('checksumhash')
        if not received_signature:
            raise ValidationError("SADAD: Notification received for transaction %s without a signature (checksumhash).", self.reference)

        expected_signature = provider._sadad_generate_signature(notification_data, is_notification=True)

        if received_signature.lower() != expected_signature.lower():
            raise ValidationError(
                "SADAD: Invalid signature for transaction %s. "
                "Received '%s', expected '%s'.", self.reference, received_signature, expected_signature
            )

        if self.env['ir.config_parameter'].sudo().get_param('payment_sadad_qa.debug'):
            _logger.info("SADAD: Signature verified successfully for transaction %s.", self.reference)

        # --- 2. STATUS MAPPING ---
        # Callback from /payment/sadad/return (has 'STATUS' key)
        if 'STATUS' in notification_data:
            self._handle_callback_status(notification_data)

        # Webhook from /payment/sadad/notify (has 'transactionStatus' key)
        elif 'transactionStatus' in notification_data:
            self._handle_webhook_status(notification_data)

        else:
            self._set_error("Received a SADAD notification with an unknown format for transaction %s.", self.reference)

    def _handle_callback_status(self, data):
        """Handle status mapping for the redirect callback."""
        status = data.get('STATUS')
        resp_code = data.get('RESPCODE')
        provider_ref = data.get('TXNID')

        if status == 'TXN_SUCCESS' or resp_code == '1':
            self._set_done(provider_reference=provider_ref)
        elif status in ('FAILED', 'TXN_FAILED') or resp_code == '0':
            self._set_canceled(f"SADAD: Payment failed with status '{status}'.")
        else:
            self._set_error(f"SADAD: Received unhandled callback status '{status}'.")

    def _handle_webhook_status(self, data):
        """Handle status mapping for the server-to-server webhook."""
        status = data.get('transactionStatus')
        provider_ref = data.get('transactionNumber')

        if status == 3:  # Success
            self._set_done(provider_reference=provider_ref)
        elif status == 2:  # Failed
            self._set_canceled("SADAD: Payment failed per webhook.")
        elif status == 1:  # In Progress
            self._set_pending()
        else:
            self._set_error(f"SADAD: Received unhandled webhook status '{status}'.")
