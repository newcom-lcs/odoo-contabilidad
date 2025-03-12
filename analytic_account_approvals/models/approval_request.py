from odoo import api, fields, models

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # Add a field to control whether to automatically add the manager if not present
    always_add_manager = fields.Boolean(
        string="Always Include Manager Approval",
        default=True,
        help="If checked, the employee's manager will always be added as an approver"
    )

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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to apply manager-first logic"""
        records = super(ApprovalRequest, self).create(vals_list)
        
        # For each created record, check if we need to reorder approvers
        for record in records:
            if record.approver_sequence and (record.has_manager_approval or record.user_has_groups('approvals.group_approval_manager')):
                record._ensure_manager_first_approver()
                
        return records
    
    def write(self, vals):
        """Override write to handle approver changes"""
        result = super(ApprovalRequest, self).write(vals)
        
        # If relevant fields changed, reapply the manager-first logic
        if any(field in vals for field in ['approver_ids', 'approver_sequence', 'has_manager_approval']):
            for record in self:
                if record.approver_sequence and (record.has_manager_approval or record.user_has_groups('approvals.group_approval_manager')):
                    record._ensure_manager_first_approver()
                    
        return result
    
    def _ensure_manager_first_approver(self):
        """Ensure that the manager approval is always first in the sequence"""
        self.ensure_one()
        
        # Skip if there are no approvers or if request is already approved/refused
        if not self.approver_ids or self.request_status in ['approved', 'refused', 'cancel']:
            return
            
        # Get all approvers
        approvers = self.approver_ids.sorted(lambda a: a.sequence)
        
        # Find the manager approver (different ways to identify)
        manager_approver = self._identify_manager_approver(approvers)
        
        if not manager_approver:
            return
            
        # If manager is not the first approver, reorder the sequence
        if manager_approver != approvers[0]:
            # Temporarily suspend triggers
            self.env.cr.execute('SAVEPOINT reorder_approvers')
            
            # Set manager as first in sequence
            min_sequence = min(approvers.mapped('sequence')) - 1
            manager_approver.sequence = min_sequence
            
            # Commit the changes
            self.env.cr.execute('RELEASE SAVEPOINT reorder_approvers')
    
    def _identify_manager_approver(self, approvers):
        """
        Identify the manager approver from the approvers list.
        Returns the manager approver record or None if not found.
        """
        self.ensure_one()
        
        # If no employee owner, we can't identify the manager
        if not self.request_owner_id:
            return None
            
        # Case 1: Direct employee's manager approver
        # This is checking for manager approvers specifically added by the "Employee's Manager" checkbox
        manager_approvers = approvers.filtered(lambda a: a.required)
        if manager_approvers:
            return manager_approvers[0]
            
        # Case 2: Find by employee's manager
        if self.request_owner_id.parent_id and self.request_owner_id.parent_id.user_id:
            manager_user = self.request_owner_id.parent_id.user_id
            manager_approver = approvers.filtered(lambda a: a.user_id.id == manager_user.id)
            if manager_approver:
                return manager_approver[0]
        
        # Case 3: Someone with manager rights
        if self.user_has_groups('approvals.group_approval_manager'):
            manager_approvers = approvers.filtered(
                lambda a: a.user_id.has_group('approvals.group_approval_manager')
            )
            if manager_approvers:
                return manager_approvers[0]
                
        # No manager found
        return None 