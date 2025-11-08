from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, UniqueConstraint
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import re

# Create Blueprint for master data
master_data_bp = Blueprint('master_data', __name__)

# Database instance (will be initialized from main app)
db = None

def init_master_data(database):
    """Initialize the master data module with database instance"""
    global db, Partner, Product
    db = database
    
    # =============================================
    # SQLAlchemy Models
    # =============================================
    
    class Partner(db.Model):
        __tablename__ = 'partners'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(160), nullable=False, unique=True)
        type = Column(Enum('customer', 'vendor', 'both', name='partner_type'), nullable=False, default='customer')
        email = Column(String(190), nullable=True)
        phone = Column(String(40), nullable=True)
        tax_id = Column(String(50), nullable=True)
        billing_address = Column(Text, nullable=True)
        shipping_address = Column(Text, nullable=True)
        
        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'type': self.type,
                'email': self.email,
                'phone': self.phone,
                'tax_id': self.tax_id,
                'billing_address': self.billing_address,
                'shipping_address': self.shipping_address
            }

    class Product(db.Model):
        __tablename__ = 'products'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        sku = Column(String(60), nullable=False, unique=True)
        name = Column(String(160), nullable=False)
        description = Column(Text, nullable=True)
        uom = Column(String(30), nullable=False, default='unit')
        default_price = Column(DECIMAL(12, 2), nullable=False, default=0.00)
        
        def to_dict(self):
            return {
                'id': self.id,
                'sku': self.sku,
                'name': self.name,
                'description': self.description,
                'uom': self.uom,
                'default_price': float(self.default_price)
            }
    
    return Partner, Product

# =============================================
# Helper Functions
# =============================================

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_partner_type(partner_type):
    """Validate partner type"""
    valid_types = ['customer', 'vendor', 'both']
    return partner_type in valid_types

def handle_error(error, message="An error occurred"):
    """Standard error handler"""
    if isinstance(error, IntegrityError):
        if 'Duplicate entry' in str(error.orig):
            return jsonify({'error': 'Duplicate entry', 'details': 'Record with this name/SKU already exists'}), 400
        return jsonify({'error': 'Data integrity error', 'details': str(error.orig)}), 400
    elif isinstance(error, SQLAlchemyError):
        return jsonify({'error': 'Database error', 'details': str(error)}), 500
    else:
        return jsonify({'error': message, 'details': str(error)}), 500

# =============================================
# PARTNER CRUD Operations
# =============================================

