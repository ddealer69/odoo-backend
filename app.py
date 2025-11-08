from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db_config import DATABASE_URI, DB_CONFIG
from user_management import user_management_bp, init_user_management
from master_data import master_data_bp, init_master_data
from projects_teaming import projects_teaming_bp, init_projects_teaming
from tasks_collaboration import tasks_collaboration_bp, init_tasks_collaboration
from sales_orders import sales_orders_bp, init_sales_orders
from purchase_orders import purchase_orders_bp, init_purchase_orders
from customer_invoices import customer_invoices_bp, init_customer_invoices
from vendor_bills import vendor_bills_bp, init_vendor_bills

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'connect_timeout': 10
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize user management module with database
Role, User, UserRole = init_user_management(db)

# Initialize master data module with database
Partner, Product = init_master_data(db)

# Initialize projects and teaming module with database
Project, ProjectMember = init_projects_teaming(db)

# Initialize tasks and collaboration module with database
Task, TaskAssignment, TaskComment, TaskAttachment = init_tasks_collaboration(db)

# Initialize sales orders module with database
SalesOrder, SalesOrderLine = init_sales_orders(db)

# Initialize purchase orders module with database
PurchaseOrder, PurchaseOrderLine = init_purchase_orders(db)

# Initialize customer invoices module with database
CustomerInvoice, CustomerInvoiceLine = init_customer_invoices(db)

# Initialize vendor bills module with database
VendorBill, VendorBillLine = init_vendor_bills(db)

# Register blueprints
app.register_blueprint(user_management_bp, url_prefix='/api/v1')
app.register_blueprint(master_data_bp, url_prefix='/api/v1')
app.register_blueprint(projects_teaming_bp, url_prefix='/api/v1')
app.register_blueprint(tasks_collaboration_bp, url_prefix='/api/v1')
app.register_blueprint(sales_orders_bp, url_prefix='/api/v1')
app.register_blueprint(purchase_orders_bp, url_prefix='/api/v1')
app.register_blueprint(customer_invoices_bp, url_prefix='/api/v1')
app.register_blueprint(vendor_bills_bp, url_prefix='/api/v1')

@app.route('/', methods=['GET'])
def health_check():
    """Health API endpoint to check if the API is working"""
    return jsonify({
        'status': 'success',
        'message': 'Health API is working perfectly!',
        'service': 'Flask SQLAlchemy Backend',
        'timestamp': '2025-11-08',
        'version': '1.0.0'
    }), 200

@app.route('/connection', methods=['GET'])
def test_database_connection():
    """Test database connection endpoint"""
    try:
        # Test the database connection by executing a simple query
        with db.engine.connect() as connection:
            result = connection.execute(text('SELECT 1 as test_value'))
            test_result = result.fetchone()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection is successful!',
            'database_info': {
                'host': DB_CONFIG['host'],
                'port': DB_CONFIG['port'],
                'database': DB_CONFIG['database'],
                'user': DB_CONFIG['user']
            },
            'test_query_result': test_result[0] if test_result else None,
            'connection_status': 'Connected successfully'
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed!',
            'error_type': 'SQLAlchemy Error',
            'error_details': str(e),
            'database_info': {
                'host': DB_CONFIG['host'],
                'port': DB_CONFIG['port'],
                'database': DB_CONFIG['database'],
                'user': DB_CONFIG['user']
            }
        }), 500
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Unexpected error occurred during connection test',
            'error_type': 'General Error',
            'error_details': str(e)
        }), 500

@app.route('/api/v1/init-db', methods=['POST'])
def initialize_database():
    """Initialize database tables"""
    try:
        # Create all tables (models are already imported)
        db.create_all()
        
        return jsonify({
            'status': 'success',
            'message': 'Database tables created successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to create database tables',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': ['/', '/connection']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("Starting Flask Application...")
    print(f"Database: {DB_CONFIG['database']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("Available endpoints:")
    print("  - GET /          : Health check API")
    print("  - GET /connection : Database connection test")
    print("\nStarting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)