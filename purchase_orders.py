"""
Purchase Orders Module
Handles purchase orders and purchase order lines with automatic total calculation
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, or_

# Global database reference
db = None

# Global model references
PurchaseOrder = None
PurchaseOrderLine = None

def init_purchase_orders(database):
    """
    Initialize the purchase orders module with the database instance.
    This pattern prevents circular import issues.
    """
    global db, PurchaseOrder, PurchaseOrderLine
    db = database
    
    class PurchaseOrder(db.Model):
        __tablename__ = 'purchase_orders'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        po_number = db.Column(db.String(40), nullable=False, unique=True)
        project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
        vendor_id = db.Column(db.Integer, db.ForeignKey('partners.id', ondelete='RESTRICT'), nullable=False)
        order_date = db.Column(db.Date, nullable=False)
        status = db.Column(db.Enum('draft', 'confirmed', 'cancelled', 'closed'), nullable=False, default='draft')
        currency = db.Column(db.String(3), nullable=False, default='INR')
        notes = db.Column(db.Text, nullable=True)
        
        # Relationships
        project = db.relationship('Project', backref='purchase_orders')
        vendor = db.relationship('Partner', backref='vendor_purchase_orders')
        lines = db.relationship('PurchaseOrderLine', backref='purchase_order', cascade='all, delete-orphan', lazy='dynamic')
        
        # Indexes are created via MySQL schema
        
        def to_dict(self, include_lines=False):
            """Convert purchase order to dictionary"""
            result = {
                'id': self.id,
                'po_number': self.po_number,
                'project_id': self.project_id,
                'project_name': self.project.name if self.project else None,
                'vendor_id': self.vendor_id,
                'vendor_name': self.vendor.name if self.vendor else None,
                'order_date': self.order_date.isoformat() if self.order_date else None,
                'status': self.status,
                'currency': self.currency,
                'notes': self.notes
            }
            
            if include_lines:
                lines_list = [line.to_dict() for line in self.lines.all()]
                result['lines'] = lines_list
                result['order_total'] = sum(float(line['line_total']) for line in lines_list)
            
            return result
    
    class PurchaseOrderLine(db.Model):
        __tablename__ = 'purchase_order_lines'
        
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
        description = db.Column(db.String(255), nullable=False)
        quantity = db.Column(db.Numeric(12, 4), nullable=False, default=1.0000)
        unit_cost = db.Column(db.Numeric(12, 2), nullable=False)
        
        # Relationship
        product = db.relationship('Product', backref='purchase_order_lines')
        
        @property
        def line_total(self):
            """Calculate line total (quantity * unit_cost)"""
            if self.quantity and self.unit_cost:
                return float(self.quantity) * float(self.unit_cost)
            return 0.0
        
        def to_dict(self):
            """Convert purchase order line to dictionary"""
            return {
                'id': self.id,
                'purchase_order_id': self.purchase_order_id,
                'product_id': self.product_id,
                'product_name': self.product.name if self.product else None,
                'description': self.description,
                'quantity': float(self.quantity) if self.quantity else 0,
                'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
                'line_total': self.line_total
            }
    
    return PurchaseOrder, PurchaseOrderLine


# Create Blueprint
purchase_orders_bp = Blueprint('purchase_orders', __name__)


# ============================================================================
# PURCHASE ORDER ENDPOINTS
# ============================================================================

@purchase_orders_bp.route('/purchase-orders', methods=['POST'])
def create_purchase_order():
    """Create a new purchase order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['po_number', 'project_id', 'vendor_id', 'order_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if PO number already exists
        existing = PurchaseOrder.query.filter_by(po_number=data['po_number']).first()
        if existing:
            return jsonify({'error': f'Purchase order with number {data["po_number"]} already exists'}), 400
        
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
        
        # Parse order date
        try:
            order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid order_date format. Use YYYY-MM-DD'}), 400
        
        # Validate status if provided
        valid_statuses = ['draft', 'confirmed', 'cancelled', 'closed']
        status = data.get('status', 'draft')
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Validate currency if provided
        currency = data.get('currency', 'INR')
        if len(currency) != 3:
            return jsonify({'error': 'Currency must be a 3-character code'}), 400
        
        # Create purchase order
        po = PurchaseOrder(
            po_number=data['po_number'],
            project_id=data['project_id'],
            vendor_id=data['vendor_id'],
            order_date=order_date,
            status=status,
            currency=currency,
            notes=data.get('notes')
        )
        
        db.session.add(po)
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order created successfully',
            'purchase_order': po.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders', methods=['GET'])
def get_purchase_orders():
    """Get all purchase orders with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        project_id = request.args.get('project_id', type=int)
        vendor_id = request.args.get('vendor_id', type=int)
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        # Build query
        query = PurchaseOrder.query
        
        if status:
            query = query.filter_by(status=status)
        if project_id:
            query = query.filter_by(project_id=project_id)
        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)
        
        # Order by order_date descending
        query = query.order_by(PurchaseOrder.order_date.desc())
        
        purchase_orders = query.all()
        
        return jsonify({
            'count': len(purchase_orders),
            'purchase_orders': [po.to_dict(include_lines=include_lines) for po in purchase_orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/<int:po_id>', methods=['GET'])
def get_purchase_order(po_id):
    """Get a specific purchase order by ID"""
    try:
        include_lines = request.args.get('include_lines', 'true').lower() == 'true'
        
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        return jsonify(po.to_dict(include_lines=include_lines)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/<int:po_id>', methods=['PUT'])
def update_purchase_order(po_id):
    """Update a purchase order"""
    try:
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        data = request.get_json()
        
        # Update po_number if provided
        if 'po_number' in data and data['po_number'] != po.po_number:
            existing = PurchaseOrder.query.filter_by(po_number=data['po_number']).first()
            if existing:
                return jsonify({'error': f'Purchase order with number {data["po_number"]} already exists'}), 400
            po.po_number = data['po_number']
        
        # Update project_id if provided
        if 'project_id' in data:
            from projects_teaming import Project
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({'error': f'Project with id {data["project_id"]} not found'}), 404
            po.project_id = data['project_id']
        
        # Update vendor_id if provided
        if 'vendor_id' in data:
            from master_data import Partner
            vendor = Partner.query.get(data['vendor_id'])
            if not vendor:
                return jsonify({'error': f'Vendor with id {data["vendor_id"]} not found'}), 404
            if vendor.type not in ['vendor', 'both']:
                return jsonify({'error': f'Partner {vendor.name} is not a vendor'}), 400
            po.vendor_id = data['vendor_id']
        
        # Update order_date if provided
        if 'order_date' in data:
            try:
                po.order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid order_date format. Use YYYY-MM-DD'}), 400
        
        # Update status if provided
        if 'status' in data:
            valid_statuses = ['draft', 'confirmed', 'cancelled', 'closed']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            po.status = data['status']
        
        # Update currency if provided
        if 'currency' in data:
            if len(data['currency']) != 3:
                return jsonify({'error': 'Currency must be a 3-character code'}), 400
            po.currency = data['currency']
        
        # Update notes if provided
        if 'notes' in data:
            po.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order updated successfully',
            'purchase_order': po.to_dict(include_lines=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/<int:po_id>', methods=['DELETE'])
def delete_purchase_order(po_id):
    """Delete a purchase order (will cascade delete all lines)"""
    try:
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        po_number = po.po_number
        db.session.delete(po)
        db.session.commit()
        
        return jsonify({
            'message': f'Purchase order {po_number} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PURCHASE ORDER LINE ENDPOINTS
# ============================================================================

@purchase_orders_bp.route('/purchase-orders/<int:po_id>/lines', methods=['POST'])
def create_purchase_order_line(po_id):
    """Create a new purchase order line"""
    try:
        # Verify purchase order exists
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['description', 'quantity', 'unit_cost']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate quantity
        try:
            quantity = Decimal(str(data['quantity']))
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid quantity value'}), 400
        
        # Validate unit_cost
        try:
            unit_cost = Decimal(str(data['unit_cost']))
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
        
        # Create purchase order line
        line = PurchaseOrderLine(
            purchase_order_id=po_id,
            product_id=product_id,
            description=data['description'],
            quantity=quantity,
            unit_cost=unit_cost
        )
        
        db.session.add(line)
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order line created successfully',
            'line': line.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/<int:po_id>/lines', methods=['GET'])
def get_purchase_order_lines(po_id):
    """Get all lines for a purchase order"""
    try:
        # Verify purchase order exists
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        lines = PurchaseOrderLine.query.filter_by(purchase_order_id=po_id).all()
        lines_data = [line.to_dict() for line in lines]
        order_total = sum(line['line_total'] for line in lines_data)
        
        return jsonify({
            'purchase_order_id': po_id,
            'po_number': po.po_number,
            'count': len(lines),
            'lines': lines_data,
            'order_total': order_total,
            'currency': po.currency
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-order-lines/<int:line_id>', methods=['GET'])
def get_purchase_order_line(line_id):
    """Get a specific purchase order line by ID"""
    try:
        line = PurchaseOrderLine.query.get(line_id)
        if not line:
            return jsonify({'error': 'Purchase order line not found'}), 404
        
        return jsonify(line.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-order-lines/<int:line_id>', methods=['PUT'])
def update_purchase_order_line(line_id):
    """Update a purchase order line"""
    try:
        line = PurchaseOrderLine.query.get(line_id)
        if not line:
            return jsonify({'error': 'Purchase order line not found'}), 404
        
        data = request.get_json()
        
        # Update product_id if provided
        if 'product_id' in data:
            if data['product_id'] is not None:
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
                quantity = Decimal(str(data['quantity']))
                if quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                line.quantity = quantity
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity value'}), 400
        
        # Update unit_cost if provided
        if 'unit_cost' in data:
            try:
                unit_cost = Decimal(str(data['unit_cost']))
                if unit_cost < 0:
                    return jsonify({'error': 'Unit cost cannot be negative'}), 400
                line.unit_cost = unit_cost
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid unit_cost value'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order line updated successfully',
            'line': line.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-order-lines/<int:line_id>', methods=['DELETE'])
def delete_purchase_order_line(line_id):
    """Delete a purchase order line"""
    try:
        line = PurchaseOrderLine.query.get(line_id)
        if not line:
            return jsonify({'error': 'Purchase order line not found'}), 404
        
        db.session.delete(line)
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order line deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADDITIONAL QUERY ENDPOINTS
# ============================================================================

@purchase_orders_bp.route('/purchase-orders/by-project/<int:project_id>', methods=['GET'])
def get_purchase_orders_by_project(project_id):
    """Get all purchase orders for a specific project"""
    try:
        from projects_teaming import Project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        purchase_orders = PurchaseOrder.query.filter_by(project_id=project_id)\
            .order_by(PurchaseOrder.order_date.desc()).all()
        
        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'count': len(purchase_orders),
            'purchase_orders': [po.to_dict(include_lines=include_lines) for po in purchase_orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/by-vendor/<int:vendor_id>', methods=['GET'])
def get_purchase_orders_by_vendor(vendor_id):
    """Get all purchase orders for a specific vendor"""
    try:
        from master_data import Partner
        vendor = Partner.query.get(vendor_id)
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
        if vendor.type not in ['vendor', 'both']:
            return jsonify({'error': f'Partner {vendor.name} is not a vendor'}), 400
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        purchase_orders = PurchaseOrder.query.filter_by(vendor_id=vendor_id)\
            .order_by(PurchaseOrder.order_date.desc()).all()
        
        return jsonify({
            'vendor_id': vendor_id,
            'vendor_name': vendor.name,
            'count': len(purchase_orders),
            'purchase_orders': [po.to_dict(include_lines=include_lines) for po in purchase_orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/by-status/<string:status>', methods=['GET'])
def get_purchase_orders_by_status(status):
    """Get all purchase orders with a specific status"""
    try:
        valid_statuses = ['draft', 'confirmed', 'cancelled', 'closed']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        purchase_orders = PurchaseOrder.query.filter_by(status=status)\
            .order_by(PurchaseOrder.order_date.desc()).all()
        
        return jsonify({
            'status': status,
            'count': len(purchase_orders),
            'purchase_orders': [po.to_dict(include_lines=include_lines) for po in purchase_orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_orders_bp.route('/purchase-orders/statistics', methods=['GET'])
def get_purchase_order_statistics():
    """Get statistics about purchase orders"""
    try:
        # Count by status
        status_counts = db.session.query(
            PurchaseOrder.status,
            func.count(PurchaseOrder.id)
        ).group_by(PurchaseOrder.status).all()
        
        # Total purchase orders
        total_pos = PurchaseOrder.query.count()
        
        # Get total spending by currency
        currency_totals = {}
        for po in PurchaseOrder.query.all():
            lines = po.lines.all()
            total = sum(float(line.line_total) for line in lines)
            if po.currency not in currency_totals:
                currency_totals[po.currency] = 0
            currency_totals[po.currency] += total
        
        return jsonify({
            'total_purchase_orders': total_pos,
            'by_status': {status: count for status, count in status_counts},
            'total_spending_by_currency': currency_totals
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