@master_data_bp.route('/partners', methods=['GET'])
def get_all_partners():
    """Get all partners with optional filtering"""
    try:
        # Get query parameters
        partner_type = request.args.get('type')
        search = request.args.get('search')
        
        query = Partner.query
        
        # Filter by type if provided
        if partner_type and validate_partner_type(partner_type):
            query = query.filter(Partner.type == partner_type)
        
        # Search by name if provided
        if search:
            query = query.filter(Partner.name.ilike(f'%{search}%'))
        
        partners = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [partner.to_dict() for partner in partners],
            'count': len(partners),
            'filters': {
                'type': partner_type,
                'search': search
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch partners")

@master_data_bp.route('/partners/<int:partner_id>', methods=['GET'])
def get_partner(partner_id):
    """Get single partner by ID"""
    try:
        partner = Partner.query.get(partner_id)
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': partner.to_dict()
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch partner")

@master_data_bp.route('/partners', methods=['POST'])
def create_partner():
    """Create new partner"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Partner name is required'}), 400
        
        # Validate partner type
        partner_type = data.get('type', 'customer')
        if not validate_partner_type(partner_type):
            return jsonify({'error': 'Invalid partner type. Must be: customer, vendor, or both'}), 400
        
        # Validate email if provided
        if data.get('email') and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        partner = Partner(
            name=data['name'],
            type=partner_type,
            email=data.get('email'),
            phone=data.get('phone'),
            tax_id=data.get('tax_id'),
            billing_address=data.get('billing_address'),
            shipping_address=data.get('shipping_address')
        )
        
        db.session.add(partner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Partner created successfully',
            'data': partner.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create partner")

@master_data_bp.route('/partners/<int:partner_id>', methods=['PUT'])
def update_partner(partner_id):
    """Update existing partner"""
    try:
        partner = Partner.query.get(partner_id)
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'name' in data:
            partner.name = data['name']
        
        if 'type' in data:
            if not validate_partner_type(data['type']):
                return jsonify({'error': 'Invalid partner type. Must be: customer, vendor, or both'}), 400
            partner.type = data['type']
        
        if 'email' in data:
            if data['email'] and not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            partner.email = data['email']
        
        if 'phone' in data:
            partner.phone = data['phone']
        
        if 'tax_id' in data:
            partner.tax_id = data['tax_id']
        
        if 'billing_address' in data:
            partner.billing_address = data['billing_address']
        
        if 'shipping_address' in data:
            partner.shipping_address = data['shipping_address']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Partner updated successfully',
            'data': partner.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update partner")

@master_data_bp.route('/partners/<int:partner_id>', methods=['DELETE'])
def delete_partner(partner_id):
    """Delete partner"""
    try:
        partner = Partner.query.get(partner_id)
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        db.session.delete(partner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Partner deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete partner")

# =============================================
# PRODUCT CRUD Operations
# =============================================

@master_data_bp.route('/products', methods=['GET'])
def get_all_products():
    """Get all products with optional filtering"""
    try:
        # Get query parameters
        search = request.args.get('search')
        sku = request.args.get('sku')
        
        query = Product.query
        
        # Search by SKU if provided
        if sku:
            query = query.filter(Product.sku.ilike(f'%{sku}%'))
        
        # Search by name if provided
        elif search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        products = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [product.to_dict() for product in products],
            'count': len(products),
            'filters': {
                'search': search,
                'sku': sku
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch products")

@master_data_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': product.to_dict()
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch product")

@master_data_bp.route('/products/sku/<string:sku>', methods=['GET'])
def get_product_by_sku(sku):
    """Get product by SKU"""
    try:
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': product.to_dict()
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to fetch product")

@master_data_bp.route('/products', methods=['POST'])
def create_product():
    """Create new product"""
    try:
        data = request.get_json()
        
        if not data or 'sku' not in data or 'name' not in data:
            return jsonify({'error': 'SKU and name are required'}), 400
        
        # Validate default_price if provided
        default_price = data.get('default_price', 0.00)
        try:
            default_price = float(default_price)
            if default_price < 0:
                return jsonify({'error': 'Default price must be non-negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid default price format'}), 400
        
        product = Product(
            sku=data['sku'],
            name=data['name'],
            description=data.get('description'),
            uom=data.get('uom', 'unit'),
            default_price=default_price
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product created successfully',
            'data': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to create product")

@master_data_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'sku' in data:
            # Check if SKU already exists for another product
            existing_product = Product.query.filter_by(sku=data['sku']).first()
            if existing_product and existing_product.id != product_id:
                return jsonify({'error': 'SKU already exists'}), 400
            product.sku = data['sku']
        
        if 'name' in data:
            product.name = data['name']
        
        if 'description' in data:
            product.description = data['description']
        
        if 'uom' in data:
            product.uom = data['uom']
        
        if 'default_price' in data:
            try:
                default_price = float(data['default_price'])
                if default_price < 0:
                    return jsonify({'error': 'Default price must be non-negative'}), 400
                product.default_price = default_price
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid default price format'}), 400
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to update product")

@master_data_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return handle_error(e, "Failed to delete product")

# =============================================
# Search and Statistics Endpoints
# =============================================

@master_data_bp.route('/partners/search', methods=['GET'])
def search_partners():
    """Advanced partner search"""
    try:
        # Get query parameters
        name = request.args.get('name')
        partner_type = request.args.get('type')
        email = request.args.get('email')
        phone = request.args.get('phone')
        
        query = Partner.query
        
        if name:
            query = query.filter(Partner.name.ilike(f'%{name}%'))
        
        if partner_type and validate_partner_type(partner_type):
            query = query.filter(Partner.type == partner_type)
        
        if email:
            query = query.filter(Partner.email.ilike(f'%{email}%'))
        
        if phone:
            query = query.filter(Partner.phone.ilike(f'%{phone}%'))
        
        partners = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [partner.to_dict() for partner in partners],
            'count': len(partners),
            'search_criteria': {
                'name': name,
                'type': partner_type,
                'email': email,
                'phone': phone
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to search partners")

@master_data_bp.route('/products/search', methods=['GET'])
def search_products():
    """Advanced product search"""
    try:
        # Get query parameters
        name = request.args.get('name')
        sku = request.args.get('sku')
        uom = request.args.get('uom')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        
        query = Product.query
        
        if name:
            query = query.filter(Product.name.ilike(f'%{name}%'))
        
        if sku:
            query = query.filter(Product.sku.ilike(f'%{sku}%'))
        
        if uom:
            query = query.filter(Product.uom.ilike(f'%{uom}%'))
        
        if min_price:
            try:
                min_price_val = float(min_price)
                query = query.filter(Product.default_price >= min_price_val)
            except ValueError:
                return jsonify({'error': 'Invalid min_price format'}), 400
        
        if max_price:
            try:
                max_price_val = float(max_price)
                query = query.filter(Product.default_price <= max_price_val)
            except ValueError:
                return jsonify({'error': 'Invalid max_price format'}), 400
        
        products = query.all()
        
        return jsonify({
            'status': 'success',
            'data': [product.to_dict() for product in products],
            'count': len(products),
            'search_criteria': {
                'name': name,
                'sku': sku,
                'uom': uom,
                'min_price': min_price,
                'max_price': max_price
            }
        }), 200
    except Exception as e:
        return handle_error(e, "Failed to search products")

@master_data_bp.route('/master-data/stats', methods=['GET'])
def get_master_data_statistics():
    """Get master data statistics"""
    try:
        total_partners = Partner.query.count()
        customers = Partner.query.filter_by(type='customer').count()
        vendors = Partner.query.filter_by(type='vendor').count()
        both = Partner.query.filter_by(type='both').count()
        
        total_products = Product.query.count()
        products_with_price = Product.query.filter(Product.default_price > 0).count()
        
        # Get unique UOMs
        uoms = db.session.query(Product.uom).distinct().all()
        unique_uoms = [uom[0] for uom in uoms]
        
        return jsonify({
            'status': 'success',
            'data': {
                'partners': {
                    'total': total_partners,
                    'customers': customers,
                    'vendors': vendors,
                    'both': both
                },
                'products': {
                    'total': total_products,
                    'with_price': products_with_price,
                    'unique_uoms': unique_uoms,
                    'uom_count': len(unique_uoms)
                }
            }
        }), 200
        
    except Exception as e:
        return handle_error(e, "Failed to fetch statistics")