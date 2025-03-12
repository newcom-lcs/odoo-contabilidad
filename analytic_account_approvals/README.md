# Analytic Account Approvals

This module extends the Odoo Approvals application by adding analytic account fields to approval request product lines.

## Features

- Adds analytic account field to approval product lines
- Adds analytic distribution field to approval product lines
- Automatically transfers the selected analytic account to purchase order lines when creating purchase orders from approvals

## Installation

1. Copy this module to your Odoo addons directory
2. Update your apps list
3. Install the "Analytic Account Approvals" module

## Usage

1. Create a new approval request
2. Add product lines to the request
3. Select an analytic account for each product line
4. When the approval generates a purchase order, the analytic account will be transferred to the purchase order lines

## Troubleshooting

If analytic accounts are not transferred to purchase orders:

1. Check Odoo logs for detailed information about what's happening during PO creation
2. Verify that users have access to analytic accounting features
3. Try updating the module to ensure the latest fixes are applied
4. Restart the Odoo server to ensure all module hooks are properly executed

## Requirements

- Odoo 16.0
- Approvals module
- Analytic module
- Purchase module

## License

LGPL-3 