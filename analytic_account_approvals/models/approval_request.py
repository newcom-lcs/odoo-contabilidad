from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to apply manager-first logic"""
        records = super(ApprovalRequest, self).create(vals_list)
        
        # For each created record, check if we need to reorder approvers
        for record in records:
            if record.approver_sequence:
                _logger.info("CREATE - Ensuring manager first for approval request ID: %s", record.id)
                record._ensure_manager_first_approver()
                
        return records
    
    def write(self, vals):
        """Override write to handle approver changes"""
        _logger.info("WRITE - Approval request write with vals: %s", vals)
        
        result = super(ApprovalRequest, self).write(vals)
        
        # If relevant fields changed, reapply the manager-first logic
        if any(field in vals for field in ['approver_ids', 'approver_sequence', 'has_manager_approval']):
            for record in self:
                _logger.info("WRITE - Reordering triggered for approval request ID: %s", record.id)
                if record.approver_sequence:
                    record._ensure_manager_first_approver()
                    
        return result

    # Additional hooks into core approval methods
    def action_approve(self, approver=None):
        """Override to ensure manager is always first before approval happens"""
        if self.approver_sequence:
            self._ensure_manager_first_approver()
        return super(ApprovalRequest, self).action_approve(approver=approver)
    
    def action_refuse(self, approver=None):
        """Override to ensure manager is always first before refusal happens"""
        if self.approver_sequence:
            self._ensure_manager_first_approver()
        return super(ApprovalRequest, self).action_refuse(approver=approver)
    
    def _get_next_approvers(self):
        """Override to ensure manager approval comes first"""
        if self.approver_sequence:
            self._ensure_manager_first_approver()
        return super(ApprovalRequest, self)._get_next_approvers()
    
    def _ensure_manager_first_approver(self):
        """Ensure that the manager approval is always first in the sequence"""
        self.ensure_one()
        
        # Skip if there are no approvers or if request is already approved/refused
        if not self.approver_ids or self.request_status in ['approved', 'refused', 'cancel']:
            _logger.info("SKIP - No approvers or request already processed: %s", self.id)
            return
            
        # Get all approvers
        approvers = self.approver_ids.sorted(lambda a: a.sequence)
        
        # Debug info about all approvers
        for i, app in enumerate(approvers):
            _logger.info("APPROVER %s: ID: %s, User: %s, Sequence: %s, Required: %s", 
                        i, app.id, app.user_id.name, app.sequence, 
                        getattr(app, 'required', 'N/A'))
        
        # Get structure of Employee's Manager setting
        has_manager = getattr(self, 'has_manager_approval', None)
        _logger.info("HAS MANAGER APPROVAL attribute: %s", has_manager)
        
        # Find the manager approver (different ways to identify)
        manager_approver = self._identify_manager_approver(approvers)
        
        if not manager_approver:
            _logger.info("NO MANAGER - Could not identify a manager approver")
            return
            
        _logger.info("FOUND MANAGER: ID: %s, User: %s, Current Sequence: %s", 
                    manager_approver.id, manager_approver.user_id.name, manager_approver.sequence)
            
        # If manager is not the first approver, reorder the sequence
        if manager_approver != approvers[0]:
            _logger.info("REORDERING - Manager is not first, will reorder")
            
            # Check direct DB fields (debug)
            self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='approval_approver'")
            columns = [col[0] for col in self.env.cr.fetchall()]
            _logger.info("APPROVAL APPROVER COLUMNS: %s", columns)
            
            # Check what fields approval_approver has
            approver_fields = self.env['approval.approver']._fields.keys()
            _logger.info("APPROVAL APPROVER FIELDS: %s", list(approver_fields))
            
            # Temporarily suspend triggers
            self.env.cr.execute('SAVEPOINT reorder_approvers')
            
            # Try a more forceful approach - change all the sequences
            min_seq = -1000  # Very low sequence for manager
            
            # Set manager to extremely low sequence
            manager_approver.write({'sequence': min_seq})
            
            # Push all other approvers after manager
            other_approvers = self.approver_ids.filtered(lambda a: a.id != manager_approver.id)
            for i, approver in enumerate(other_approvers):
                approver.write({'sequence': min_seq + 10 + (i * 10)})
            
            # Also try direct SQL update
            self.env.cr.execute(
                """UPDATE approval_approver 
                   SET sequence = %s 
                   WHERE id = %s""", 
                (min_seq, manager_approver.id)
            )
            
            # Commit the changes
            self.env.cr.execute('RELEASE SAVEPOINT reorder_approvers')
            
            # Force a reload of the records from database
            self.env.cr.commit()  # Commit transaction to ensure changes are saved
            self.invalidate_cache()  # Clear cache to force reload

            # Check final sequence order
            approvers_after = self.approver_ids.sorted(lambda a: a.sequence)
            for i, app in enumerate(approvers_after):
                _logger.info("AFTER REORDER - APPROVER %s: ID: %s, User: %s, Sequence: %s", 
                            i, app.id, app.user_id.name, app.sequence)
    
    def _identify_manager_approver(self, approvers):
        """
        Identify the manager approver from the approvers list.
        Returns the manager approver record or None if not found.
        """
        self.ensure_one()
        
        # If no employee owner, we can't identify the manager
        if not self.request_owner_id:
            _logger.info("NO OWNER - Request has no owner")
            return None
            
        _logger.info("REQUEST OWNER: %s, Manager: %s", 
                   self.request_owner_id.name, 
                   self.request_owner_id.parent_id.name if self.request_owner_id.parent_id else "None")
        
        # Try to get more info about what's available
        request_fields = self._fields.keys()
        _logger.info("APPROVAL REQUEST FIELDS: %s", list(request_fields))
        
        # Check for specific fields in the model
        has_manager_field = 'has_manager_approval' in request_fields
        _logger.info("HAS MANAGER APPROVAL field exists: %s", has_manager_field)
        
        # Case 1: First try to check if any approver has manager = True (standard field in approval_approver)
        manager_approvers = None
        try:
            # In Odoo 16, the manager field is 'is_manager' in approval.approver
            if hasattr(approvers[0], 'is_manager'):
                manager_approvers = approvers.filtered(lambda a: a.is_manager)
                _logger.info("MANAGER CHECK A: Found %s approvers with is_manager=True", len(manager_approvers))
            # Fallback to required if is_manager doesn't exist
            elif hasattr(approvers[0], 'required'):
                manager_approvers = approvers.filtered(lambda a: a.required)
                _logger.info("MANAGER CHECK B: Found %s approvers with required=True", len(manager_approvers))
        except Exception as e:
            _logger.error("Error checking for manager attributes: %s", e)
        
        if manager_approvers:
            _logger.info("IDENTIFIED Manager via special field: %s", manager_approvers[0].user_id.name)
            return manager_approvers[0]
            
        # Case 2: Find by employee's manager
        if self.request_owner_id.parent_id and self.request_owner_id.parent_id.user_id:
            manager_user = self.request_owner_id.parent_id.user_id
            _logger.info("LOOKING for manager user: %s (ID: %s)", manager_user.name, manager_user.id)
            
            manager_approver = approvers.filtered(lambda a: a.user_id.id == manager_user.id)
            if manager_approver:
                _logger.info("IDENTIFIED Manager via parent_id: %s", manager_approver[0].user_id.name)
                return manager_approver[0]
        
        # Case 3: Someone with manager rights
        try:
            if self.user_has_groups('approvals.group_approval_manager'):
                manager_approvers = approvers.filtered(
                    lambda a: a.user_id.has_group('approvals.group_approval_manager')
                )
                if manager_approvers:
                    _logger.info("IDENTIFIED Manager via manager group: %s", manager_approvers[0].user_id.name)
                    return manager_approvers[0]
        except Exception as e:
            _logger.error("Error checking for manager groups: %s", e)
                
        # Case 4: Try a simple approach - see if "manager" is in any approver's name or job
        try:
            for approver in approvers:
                user = approver.user_id
                if user and user.employee_id and user.employee_id.job_id:
                    job_name = user.employee_id.job_id.name.lower()
                    if "manager" in job_name:
                        _logger.info("IDENTIFIED Manager via job title: %s", user.name)
                        return approver
        except Exception as e:
            _logger.error("Error checking for manager in job title: %s", e)
                
        # No manager found
        _logger.info("NO MANAGER identified after all attempts")
        return None 