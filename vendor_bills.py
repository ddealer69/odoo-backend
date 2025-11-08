"""
Vendor Bills Module
Handles vendor bills and vendor bill lines with automatic total calculation
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, or_

# Global database reference
db = None

# Global model references
VendorBill = None
VendorBillLine = None

def init_vendor_bills(database):
    """
    Initialize the vendor bills module with the database instance.
    This pattern prevents circular import issues.
    """
    global db, VendorBill, VendorBillLine
    db = database
    
    class VendorBill(db.Model):
        __tablename__ = 'vendor_bills'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        bill_number = db.Column(db.String(40), nullable=False, unique=True)
        project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
        vendor_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='RESTRICT'), nullable=False)
        bill_date = db.Column(db.Date, nullable=False)
        due_date = db.Column(db.Date, nullable=True)
        status = db.Column(db.Enum('draft', 'posted', 'paid', 'void'), nullable=False, default='draft')
        currency = db.Column(db.String(3), nullable=False, default='INR')
        notes = db.Column(db.Text, nullable=True)
        
        # Relationships
        project = db.relationship('Project', backref='vendor_bills')
        vendor = db.relationship('Partner', backref='vendor_bills')
        lines = db.relationship('VendorBillLine', backref='vendor_bill', cascade='all, delete-orphan', lazy='dynamic')
        
        # Indexes are created via MySQL schema
        
        def to_dict(self, include_lines=False):
            """Convert vendor bill to dictionary"""
            result = {
                'id': self.id,
                'bill_number': self.bill_number,
                'project_id': self.project_id,
                'project_name': self.project.name if self.project else None,
                'vendor_id': self.vendor_id,
                'vendor_name': self.vendor.name if self.vendor else None,
                'bill_date': self.bill_date.isoformat() if self.bill_date else None,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'status': self.status,
                'currency': self.currency,
                'notes': self.notes
            }
            
            if include_lines:
                lines_list = [line.to_dict() for line in self.lines.all()]
                result['lines'] = lines_list
                result['bill_total'] = sum(float(line['line_total']) for line in lines_list)
            
            return result
    
    class VendorBillLine(db.Model):
        __tablename__ = 'vendor_bill_lines'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        vendor_bill_id = db.Column(db.Integer, db.ForeignKey('vendor_bills.id', ondelete='CASCADE'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
        description = db.Column(db.String(255), nullable=False)
        quantity = db.Column(db.Numeric(12, 4), nullable=False, default=1.0000)
        unit_cost = db.Column(db.Numeric(12, 2), nullable=False)
        purchase_order_line_id = db.Column(db.Integer, db.ForeignKey('purchase_order_lines.id', ondelete='SET NULL'), nullable=True)
        
        # Relationship
        product = db.relationship('Product', backref='vendor_bill_lines')
        purchase_order_line = db.relationship('PurchaseOrderLine', backref='vendor_bill_lines')
        
        @property
        def line_total(self):
            """Calculate line total (quantity * unit_cost)"""
            if self.quantity and self.unit_cost:
                return float(self.quantity) * float(self.unit_cost)
            return 0.0
        
        def to_dict(self):
            """Convert vendor bill line to dictionary"""
            return {
                'id': self.id,
                'vendor_bill_id': self.vendor_bill_id,
                'product_id': self.product_id,
                'product_name': self.product.name if self.product else None,
                'description': self.description,
                'quantity': float(self.quantity) if self.quantity else 0,
                'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
                'line_total': self.line_total,
                'purchase_order_line_id': self.purchase_order_line_id
            }
    
    return VendorBill, VendorBillLine


# Create Blueprint
vendor_bills_bp = Blueprint('vendor_bills', __name__)


@vendor_bills_bp.route('/vendor-bills', methods=['POST'])
def create_vendor_bill():
    """Create a new vendor bill"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bill_number', 'project_id', 'vendor_id', 'bill_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if bill number already exists
        existing = VendorBill.query.filter_by(bill_number=data['bill_number']).first()
        if existing:
            return jsonify({'error': f'Vendor bill with number {data["bill_number"]} already exists'}), 400
        
        # Validate project exists
        from projects_teaming import Project
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': f'Project with id {data["project_id"]} not found'}), 404
        
        # Validate vendor exists and is a vendor
        from master_data import Partner
        vendor = Partner.query.get(data['vendor_id'])
        if not vendor:
            return jsonify({'error': f'Vendor with id {data["vendor_id"]} not found'}), 404
        if vendor.type not in ['vendor', 'both']:
            return jsonify({'error': f'Partner {vendor.name} is not a vendor'}), 400
        
        # Parse bill date
        try:
            bill_date = datetime.strptime(data['bill_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid bill_date format. Use YYYY-MM-DD'}), 400
        
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
        
        # Create vendor bill
        vb = VendorBill(
            bill_number=data['bill_number'],
            project_id=data['project_id'],
            vendor_id=data['vendor_id'],
            bill_date=bill_date,
            due_date=due_date,
            status=status,
            currency=currency,
            notes=data.get('notes')
        )
        
        db.session.add(vb)
        db.session.commit()
        
        return jsonify({
            'message': 'Vendor bill created successfully',
            'vendor_bill': vb.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills', methods=['GET'])
def get_vendor_bills():
    """Get all vendor bills with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        project_id = request.args.get('project_id', type=int)
        vendor_id = request.args.get('vendor_id', type=int)
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        # Build query
        query = VendorBill.query
        
        if status:
            query = query.filter_by(status=status)
        if project_id:
            query = query.filter_by(project_id=project_id)
        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)
        
        # Order by bill_date descending
        query = query.order_by(VendorBill.bill_date.desc())
        
        vendor_bills = query.all()
        
        return jsonify({
            'count': len(vendor_bills),
            'vendor_bills': [vb.to_dict(include_lines=include_lines) for vb in vendor_bills]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>', methods=['GET'])
def get_vendor_bill(vb_id):
    """Get a specific vendor bill by ID"""
    try:
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        vb = VendorBill.query.get(vb_id)
        if not vb:
            return jsonify({'error': 'Vendor bill not found'}), 404
        
        return jsonify(vb.to_dict(include_lines=include_lines)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>', methods=['PUT'])
def update_vendor_bill(vb_id):
    """Update a vendor bill"""
    try:
        vb = VendorBill.query.get(vb_id)
        if not vb:
            return jsonify({'error': 'Vendor bill not found'}), 404
        
        data = request.get_json()
        
        # Update bill_number if provided and different
        if 'bill_number' in data and data['bill_number'] != vb.bill_number:
            existing = VendorBill.query.filter_by(bill_number=data['bill_number']).first()
            if existing:
                return jsonify({'error': f'Vendor bill with number {data["bill_number"]} already exists'}), 400
            vb.bill_number = data['bill_number']
        
        # Update project if provided
        if 'project_id' in data:
            from projects_teaming import Project
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({'error': f'Project with id {data["project_id"]} not found'}), 404
            vb.project_id = data['project_id']
        
        # Update vendor if provided
        if 'vendor_id' in data:
            from master_data import Partner
            vendor = Partner.query.get(data['vendor_id'])
            if not vendor:
                return jsonify({'error': f'Vendor with id {data["vendor_id"]} not found'}), 404
            if vendor.type not in ['vendor', 'both']:
                return jsonify({'error': f'Partner {vendor.name} is not a vendor'}), 400
            vb.vendor_id = data['vendor_id']
        
        # Update bill date if provided
        if 'bill_date' in data:
            try:
                vb.bill_date = datetime.strptime(data['bill_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid bill_date format. Use YYYY-MM-DD'}), 400
        
        # Update due date if provided
        if 'due_date' in data:
            if data['due_date']:
                try:
                    vb.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid due_date format. Use YYYY-MM-DD'}), 400
            else:
                vb.due_date = None
        
        # Update status if provided
        if 'status' in data:
            valid_statuses = ['draft', 'posted', 'paid', 'void']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            vb.status = data['status']
        
        # Update currency if provided
        if 'currency' in data:
            if len(data['currency']) != 3:
                return jsonify({'error': 'Currency must be a 3-character code'}), 400
            vb.currency = data['currency']
        
        # Update notes if provided
        if 'notes' in data:
            vb.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vendor bill updated successfully',
            'vendor_bill': vb.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>', methods=['DELETE'])
def delete_vendor_bill(vb_id):
    """Delete a vendor bill and its lines (CASCADE)"""
    try:
        vb = VendorBill.query.get(vb_id)
        if not vb:
            return jsonify({'error': 'Vendor bill not found'}), 404
        
        bill_number = vb.bill_number
        db.session.delete(vb)
        db.session.commit()
        
        return jsonify({
            'message': f'Vendor bill {bill_number} and all its lines deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== VENDOR BILL LINES ENDPOINTS ====================

@vendor_bills_bp.route('/vendor-bills/<int:vb_id>/lines', methods=['POST'])
def create_vendor_bill_line(vb_id):
    """Create a new vendor bill line"""
    try:
        # Check if vendor bill exists
        vb = VendorBill.query.get(vb_id)
        if not vb:
            return jsonify({'error': 'Vendor bill not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['description', 'quantity', 'unit_cost']
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
        
        # Validate unit_cost
        try:
            unit_cost = float(data['unit_cost'])
            if unit_cost < 0:
                return jsonify({'error': 'Unit cost cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid unit_cost value'}), 400
        
        # Validate product if provided
        product_id = data.get('product_id')
        if product_id:
            from master_data import Product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product with id {product_id} not found'}), 404
        
        # Validate purchase order line if provided
        po_line_id = data.get('purchase_order_line_id')
        if po_line_id:
            from purchase_orders import PurchaseOrderLine
            po_line = PurchaseOrderLine.query.get(po_line_id)
            if not po_line:
                return jsonify({'error': f'Purchase order line with id {po_line_id} not found'}), 404
        
        # Create vendor bill line
        line = VendorBillLine(
            vendor_bill_id=vb_id,
            product_id=product_id,
            description=data['description'],
            quantity=quantity,
            unit_cost=unit_cost,
            purchase_order_line_id=po_line_id
        )
        
        db.session.add(line)
        db.session.commit()
        
        return jsonify({
            'message': 'Vendor bill line created successfully',
            'line': line.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>/lines', methods=['GET'])
def get_vendor_bill_lines(vb_id):
    """Get all lines for a vendor bill"""
    try:
        vb = VendorBill.query.get(vb_id)
        if not vb:
            return jsonify({'error': 'Vendor bill not found'}), 404
        
        lines = VendorBillLine.query.filter_by(vendor_bill_id=vb_id).all()
        lines_data = [line.to_dict() for line in lines]
        
        return jsonify({
            'vendor_bill_id': vb_id,
            'bill_number': vb.bill_number,
            'count': len(lines_data),
            'lines': lines_data,
            'bill_total': sum(line['line_total'] for line in lines_data),
            'currency': vb.currency
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>/lines/<int:line_id>', methods=['GET'])
def get_vendor_bill_line(vb_id, line_id):
    """Get a specific vendor bill line"""
    try:
        line = VendorBillLine.query.filter_by(id=line_id, vendor_bill_id=vb_id).first()
        if not line:
            return jsonify({'error': 'Vendor bill line not found'}), 404
        
        return jsonify(line.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>/lines/<int:line_id>', methods=['PUT'])
def update_vendor_bill_line(vb_id, line_id):
    """Update a vendor bill line"""
    try:
        line = VendorBillLine.query.filter_by(id=line_id, vendor_bill_id=vb_id).first()
        if not line:
            return jsonify({'error': 'Vendor bill line not found'}), 404
        
        data = request.get_json()
        
        # Update product if provided
        if 'product_id' in data:
            if data['product_id']:
                from master_data import Product
                product = Product.query.get(data['product_id'])
                if not product:
                    return jsonify({'error': f'Product with id {data["product_id"]} not found'}), 404
            line.product_id = data['product_id']
        
        # Update description if provided
        if 'description' in data:
            line.description = data['description']
        
        # Update quantity if provided
        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                line.quantity = quantity
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity value'}), 400
        
        # Update unit_cost if provided
        if 'unit_cost' in data:
            try:
                unit_cost = float(data['unit_cost'])
                if unit_cost < 0:
                    return jsonify({'error': 'Unit cost cannot be negative'}), 400
                line.unit_cost = unit_cost
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid unit_cost value'}), 400
        
        # Update purchase order line if provided
        if 'purchase_order_line_id' in data:
            if data['purchase_order_line_id']:
                from purchase_orders import PurchaseOrderLine
                po_line = PurchaseOrderLine.query.get(data['purchase_order_line_id'])
                if not po_line:
                    return jsonify({'error': f'Purchase order line with id {data["purchase_order_line_id"]} not found'}), 404
            line.purchase_order_line_id = data['purchase_order_line_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vendor bill line updated successfully',
            'line': line.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/<int:vb_id>/lines/<int:line_id>', methods=['DELETE'])
def delete_vendor_bill_line(vb_id, line_id):
    """Delete a vendor bill line"""
    try:
        line = VendorBillLine.query.filter_by(id=line_id, vendor_bill_id=vb_id).first()
        if not line:
            return jsonify({'error': 'Vendor bill line not found'}), 404
        
        db.session.delete(line)
        db.session.commit()
        
        return jsonify({
            'message': 'Vendor bill line deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== QUERY & STATISTICS ENDPOINTS ====================

@vendor_bills_bp.route('/projects/<int:project_id>/vendor-bills', methods=['GET'])
def get_project_vendor_bills(project_id):
    """Get all vendor bills for a specific project"""
    try:
        from projects_teaming import Project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        vendor_bills = VendorBill.query.filter_by(project_id=project_id).order_by(VendorBill.bill_date.desc()).all()
        
        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'count': len(vendor_bills),
            'vendor_bills': [vb.to_dict(include_lines=include_lines) for vb in vendor_bills]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendors/<int:vendor_id>/bills', methods=['GET'])
def get_vendor_bills_by_vendor(vendor_id):
    """Get all vendor bills for a specific vendor"""
    try:
        from master_data import Partner
        vendor = Partner.query.get(vendor_id)
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
        
        if vendor.type not in ['vendor', 'both']:
            return jsonify({'error': 'Partner is not a vendor'}), 400
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        vendor_bills = VendorBill.query.filter_by(vendor_id=vendor_id).order_by(VendorBill.bill_date.desc()).all()
        
        return jsonify({
            'vendor_id': vendor_id,
            'vendor_name': vendor.name,
            'count': len(vendor_bills),
            'vendor_bills': [vb.to_dict(include_lines=include_lines) for vb in vendor_bills]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vendor_bills_bp.route('/vendor-bills/statistics', methods=['GET'])
def get_vendor_bill_statistics():
    """Get vendor bill statistics"""
    try:
        total_bills = VendorBill.query.count()
        
        # Count by status
        status_counts = db.session.query(
            VendorBill.status,
            func.count(VendorBill.id)
        ).group_by(VendorBill.status).all()
        
        status_breakdown = {status: count for status, count in status_counts}
        
        # Calculate total spending by currency
        vendor_bills = VendorBill.query.all()
        spending_by_currency = {}
        
        for vb in vendor_bills:
            lines = vb.lines.all()
            total = sum(line.line_total for line in lines)
            if vb.currency in spending_by_currency:
                spending_by_currency[vb.currency] += total
            else:
                spending_by_currency[vb.currency] = total
        
        return jsonify({
            'total_bills': total_bills,
            'status_breakdown': status_breakdown,
            'spending_by_currency': spending_by_currency
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
