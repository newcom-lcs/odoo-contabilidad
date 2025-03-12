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
    
    # Add the manager-first approval flow functionality
    @api.model
    def create(self, vals):
        """Override create to reorganize the approver sequence to prioritize manager approval"""
        res = super(ApprovalRequest, self).create(vals)
        if res.request_owner_id and res.request_owner_id.parent_id:
            # Reorder approvers to prioritize employee's manager
            res._reorder_approvers_prioritize_manager()
        return res
    
    def _reorder_approvers_prioritize_manager(self):
        """Reorder approvers to ensure the employee's manager comes first"""
        if not self.request_owner_id or not self.request_owner_id.parent_id:
            return
            
        # Try multiple ways to find the manager approver
        manager_approver = None
        
        # 1. Try to find manager by employee record
        manager = self.request_owner_id.parent_id
        manager_user = manager.user_id
        
        # 2. Direct match by manager's employee ID
        if not manager_approver and manager.id:
            manager_approver = self.approver_ids.filtered(
                lambda a: a.user_id.employee_id and a.user_id.employee_id.id == manager.id
            )
        
        # 3. Match by manager's user ID
        if not manager_approver and manager_user:
            manager_approver = self.approver_ids.filtered(
                lambda a: a.user_id.id == manager_user.id
            )
        
        # 4. Match by checking category - some companies use 'Manager' category
        if not manager_approver:
            # Try to find any approver who has 'Manager' in their job title or category
            manager_approver = self.approver_ids.filtered(
                lambda a: a.user_id.employee_id and 
                (a.user_id.employee_id.job_id and 'manager' in a.user_id.employee_id.job_id.name.lower() or
                a.user_id.has_group('hr.group_hr_manager'))
            )
            
            # If multiple managers found, pick the first one
            if manager_approver and len(manager_approver) > 1:
                manager_approver = manager_approver[0]
        
        # If no manager found and always_add_manager is True, add the manager
        if not manager_approver and self.always_add_manager and manager_user:
            # Store existing approvers
            existing_approvers = self.approver_ids
            
            # Add the manager as a new approver
            self.write({'approver_ids': [(0, 0, {
                'user_id': manager_user.id,
                'status': 'new',
                'request_id': self.id,
            })]})
            
            # Get the newly added manager approver
            manager_approver = self.approver_ids - existing_approvers
        
        # If manager is in the approver list, reorder to put them first
        if manager_approver:
            # Temporarily store all approvers
            all_approvers = self.approver_ids
            
            # Remove all approvers
            self.write({'approver_ids': [(5, 0, 0)]})
            
            # Add manager first
            self.write({'approver_ids': [(0, 0, {
                'user_id': manager_approver.user_id.id,
                'status': manager_approver.status,
                'request_id': self.id,
            })]})
            
            # Add all other approvers except the manager
            for approver in all_approvers.filtered(lambda a: a.id != manager_approver.id):
                self.write({'approver_ids': [(0, 0, {
                    'user_id': approver.user_id.id,
                    'status': approver.status,
                    'request_id': self.id,
                })]})
    
    def write(self, vals):
        """Override write to ensure approver sequence is maintained when approvers are modified"""
        result = super(ApprovalRequest, self).write(vals)
        
        # If approvers have been modified, reapply the ordering logic
        if 'approver_ids' in vals and self.request_owner_id and self.request_owner_id.parent_id:
            # Only reorder if the status of the request allows modifications to approvers
            if self.request_status in ['new', 'pending']:
                self._reorder_approvers_prioritize_manager()
                
        return result 