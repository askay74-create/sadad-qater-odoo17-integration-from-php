# -*- coding: utf-8 -*-

import base64
import csv
import io
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SadadReconWizard(models.TransientModel):
    _name = 'sadad.recon.wizard'
    _description = 'SADAD Reconciliation Wizard'

    date_from = fields.Date(string="From Date", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="To Date", required=True, default=fields.Date.context_today)

    statement_file = fields.Binary(string="SADAD Statement", required=True)
    statement_filename = fields.Char()

    line_ids = fields.One2many('sadad.recon.line', 'wizard_id', string="Reconciliation Lines")

    recon_result_file = fields.Binary(string="Download Result", readonly=True)
    recon_result_filename = fields.Char(string="Result Filename", default="reconciliation_result.csv", readonly=True)

    def _get_sadad_statement_rows(self):
        """Parse the uploaded CSV file and return a list of dicts."""
        if not self.statement_file:
            raise UserError(_("You must upload a SADAD statement file."))

        try:
            decoded_file = base64.b64decode(self.statement_file).decode('utf-8')
            csv_rows = list(csv.DictReader(io.StringIO(decoded_file)))
            return csv_rows
        except Exception as e:
            _logger.error("Error parsing SADAD statement CSV: %s", e)
            raise UserError(_("Failed to parse the CSV file. Please ensure it is a valid, UTF-8 encoded CSV."))

    def _get_odoo_transactions(self):
        """Fetch Odoo transactions for the selected period."""
        domain = [
            ('provider_code', '=', 'sadad_qa'),
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('state', 'in', ['done', 'pending', 'authorized'])
        ]
        return self.env['payment.transaction'].search(domain)

    def action_run_reconciliation(self):
        self.ensure_one()
        self.line_ids.unlink() # Clear previous results

        sadad_txns = self._get_sadad_statement_rows()
        odoo_txns = self._get_odoo_transactions()

        # Normalize SADAD headers
        header_map = {
            'transactionNumber': 'sadad_ref', 'txnid': 'sadad_ref',
            'websiteRefNo': 'odoo_ref', 'ORDERID': 'odoo_ref',
            'txnAmount': 'amount', 'amount': 'amount',
            'transactionStatus': 'status', 'status': 'status',
            'txnDate': 'date', 'date': 'date',
        }

        normalized_sadad_txns = []
        for row in sadad_txns:
            normalized_row = {}
            for key, value in row.items():
                normalized_key = header_map.get(key.strip(), key.strip())
                normalized_row[normalized_key] = value
            normalized_sadad_txns.append(normalized_row)

        odoo_txs_by_ref = {tx.reference: tx for tx in odoo_txns}
        odoo_txs_by_provider_ref = {tx.provider_reference: tx for tx in odoo_txns if tx.provider_reference}

        processed_odoo_refs = set()
        recon_lines = []

        # Match SADAD transactions to Odoo transactions
        for sadad_tx in normalized_sadad_txns:
            odoo_tx = None
            sadad_ref = sadad_tx.get('sadad_ref')
            odoo_ref = sadad_tx.get('odoo_ref')

            if sadad_ref and sadad_ref in odoo_txs_by_provider_ref:
                odoo_tx = odoo_txs_by_provider_ref[sadad_ref]
            elif odoo_ref and odoo_ref in odoo_txs_by_ref:
                odoo_tx = odoo_txs_by_ref[odoo_ref]

            line_vals = {
                'sadad_tx_ref': sadad_ref,
                'odoo_tx_ref': odoo_ref,
                'sadad_amount': float(sadad_tx.get('amount', 0.0)),
                'transaction_date': fields.Date.to_date(sadad_tx.get('date', '').split(' ')[0]),
            }

            if odoo_tx:
                processed_odoo_refs.add(odoo_tx.reference)
                line_vals.update({
                    'odoo_tx_ref': odoo_tx.reference,
                    'odoo_amount': odoo_tx.amount,
                })
                if not odoo_tx.currency_id.is_zero(odoo_tx.amount - line_vals['sadad_amount']):
                    line_vals['status'] = 'AMOUNT_MISMATCH'
                else:
                    line_vals['status'] = 'OK'
            else:
                line_vals['status'] = 'NOT_IN_ODOO'

            recon_lines.append((0, 0, line_vals))

        # Find Odoo transactions not in SADAD statement
        unmatched_odoo_txs = odoo_txns.filtered(lambda tx: tx.reference not in processed_odoo_refs)
        for tx in unmatched_odoo_txs:
            recon_lines.append((0, 0, {
                'status': 'NOT_IN_SADAD',
                'odoo_tx_ref': tx.reference,
                'sadad_tx_ref': tx.provider_reference,
                'odoo_amount': tx.amount,
                'transaction_date': tx.create_date.date(),
            }))

        self.line_ids = recon_lines
        self._generate_result_csv()

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _generate_result_csv(self):
        """Generate a CSV from the reconciliation lines and store it for download."""
        if not self.line_ids:
            return

        output = io.StringIO()
        writer = csv.writer(output)

        header = ['Status', 'Odoo Reference', 'SADAD Reference', 'Odoo Amount', 'SADAD Amount', 'Date', 'Notes']
        writer.writerow(header)

        for line in self.line_ids:
            writer.writerow([
                line.status,
                line.odoo_tx_ref or '',
                line.sadad_tx_ref or '',
                line.odoo_amount,
                line.sadad_amount,
                line.transaction_date,
                line.notes or '',
            ])

        self.recon_result_file = base64.b64encode(output.getvalue().encode('utf-8'))
        self.recon_result_filename = f"sadad_recon_{fields.Date.today()}.csv"

    def action_export_odoo_tx(self):
        """Exports Odoo transactions for the given period to CSV."""
        self.ensure_one()
        odoo_txns = self._get_odoo_transactions()

        output = io.StringIO()
        writer = csv.writer(output)
        header = ['Odoo Reference', 'SADAD Reference', 'Amount', 'Currency', 'State', 'Date']
        writer.writerow(header)

        for tx in odoo_txns:
            writer.writerow([
                tx.reference,
                tx.provider_reference or '',
                tx.amount,
                tx.currency_id.name,
                tx.state,
                tx.create_date,
            ])

        b64_content = base64.b64encode(output.getvalue().encode('utf-8'))
        filename = f"odoo_sadad_txs_{self.date_from}_to_{self.date_to}.csv"

        return {
            'type': 'ir.actions.act_url',
            'url': f"data:text/csv;base64,{b64_content.decode()}",
            'target': 'self_download',
            'download': filename,
        }


class SadadReconLine(models.TransientModel):
    _name = 'sadad.recon.line'
    _description = 'SADAD Reconciliation Line'

    wizard_id = fields.Many2one('sadad.recon.wizard', string="Wizard", required=True, ondelete='cascade')

    status = fields.Selection([
        ('OK', 'OK'),
        ('AMOUNT_MISMATCH', 'Amount Mismatch'),
        ('NOT_IN_ODOO', 'Not in Odoo'),
        ('NOT_IN_SADAD', 'Not in SADAD')
    ], string="Status", readonly=True)

    odoo_tx_ref = fields.Char(string="Odoo Reference", readonly=True)
    sadad_tx_ref = fields.Char(string="SADAD Reference", readonly=True)
    odoo_amount = fields.Float(string="Odoo Amount", digits='Account', readonly=True)
    sadad_amount = fields.Float(string="SADAD Amount", digits='Account', readonly=True)
    transaction_date = fields.Date(string="Date", readonly=True)
    notes = fields.Char(string="Notes", readonly=True)
