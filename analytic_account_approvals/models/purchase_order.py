from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def write(self, vals):
        """Override write to detect when lines are added to an existing PO"""
        result = super(PurchaseOrder, self).write(vals)
        
        # Check if order_line is in vals, meaning lines were added/modified
        if 'order_line' in vals:
            self._apply_analytics_from_approvals()
            
        return result
    
    def _apply_analytics_from_approvals(self):
        """Find approval requests that could be related to this PO and apply analytics"""
        ApprovalRequest = self.env['approval.request']
        
        # Get active approvals without using state filter
        approvals = ApprovalRequest.search([])
        
        for po_line in self.order_line:
            # Skip lines that already have analytic distribution
            if po_line.analytic_distribution:
                continue
                
            # Look for matching approval lines by product
            for approval in approvals:
                if not hasattr(approval, 'product_line_ids'):
                    continue
                    
                matching_lines = approval.product_line_ids.filtered(
                    lambda l: l.product_id.id == po_line.product_id.id
                )
                
                if matching_lines:
                    matched_line = matching_lines[0]  # Take the first one if multiple
                    
                    if matched_line.analytic_account_id:
                        po_line.write({
                            'analytic_distribution': {str(matched_line.analytic_account_id.id): 100}
                        })
                        break
                    elif matched_line.analytic_distribution:
                        po_line.write({
                            'analytic_distribution': matched_line.analytic_distribution
                        })
                        break 