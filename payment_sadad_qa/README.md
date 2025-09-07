# SADAD (Qatar) Payment Provider for Odoo 17

## Overview

This module provides a comprehensive integration of the SADAD (Qatar) Web Checkout payment gateway with Odoo 17 Community Edition. It allows Odoo merchants to accept payments from customers in Qatar via SADAD's secure redirect-based payment flow.

The integration is designed to be robust, secure, and easy to manage, with features built for production environments.

## Key Features

*   **Redirect Payment Flow**: Customers are redirected to the secure SADAD Web Checkout page to complete their payment.
*   **Dynamic Settings**: All credentials (Merchant ID, Secret Keys) and settings (Environment, Language) are managed from a dedicated settings page within Odoo, requiring no code changes to switch between Test and Live modes.
*   **Secure Signature Verification**: Implements SADAD's official SHA-256 signature protocol for all requests, callbacks, and webhooks to prevent tampering and ensure data integrity.
*   **Webhook (IPN) Support**: Handles asynchronous payment updates from SADAD via webhooks for increased reliability.
*   **Transaction Status Mapping**: Automatically maps SADAD's payment statuses to the correct Odoo transaction states (Done, Canceled, Pending, Error).
*   **Financial Reconciliation Tool**: A powerful wizard to compare Odoo transactions against a SADAD statement CSV, highlighting discrepancies and making financial audits easier.
*   **Developer & Test Friendly**: Includes a Postman collection with pre-request scripts to easily test callback and webhook endpoints.

## Installation

### Docker
1.  Mount your custom addons directory. For example, if your module is in `./custom-addons/payment_sadad_qa`, add the following to your `docker-compose.yml`:
    ```yaml
    volumes:
      - ./custom-addons:/mnt/extra-addons
    ```
2.  Restart your Odoo container.
3.  Log in to Odoo, go to **Apps**, click **Update Apps List**, and remove the default "Apps" filter.
4.  Search for "SADAD" and click **Install**.

### Bare Metal
1.  Copy the `payment_sadad_qa` directory into your Odoo `addons` path.
2.  Restart the Odoo service.
3.  Log in to Odoo, enable developer mode, and go to **Apps**.
4.  Click **Update Apps List**, remove the "Apps" filter, search for "SADAD", and click **Install**.

## Configuration

### 1. Configure in Odoo

1.  Navigate to **Website ‣ Configuration ‣ SADAD Settings**.
2.  Fill in the following fields with the credentials from your SADAD Merchant Panel:
    *   **SADAD Merchant ID**: Your unique merchant identifier.
    *   **SADAD Test Secret Key**: The secret key for the test environment.
    *   **SADAD Live Secret Key**: The secret key for the production environment.
    *   **Environment**: Set to **Test** for development or **Production** for live payments.
    *   **Checkout Language**: Choose the default language for the SADAD payment page.
    *   **Debug Mode**: Enable this to log detailed information about payment requests and responses. **Do not use in production.**
3.  Click **Save**.

### 2. Configure in SADAD Merchant Panel

Log in to your SADAD Merchant Panel (`panel.sadad.qa`) and configure the following URLs. Replace `https://{{DOMAIN}}` with your Odoo instance's public domain.

*   **Webhook / IPN URL (JSON POST)**:
    ```
    https://{{DOMAIN}}/payment/sadad/notify
    ```
*   **Callback / Return URL**:
    This URL is sent with every payment request, so you don't need to configure a fixed return URL in the panel. The module will automatically send:
    ```
    https://{{DOMAIN}}/payment/sadad/return
    ```

### 3. Enable the Payment Provider

1.  Navigate to **Website ‣ Configuration ‣ Payment Providers**.
2.  Find **SADAD (Qatar)** in the list and open it.
3.  Change the **State** from **Disabled** to **Enabled**.
4.  (Optional) Configure availability, supported currencies, and payment icons as needed.

## Usage

### Paying for an Order
Once enabled, "SADAD (Qatar)" will appear as a payment option on your website's checkout page. When a customer selects it and clicks "Pay Now", they will be automatically redirected to the SADAD Web Checkout page. After the payment is completed, they will be redirected back to your Odoo store's payment status page.

### Reconciling Transactions
1.  Navigate to **Website ‣ Configuration ‣ SADAD Reconciliation**.
2.  Select the **From Date** and **To Date** for the period you want to reconcile.
3.  Upload the transaction statement CSV file provided by SADAD.
4.  Click **Run Reconciliation**.
5.  The results will appear in the **Results** tab below, with one of the following statuses:
    *   **OK**: The transaction exists in both Odoo and SADAD with the same amount.
    *   **Amount Mismatch**: The transaction exists in both systems, but the amounts differ.
    *   **Not in Odoo**: The transaction is in the SADAD statement but could not be found in Odoo.
    *   **Not in SADAD**: The transaction exists in Odoo but was not found in the SADAD statement.
6.  You can download the results as a CSV file for your records.

## Testing (UAT)
Before going live, perform these tests in the **Test** environment.

- [ ] Create a test Sales Order and proceed to checkout using SADAD. Verify you are redirected correctly.
- [ ] Complete a test payment successfully on the SADAD page. Verify you are redirected back to Odoo and the transaction is marked as **Done**.
- [ ] Simulate a webhook notification using the provided **Postman collection**. Verify a transaction's state can be updated via the webhook.
- [ ] Test the cancel flow by clicking "Cancel" on the SADAD page. Verify the transaction in Odoo is marked as **Canceled**.
- [ ] Use the Reconciliation wizard to match a test statement with your test transactions.
