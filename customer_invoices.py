"""
Customer Invoices Module
Handles customer invoices and invoice lines with automatic total calculation
Supports linking to sales orders, timesheets, and expenses
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, or_

# Global database reference
db = None

# Global model references
CustomerInvoice = None
CustomerInvoiceLine = None

def init_customer_invoices(database):
    """
    Initialize the customer invoices module with the database instance.
    This pattern prevents circular import issues.
    """
    global db, CustomerInvoice, CustomerInvoiceLine
    db = database
    
    class CustomerInvoice(db.Model):
        __tablename__ = 'customer_invoices'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        invoice_number = db.Column(db.String(40), nullable=False, unique=True)
        project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
        customer_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='RESTRICT'), nullable=False)
        invoice_date = db.Column(db.Date, nullable=False)
        due_date = db.Column(db.Date, nullable=True)
        status = db.Column(db.Enum('draft', 'posted', 'paid', 'void'), nullable=False, default='draft')
        currency = db.Column(db.String(3), nullable=False, default='INR')
        notes = db.Column(db.Text, nullable=True)
        
        # Relationships
        project = db.relationship('Project', backref='customer_invoices')
        customer = db.relationship('Partner', backref='customer_invoices')
        lines = db.relationship('CustomerInvoiceLine', backref='invoice', cascade='all, delete-orphan', lazy='dynamic')
        
        # Indexes are created via MySQL schema
        
        def to_dict(self, include_lines=False):
            """Convert customer invoice to dictionary"""
            result = {
                'id': self.id,
                'invoice_number': self.invoice_number,
                'project_id': self.project_id,
                'project_name': self.project.name if self.project else None,
                'customer_id': self.customer_id,
                'customer_name': self.customer.name if self.customer else None,
                'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'status': self.status,
                'currency': self.currency,
                'notes': self.notes
            }
            
            if include_lines:
                lines_list = [line.to_dict() for line in self.lines.all()]
                result['lines'] = lines_list
                result['invoice_total'] = sum(float(line['line_total']) for line in lines_list)
            
            return result
    
    class CustomerInvoiceLine(db.Model):
        __tablename__ = 'customer_invoice_lines'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        customer_invoice_id = db.Column(db.Integer, db.ForeignKey('customer_invoices.id', ondelete='CASCADE'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
        description = db.Column(db.String(255), nullable=False)
        quantity = db.Column(db.Numeric(12, 4), nullable=False, default=1.0000)
        unit_price = db.Column(db.Numeric(12, 2), nullable=False)
        sales_order_line_id = db.Column(db.Integer, db.ForeignKey('sales_order_lines.id', ondelete='SET NULL'), nullable=True)
        source_type = db.Column(db.Enum('timesheet', 'expense', 'manual', 'sales_order'), nullable=False, default='manual')
        source_id = db.Column(db.Integer, nullable=True)
        
        # Relationships
        product = db.relationship('Product', backref='invoice_lines')
        sales_order_line = db.relationship('SalesOrderLine', backref='invoice_lines')
        
        @property
        def line_total(self):
            """Calculate line total (quantity * unit_price)"""
            if self.quantity and self.unit_price:
                return float(self.quantity) * float(self.unit_price)
            return 0.0
        
        def to_dict(self):
            """Convert customer invoice line to dictionary"""
            return {
                'id': self.id,
                'customer_invoice_id': self.customer_invoice_id,
                'product_id': self.product_id,
                'product_name': self.product.name if self.product else None,
                'description': self.description,
                'quantity': float(self.quantity) if self.quantity else 0,
                'unit_price': float(self.unit_price) if self.unit_price else 0,
                'line_total': self.line_total,
                'sales_order_line_id': self.sales_order_line_id,
                'source_type': self.source_type,
                'source_id': self.source_id
            }
    
    return CustomerInvoice, CustomerInvoiceLine


# Create Blueprint
customer_invoices_bp = Blueprint('customer_invoices', __name__)


# ==================== CUSTOMER INVOICE ENDPOINTS ====================

@customer_invoices_bp.route('/customer-invoices', methods=['POST'])
def create_customer_invoice():
    """Create a new customer invoice"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['invoice_number', 'project_id', 'customer_id', 'invoice_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if invoice number already exists
        existing = CustomerInvoice.query.filter_by(invoice_number=data['invoice_number']).first()
        if existing:
            return jsonify({'error': f'Invoice with number {data["invoice_number"]} already exists'}), 400
        
        # Validate project exists
        from projects_teaming import Project
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': f'Project with id {data["project_id"]} not found'}), 404
        
        # Validate customer exists and is a customer
        from master_data import Partner
        customer = Partner.query.get(data['customer_id'])
        if not customer:
            return jsonify({'error': f'Customer with id {data["customer_id"]} not found'}), 404
        if customer.type not in ['customer', 'both']:
            return jsonify({'error': f'Partner {customer.name} is not a customer'}), 400
        
        # Parse invoice date
        try:
            invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid invoice_date format. Use YYYY-MM-DD'}), 400
        
        # Parse due date if provided
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid due_date format. Use YYYY-MM-DD'}), 400
        
        # Validate status if provided
        valid_statuses = ['draft', 'posted', 'paid', 'void']
        status = data.get('status', 'draft')
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Validate currency if provided
        currency = data.get('currency', 'INR')
        if len(currency) != 3:
            return jsonify({'error': 'Currency must be a 3-character code'}), 400
        
        # Create customer invoice
        invoice = CustomerInvoice(
            invoice_number=data['invoice_number'],
            project_id=data['project_id'],
            customer_id=data['customer_id'],
            invoice_date=invoice_date,
            due_date=due_date,
            status=status,
            currency=currency,
            notes=data.get('notes')
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        return jsonify({
            'message': 'Customer invoice created successfully',
            'invoice': invoice.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices', methods=['GET'])
def get_customer_invoices():
    """Get all customer invoices with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        project_id = request.args.get('project_id', type=int)
        customer_id = request.args.get('customer_id', type=int)
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        # Build query
        query = CustomerInvoice.query
        
        if status:
            query = query.filter_by(status=status)
        if project_id:
            query = query.filter_by(project_id=project_id)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        # Order by invoice_date descending
        query = query.order_by(CustomerInvoice.invoice_date.desc())
        
        invoices = query.all()
        
        return jsonify({
            'count': len(invoices),
            'invoices': [invoice.to_dict(include_lines=include_lines) for invoice in invoices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>', methods=['GET'])
def get_customer_invoice(invoice_id):
    """Get a specific customer invoice by ID"""
    try:
        invoice = CustomerInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': f'Invoice with id {invoice_id} not found'}), 404
        
        # Include lines by default for single invoice retrieval
        return jsonify(invoice.to_dict(include_lines=True)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>', methods=['PUT'])
def update_customer_invoice(invoice_id):
    """Update a customer invoice"""
    try:
        invoice = CustomerInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': f'Invoice with id {invoice_id} not found'}), 404
        
        data = request.get_json()
        
        # Update invoice number if provided and different
        if 'invoice_number' in data and data['invoice_number'] != invoice.invoice_number:
            existing = CustomerInvoice.query.filter_by(invoice_number=data['invoice_number']).first()
            if existing:
                return jsonify({'error': f'Invoice with number {data["invoice_number"]} already exists'}), 400
            invoice.invoice_number = data['invoice_number']
        
        # Update project if provided
        if 'project_id' in data:
            from projects_teaming import Project
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({'error': f'Project with id {data["project_id"]} not found'}), 404
            invoice.project_id = data['project_id']
        
        # Update customer if provided
        if 'customer_id' in data:
            from master_data import Partner
            customer = Partner.query.get(data['customer_id'])
            if not customer:
                return jsonify({'error': f'Customer with id {data["customer_id"]} not found'}), 404
            if customer.type not in ['customer', 'both']:
                return jsonify({'error': f'Partner {customer.name} is not a customer'}), 400
            invoice.customer_id = data['customer_id']
        
        # Update dates
        if 'invoice_date' in data:
            try:
                invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid invoice_date format. Use YYYY-MM-DD'}), 400
        
        if 'due_date' in data:
            if data['due_date']:
                try:
                    invoice.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid due_date format. Use YYYY-MM-DD'}), 400
            else:
                invoice.due_date = None
        
        # Update status
        if 'status' in data:
            valid_statuses = ['draft', 'posted', 'paid', 'void']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            invoice.status = data['status']
        
        # Update currency
        if 'currency' in data:
            if len(data['currency']) != 3:
                return jsonify({'error': 'Currency must be a 3-character code'}), 400
            invoice.currency = data['currency']
        
        # Update notes
        if 'notes' in data:
            invoice.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Customer invoice updated successfully',
            'invoice': invoice.to_dict(include_lines=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>', methods=['DELETE'])
def delete_customer_invoice(invoice_id):
    """Delete a customer invoice and all its lines (CASCADE)"""
    try:
        invoice = CustomerInvoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': f'Invoice with id {invoice_id} not found'}), 404
        
        invoice_number = invoice.invoice_number
        lines_count = invoice.lines.count()
        
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({
            'message': f'Invoice {invoice_number} and {lines_count} line(s) deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== CUSTOMER INVOICE LINE ENDPOINTS ====================

@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>/lines', methods=['POST'])
def create_invoice_line(invoice_id):
    """Create a new invoice line for a customer invoice"""
    try:
        # Verify invoice exists
        invoice = CustomerInvoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': f'Invoice with id {invoice_id} not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['description', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate quantity
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid quantity value'}), 400
        
        # Validate unit_price
        try:
            unit_price = float(data['unit_price'])
            if unit_price < 0:
                return jsonify({'error': 'Unit price cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid unit_price value'}), 400
        
        # Validate product if provided
        product_id = data.get('product_id')
        if product_id:
            from master_data import Product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product with id {product_id} not found'}), 404
        
        # Validate sales order line if provided
        sales_order_line_id = data.get('sales_order_line_id')
        if sales_order_line_id:
            from sales_orders import SalesOrderLine
            sol = SalesOrderLine.query.get(sales_order_line_id)
            if not sol:
                return jsonify({'error': f'Sales order line with id {sales_order_line_id} not found'}), 404
        
        # Validate source_type
        valid_source_types = ['timesheet', 'expense', 'manual', 'sales_order']
        source_type = data.get('source_type', 'manual')
        if source_type not in valid_source_types:
            return jsonify({'error': f'Invalid source_type. Must be one of: {", ".join(valid_source_types)}'}), 400
        
        # Create invoice line
        line = CustomerInvoiceLine(
            customer_invoice_id=invoice_id,
            product_id=product_id,
            description=data['description'],
            quantity=quantity,
            unit_price=unit_price,
            sales_order_line_id=sales_order_line_id,
            source_type=source_type,
            source_id=data.get('source_id')
        )
        
        db.session.add(line)
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice line created successfully',
            'line': line.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>/lines', methods=['GET'])
def get_invoice_lines(invoice_id):
    """Get all lines for a specific customer invoice"""
    try:
        invoice = CustomerInvoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': f'Invoice with id {invoice_id} not found'}), 404
        
        lines = invoice.lines.all()
        lines_data = [line.to_dict() for line in lines]
        
        return jsonify({
            'invoice_id': invoice_id,
            'invoice_number': invoice.invoice_number,
            'count': len(lines_data),
            'lines': lines_data,
            'total': sum(line['line_total'] for line in lines_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>/lines/<int:line_id>', methods=['GET'])
def get_invoice_line(invoice_id, line_id):
    """Get a specific invoice line"""
    try:
        line = CustomerInvoiceLine.query.get(line_id)
        
        if not line:
            return jsonify({'error': f'Invoice line with id {line_id} not found'}), 404
        
        if line.customer_invoice_id != invoice_id:
            return jsonify({'error': 'Invoice line does not belong to this invoice'}), 400
        
        return jsonify(line.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>/lines/<int:line_id>', methods=['PUT'])
def update_invoice_line(invoice_id, line_id):
    """Update an invoice line"""
    try:
        line = CustomerInvoiceLine.query.get(line_id)
        
        if not line:
            return jsonify({'error': f'Invoice line with id {line_id} not found'}), 404
        
        if line.customer_invoice_id != invoice_id:
            return jsonify({'error': 'Invoice line does not belong to this invoice'}), 400
        
        data = request.get_json()
        
        # Update product if provided
        if 'product_id' in data:
            if data['product_id']:
                from master_data import Product
                product = Product.query.get(data['product_id'])
                if not product:
                    return jsonify({'error': f'Product with id {data["product_id"]} not found'}), 404
            line.product_id = data['product_id']
        
        # Update description
        if 'description' in data:
            line.description = data['description']
        
        # Update quantity
        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                line.quantity = quantity
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity value'}), 400
        
        # Update unit_price
        if 'unit_price' in data:
            try:
                unit_price = float(data['unit_price'])
                if unit_price < 0:
                    return jsonify({'error': 'Unit price cannot be negative'}), 400
                line.unit_price = unit_price
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid unit_price value'}), 400
        
        # Update sales order line reference
        if 'sales_order_line_id' in data:
            if data['sales_order_line_id']:
                from sales_orders import SalesOrderLine
                sol = SalesOrderLine.query.get(data['sales_order_line_id'])
                if not sol:
                    return jsonify({'error': f'Sales order line with id {data["sales_order_line_id"]} not found'}), 404
            line.sales_order_line_id = data['sales_order_line_id']
        
        # Update source type and id
        if 'source_type' in data:
            valid_source_types = ['timesheet', 'expense', 'manual', 'sales_order']
            if data['source_type'] not in valid_source_types:
                return jsonify({'error': f'Invalid source_type. Must be one of: {", ".join(valid_source_types)}'}), 400
            line.source_type = data['source_type']
        
        if 'source_id' in data:
            line.source_id = data['source_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice line updated successfully',
            'line': line.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/<int:invoice_id>/lines/<int:line_id>', methods=['DELETE'])
def delete_invoice_line(invoice_id, line_id):
    """Delete an invoice line"""
    try:
        line = CustomerInvoiceLine.query.get(line_id)
        
        if not line:
            return jsonify({'error': f'Invoice line with id {line_id} not found'}), 404
        
        if line.customer_invoice_id != invoice_id:
            return jsonify({'error': 'Invoice line does not belong to this invoice'}), 400
        
        db.session.delete(line)
        db.session.commit()
        
        return jsonify({'message': 'Invoice line deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== QUERY & REPORTING ENDPOINTS ====================

@customer_invoices_bp.route('/projects/<int:project_id>/customer-invoices', methods=['GET'])
def get_project_invoices(project_id):
    """Get all customer invoices for a specific project"""
    try:
        from projects_teaming import Project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': f'Project with id {project_id} not found'}), 404
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        invoices = CustomerInvoice.query.filter_by(project_id=project_id)\
            .order_by(CustomerInvoice.invoice_date.desc()).all()
        
        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'count': len(invoices),
            'invoices': [invoice.to_dict(include_lines=include_lines) for invoice in invoices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customers/<int:customer_id>/customer-invoices', methods=['GET'])
def get_customer_invoices_by_customer(customer_id):
    """Get all customer invoices for a specific customer"""
    try:
        from master_data import Partner
        customer = Partner.query.get(customer_id)
        if not customer:
            return jsonify({'error': f'Customer with id {customer_id} not found'}), 404
        
        if customer.type not in ['customer', 'both']:
            return jsonify({'error': f'Partner {customer.name} is not a customer'}), 400
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        invoices = CustomerInvoice.query.filter_by(customer_id=customer_id)\
            .order_by(CustomerInvoice.invoice_date.desc()).all()
        
        return jsonify({
            'customer_id': customer_id,
            'customer_name': customer.name,
            'count': len(invoices),
            'invoices': [invoice.to_dict(include_lines=include_lines) for invoice in invoices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_invoices_bp.route('/customer-invoices/statistics', methods=['GET'])
def get_invoice_statistics():
    """Get statistics about customer invoices"""
    try:
        # Total invoices by status
        stats_by_status = db.session.query(
            CustomerInvoice.status,
            func.count(CustomerInvoice.id).label('count')
        ).group_by(CustomerInvoice.status).all()
        
        # Get all invoices with their lines for revenue calculation
        invoices = CustomerInvoice.query.all()
        
        revenue_by_status = {}
        revenue_by_currency = {}
        
        for invoice in invoices:
            lines = invoice.lines.all()
            total = sum(line.line_total for line in lines)
            
            # By status
            if invoice.status not in revenue_by_status:
                revenue_by_status[invoice.status] = 0
            revenue_by_status[invoice.status] += total
            
            # By currency
            if invoice.currency not in revenue_by_currency:
                revenue_by_currency[invoice.currency] = 0
            revenue_by_currency[invoice.currency] += total
        
        return jsonify({
            'total_invoices': len(invoices),
            'by_status': {status: count for status, count in stats_by_status},
            'revenue_by_status': revenue_by_status,
            'revenue_by_currency': revenue_by_currency
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
