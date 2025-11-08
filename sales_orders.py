from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Date, DECIMAL, Boolean, Enum, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, date

# Create Blueprint for sales orders
sales_orders_bp = Blueprint('sales_orders', __name__)

# Database instance (will be initialized from main app)
db = None

def init_sales_orders(database):
    """Initialize the sales orders module with database instance"""
    global db, SalesOrder, SalesOrderLine
    db = database
    
    # =============================================
    # SQLAlchemy Models
    # =============================================
    
    class SalesOrder(db.Model):
        __tablename__ = 'sales_orders'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        so_number = Column(String(40), nullable=False, unique=True)
        project_id = Column(Integer, ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
        customer_id = Column(Integer, ForeignKey('partners.id', ondelete='RESTRICT'), nullable=False)
        order_date = Column(Date, nullable=False)
        status = Column(Enum('draft', 'confirmed', 'cancelled', 'closed', name='sales_order_status'), 
                       nullable=False, default='draft')
        currency = Column(String(3), nullable=False, default='INR')
        notes = Column(Text, nullable=True)
        
        # Relationships
        project = relationship('Project', foreign_keys=[project_id])
        customer = relationship('Partner', foreign_keys=[customer_id])
        lines = relationship('SalesOrderLine', back_populates='sales_order', cascade='all, delete-orphan')
        
        def to_dict(self, include_relations=False, include_lines=False):
            order_data = {
                'id': self.id,
                'so_number': self.so_number,
                'project_id': self.project_id,
                'customer_id': self.customer_id,
                'order_date': self.order_date.isoformat() if self.order_date else None,
                'status': self.status,
                'currency': self.currency,
                'notes': self.notes
            }
            
            if include_relations:
                order_data['project'] = {
                    'id': self.project.id,
                    'project_code': self.project.project_code,
                    'name': self.project.name,
                    'status': self.project.status
                } if self.project else None
                
                order_data['customer'] = {
                    'id': self.customer.id,
                    'name': self.customer.name,
                    'type': self.customer.type,
                    'email': self.customer.email,
                    'phone': self.customer.phone
                } if self.customer else None
            
            if include_lines:
                order_data['lines'] = [line.to_dict() for line in self.lines]
                order_data['line_count'] = len(self.lines)
                # Calculate total from lines
                order_data['order_total'] = sum(
                    float(line.quantity) * float(line.unit_price) 
                    for line in self.lines
                )
            
            return order_data

    class SalesOrderLine(db.Model):
        __tablename__ = 'sales_order_lines'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        sales_order_id = Column(Integer, ForeignKey('sales_orders.id', ondelete='CASCADE'), nullable=False)
        product_id = Column(Integer, ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
        description = Column(String(255), nullable=False)
        quantity = Column(DECIMAL(12, 4), nullable=False, default=1.0000)
        unit_price = Column(DECIMAL(12, 2), nullable=False)
        milestone_flag = Column(Boolean, nullable=False, default=False)
        
        # Relationships
        sales_order = relationship('SalesOrder', back_populates='lines')
        product = relationship('Product')
        
        @property
        def line_total(self):
            """Calculate line total"""
            return float(self.quantity) * float(self.unit_price)
        
        def to_dict(self, include_relations=False):
            line_data = {
                'id': self.id,
                'sales_order_id': self.sales_order_id,
                'product_id': self.product_id,
                'description': self.description,
                'quantity': float(self.quantity),
                'unit_price': float(self.unit_price),
                'line_total': self.line_total,
                'milestone_flag': self.milestone_flag
            }
            
            if include_relations:
                line_data['product'] = {
                    'id': self.product.id,
                    'sku': self.product.sku,
                    'name': self.product.name,
                    'default_price': float(self.product.default_price) if self.product.default_price else None
                } if self.product else None
                
                if self.sales_order:
                    line_data['sales_order'] = {
                        'id': self.sales_order.id,
                        'so_number': self.sales_order.so_number,
                        'status': self.sales_order.status,
                        'order_date': self.sales_order.order_date.isoformat() if self.sales_order.order_date else None
                    }
            
            return line_data
    
    return SalesOrder, SalesOrderLine

# =============================================
# Helper Functions
# =============================================

def validate_status(status):
    """Validate sales order status"""
    valid_statuses = ['draft', 'confirmed', 'cancelled', 'closed']
    return status in valid_statuses

def validate_currency(currency):
    """Validate currency code (basic validation)"""
    return currency and len(currency) == 3 and currency.isalpha()

def validate_date_string(date_string):
    """Validate and parse date string"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def handle_error(error, message="An error occurred"):
    """Standard error handler"""
    if isinstance(error, IntegrityError):
        if 'Duplicate entry' in str(error.orig):
            return jsonify({'error': 'Duplicate entry', 'details': 'SO number already exists'}), 400
        elif 'foreign key constraint fails' in str(error.orig):
            return jsonify({'error': 'Reference error', 'details': 'Referenced project, customer, or product does not exist'}), 400
        elif 'CONSTRAINT' in str(error.orig):
            return jsonify({'error': 'Constraint violation', 'details': str(error.orig)}), 400
        return jsonify({'error': 'Data integrity error', 'details': str(error.orig)}), 400
    elif isinstance(error, SQLAlchemyError):
        return jsonify({'error': 'Database error', 'details': str(error)}), 500
    else:
        return jsonify({'error': message, 'details': str(error)}), 500

# =============================================
# SALES ORDER CRUD Operations
# =============================================

@sales_orders_bp.route('/sales-orders', methods=['GET'])
def get_all_sales_orders():
    """Get all sales orders with optional filtering"""
    try:
        status = request.args.get('status')
        project_id = request.args.get('project_id')
        customer_id = request.args.get('customer_id')
        include_relations = request.args.get('include_relations', 'false').lower() == 'true'
        include_lines = request.args.get('include_lines', 'false').lower() == 'true'
        
        query = SalesOrder.query
        
        if status and validate_status(status):
            query = query.filter(SalesOrder.status == status)
        
        if project_id:
            query = query.filter(SalesOrder.project_id == project_id)
        
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        
        orders = query.order_by(SalesOrder.order_date.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [order.to_dict(include_relations=include_relations, include_lines=include_lines) 
                    for order in orders],
            'count': len(orders),
            'filters': {
                'status': status,
                'project_id': project_id,
                'customer_id': customer_id
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch sales orders")

@sales_orders_bp.route('/sales-orders/<int:order_id>', methods=['GET'])
def get_sales_order(order_id):
    """Get single sales order by ID with all details"""
    try:
        order = SalesOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Sales order not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': order.to_dict(include_relations=True, include_lines=True)
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch sales order")

@sales_orders_bp.route('/sales-orders', methods=['POST'])
def create_sales_order():
    """Create new sales order"""
    try:
        data = request.get_json()
        
        if not data or 'so_number' not in data or 'project_id' not in data or 'customer_id' not in data or 'order_date' not in data:
            return jsonify({'error': 'so_number, project_id, customer_id, and order_date are required'}), 400
        
        # Validate status if provided
        status = data.get('status', 'draft')
        if not validate_status(status):
            return jsonify({'error': 'Invalid status. Must be: draft, confirmed, cancelled, or closed'}), 400
        
        # Validate currency if provided
        currency = data.get('currency', 'INR')
        if not validate_currency(currency):
            return jsonify({'error': 'Invalid currency. Must be a 3-letter currency code'}), 400
        
        # Validate order_date
        try:
            order_date = validate_date_string(data['order_date'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Check if project exists
        from projects_teaming import Project
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if customer exists and is a customer or both type
        from master_data import Partner
        customer = Partner.query.get(data['customer_id'])
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        if customer.type not in ['customer', 'both']:
            return jsonify({'error': 'Partner must be a customer or both type'}), 400
        
        sales_order = SalesOrder(
            so_number=data['so_number'],
            project_id=data['project_id'],
            customer_id=data['customer_id'],
            order_date=order_date,
            status=status,
            currency=currency.upper(),
            notes=data.get('notes')
        )
        
        db.session.add(sales_order)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sales order created successfully',
            'data': sales_order.to_dict(include_relations=True, include_lines=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create sales order")

@sales_orders_bp.route('/sales-orders/<int:order_id>', methods=['PUT'])
def update_sales_order(order_id):
    """Update existing sales order"""
    try:
        order = SalesOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Sales order not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'so_number' in data:
            # Check if SO number already exists for another order
            existing_order = SalesOrder.query.filter_by(so_number=data['so_number']).first()
            if existing_order and existing_order.id != order_id:
                return jsonify({'error': 'SO number already exists'}), 400
            order.so_number = data['so_number']
        
        if 'status' in data:
            if not validate_status(data['status']):
                return jsonify({'error': 'Invalid status. Must be: draft, confirmed, cancelled, or closed'}), 400
            order.status = data['status']
        
        if 'currency' in data:
            if not validate_currency(data['currency']):
                return jsonify({'error': 'Invalid currency. Must be a 3-letter currency code'}), 400
            order.currency = data['currency'].upper()
        
        if 'order_date' in data:
            try:
                order.order_date = validate_date_string(data['order_date'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        if 'project_id' in data:
            from projects_teaming import Project
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            order.project_id = data['project_id']
        
        if 'customer_id' in data:
            from master_data import Partner
            customer = Partner.query.get(data['customer_id'])
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            if customer.type not in ['customer', 'both']:
                return jsonify({'error': 'Partner must be a customer or both type'}), 400
            order.customer_id = data['customer_id']
        
        if 'notes' in data:
            order.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sales order updated successfully',
            'data': order.to_dict(include_relations=True, include_lines=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update sales order")

@sales_orders_bp.route('/sales-orders/<int:order_id>', methods=['DELETE'])
def delete_sales_order(order_id):
    """Delete sales order"""
    try:
        order = SalesOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Sales order not found'}), 404
        
        # Get line count before deletion
        line_count = len(order.lines)
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Sales order deleted successfully (removed {line_count} order lines)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete sales order")

# =============================================
# SALES ORDER LINE CRUD Operations
# =============================================

@sales_orders_bp.route('/sales-orders/<int:order_id>/lines', methods=['GET'])
def get_order_lines(order_id):
    """Get all lines for a sales order"""
    try:
        order = SalesOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Sales order not found'}), 404
        
        lines = SalesOrderLine.query.filter_by(sales_order_id=order_id).all()
        
        # Calculate total
        order_total = sum(line.line_total for line in lines)
        
        return jsonify({
            'status': 'success',
            'data': [line.to_dict(include_relations=True) for line in lines],
            'count': len(lines),
            'order_total': order_total,
            'sales_order': {
                'id': order.id,
                'so_number': order.so_number,
                'status': order.status,
                'currency': order.currency
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch order lines")

@sales_orders_bp.route('/sales-orders/<int:order_id>/lines', methods=['POST'])
def create_order_line(order_id):
    """Create new sales order line"""
    try:
        data = request.get_json()
        
        if not data or 'description' not in data or 'unit_price' not in data:
            return jsonify({'error': 'description and unit_price are required'}), 400
        
        # Check if sales order exists
        order = SalesOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Sales order not found'}), 404
        
        # Validate quantity
        quantity = data.get('quantity', 1.0)
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid quantity format'}), 400
        
        # Validate unit_price
        try:
            unit_price = float(data['unit_price'])
            if unit_price < 0:
                return jsonify({'error': 'Unit price cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid unit price format'}), 400
        
        # Check if product exists (if provided)
        product_id = data.get('product_id')
        if product_id:
            from master_data import Product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
        
        order_line = SalesOrderLine(
            sales_order_id=order_id,
            product_id=product_id,
            description=data['description'],
            quantity=quantity,
            unit_price=unit_price,
            milestone_flag=data.get('milestone_flag', False)
        )
        
        db.session.add(order_line)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sales order line created successfully',
            'data': order_line.to_dict(include_relations=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create order line")

@sales_orders_bp.route('/sales-orders/<int:order_id>/lines/<int:line_id>', methods=['PUT'])
def update_order_line(order_id, line_id):
    """Update existing sales order line"""
    try:
        line = SalesOrderLine.query.filter_by(id=line_id, sales_order_id=order_id).first()
        if not line:
            return jsonify({'error': 'Sales order line not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'description' in data:
            line.description = data['description']
        
        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                line.quantity = quantity
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity format'}), 400
        
        if 'unit_price' in data:
            try:
                unit_price = float(data['unit_price'])
                if unit_price < 0:
                    return jsonify({'error': 'Unit price cannot be negative'}), 400
                line.unit_price = unit_price
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid unit price format'}), 400
        
        if 'product_id' in data:
            if data['product_id']:
                from master_data import Product
                product = Product.query.get(data['product_id'])
                if not product:
                    return jsonify({'error': 'Product not found'}), 404
            line.product_id = data['product_id']
        
        if 'milestone_flag' in data:
            line.milestone_flag = bool(data['milestone_flag'])
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sales order line updated successfully',
            'data': line.to_dict(include_relations=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update order line")

@sales_orders_bp.route('/sales-orders/<int:order_id>/lines/<int:line_id>', methods=['DELETE'])
def delete_order_line(order_id, line_id):
    """Delete sales order line"""
    try:
        line = SalesOrderLine.query.filter_by(id=line_id, sales_order_id=order_id).first()
        if not line:
            return jsonify({'error': 'Sales order line not found'}), 404
        
        db.session.delete(line)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sales order line deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete order line")

# =============================================
# Additional Endpoints
# =============================================

@sales_orders_bp.route('/projects/<int:project_id>/sales-orders', methods=['GET'])
def get_project_sales_orders(project_id):
    """Get all sales orders for a project"""
    try:
        from projects_teaming import Project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        status = request.args.get('status')
        
        query = SalesOrder.query.filter_by(project_id=project_id)
        
        if status and validate_status(status):
            query = query.filter(SalesOrder.status == status)
        
        orders = query.order_by(SalesOrder.order_date.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [order.to_dict(include_relations=True, include_lines=True) for order in orders],
            'count': len(orders),
            'project': {
                'id': project.id,
                'project_code': project.project_code,
                'name': project.name
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch project sales orders")

@sales_orders_bp.route('/customers/<int:customer_id>/sales-orders', methods=['GET'])
def get_customer_sales_orders(customer_id):
    """Get all sales orders for a customer"""
    try:
        from master_data import Partner
        customer = Partner.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        orders = SalesOrder.query.filter_by(customer_id=customer_id).order_by(SalesOrder.order_date.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [order.to_dict(include_relations=True, include_lines=True) for order in orders],
            'count': len(orders),
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'type': customer.type,
                'email': customer.email
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch customer sales orders")

@sales_orders_bp.route('/sales-orders/stats', methods=['GET'])
def get_sales_order_statistics():
    """Get sales order statistics"""
    try:
        total_orders = SalesOrder.query.count()
        
        # Count by status
        draft_orders = SalesOrder.query.filter_by(status='draft').count()
        confirmed_orders = SalesOrder.query.filter_by(status='confirmed').count()
        cancelled_orders = SalesOrder.query.filter_by(status='cancelled').count()
        closed_orders = SalesOrder.query.filter_by(status='closed').count()
        
        # Calculate total order value (confirmed orders only)
        confirmed_order_ids = [o.id for o in SalesOrder.query.filter_by(status='confirmed').all()]
        total_lines = SalesOrderLine.query.filter(SalesOrderLine.sales_order_id.in_(confirmed_order_ids)).all() if confirmed_order_ids else []
        total_revenue = sum(line.line_total for line in total_lines)
        
        # Count lines
        total_lines_count = SalesOrderLine.query.count()
        milestone_lines = SalesOrderLine.query.filter_by(milestone_flag=True).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'orders': {
                    'total': total_orders,
                    'by_status': {
                        'draft': draft_orders,
                        'confirmed': confirmed_orders,
                        'cancelled': cancelled_orders,
                        'closed': closed_orders
                    }
                },
                'lines': {
                    'total_lines': total_lines_count,
                    'milestone_lines': milestone_lines,
                    'regular_lines': total_lines_count - milestone_lines
                },
                'revenue': {
                    'total_confirmed_revenue': round(total_revenue, 2),
                    'currency': 'INR'
                }
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch statistics")

@sales_orders_bp.route('/sales-order-lines', methods=['GET'])
def get_all_order_lines():
    """Get all sales order lines with optional filtering"""
    try:
        sales_order_id = request.args.get('sales_order_id')
        product_id = request.args.get('product_id')
        milestone_only = request.args.get('milestone_only', 'false').lower() == 'true'
        
        query = SalesOrderLine.query
        
        if sales_order_id:
            query = query.filter(SalesOrderLine.sales_order_id == sales_order_id)
        
        if product_id:
            query = query.filter(SalesOrderLine.product_id == product_id)
        
        if milestone_only:
            query = query.filter(SalesOrderLine.milestone_flag == True)
        
        lines = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [line.to_dict(include_relations=True) for line in lines],
            'count': len(lines)
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch order lines")
