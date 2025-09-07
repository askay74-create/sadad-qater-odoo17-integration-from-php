# -*- coding: utf-8 -*-

import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SadadController(http.Controller):
    _return_url = '/payment/sadad/return'
    _cancel_url = '/payment/sadad/cancel'
    _notify_url = '/payment/sadad/notify'

    @http.route(_return_url, type='http', auth='public', methods=['POST'], csrf=False, save_session=False)
    def sadad_return_from_checkout(self, **data):
        """
        Process the callback from SADAD after a customer attempts payment.
        This route handles both successful and failed payments.
        """
        if request.env['ir.config_parameter'].sudo().get_param('payment_sadad_qa.debug'):
            _logger.info("SADAD: Handling return from checkout with data:\n%s", pprint.pformat(data))

        # Pass the notification data to the payment framework for processing.
        request.env['payment.transaction']._handle_notification_data('sadad_qa', data)

        # Redirect the user to the standard payment status page.
        return request.redirect('/payment/status')

    @http.route(_cancel_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def sadad_cancel_from_checkout(self, **data):
        """
        Handle the customer cancelling the payment process on the SADAD page.
        We assume SADAD sends back the transaction reference even on cancellation.
        """
        if request.env['ir.config_parameter'].sudo().get_param('payment_sadad_qa.debug'):
            _logger.info("SADAD: Handling cancel from checkout with data:\n%s", pprint.pformat(data))

        # We process the data similarly to the return URL. The transaction state
        # will be set to 'cancel' based on the status in the payload.
        request.env['payment.transaction']._handle_notification_data('sadad_qa', data)

        return request.redirect('/payment/status')

    @http.route(_notify_url, type='json', auth='public', csrf=False)
    def sadad_webhook_notification(self):
        """
        Process the server-to-server webhook notification from SADAD.
        This is used for asynchronous payment status updates.
        """
        payload = request.jsonrequest
        if request.env['ir.config_parameter'].sudo().get_param('payment_sadad_qa.debug'):
            _logger.info("SADAD: Handling webhook notification with data:\n%s", pprint.pformat(payload))

        try:
            # The JSON payload is passed to the payment framework.
            if payload:
                request.env['payment.transaction']._handle_notification_data('sadad_qa', payload)
        except Exception as e:
            # Log any exceptions but do not return an error status code,
            # otherwise SADAD might retry sending the same webhook.
            _logger.error("SADAD: Error processing webhook notification: %s", e, exc_info=True)

        # Return an empty 200 OK response to acknowledge receipt.
        return {}
