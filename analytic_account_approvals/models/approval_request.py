from odoo import api, fields, models

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    def action_create_purchase_orders(self):
        """Override the standard method to create purchase orders with analytic accounts."""
        # Store the existing purchase orders before calling the original method
        existing_pos = self.env['purchase.order'].search([])
        
        # Call the original method to create purchase orders
        result = super(ApprovalRequest, self).action_create_purchase_orders()
        
        # Get newly created purchase orders by comparing with existing ones
        new_pos = self.env['purchase.order'].search([]) - existing_pos
        
        if not new_pos:
            return result
        
        # Update the purchase order lines with analytic information
        for po in new_pos:
            self._update_po_lines_with_analytics(po)
        
        return result
    
    def _update_po_lines_with_analytics(self, purchase_order):
        """Update purchase order lines with analytic account information"""
        for po_line in purchase_order.order_line:
            # Find matching approval lines by product
            matching_lines = self.product_line_ids.filtered(lambda l: l.product_id.id == po_line.product_id.id)
            
            if matching_lines:
                matched_line = matching_lines[0]  # Take the first one if multiple
                
                if matched_line.analytic_account_id:
                    po_line.write({
                        'analytic_distribution': {str(matched_line.analytic_account_id.id): 100}
                    })
                elif matched_line.analytic_distribution:
                    po_line.write({
                        'analytic_distribution': matched_line.analytic_distribution
                    }) 