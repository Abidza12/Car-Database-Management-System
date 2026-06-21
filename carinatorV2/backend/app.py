from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Serve static files (CSS, JS, images, etc.)
@app.route('/frontend/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_FOLDER, path)

# Serve index.html for root path
@app.route('/')
def index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:filename>')
def serve_frontend_files(filename):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.css', '.js', '.svg')):
        return send_from_directory(FRONTEND_FOLDER, filename)
    from flask import abort
    abort(404)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'carinator.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS brands (
            brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            country_of_origin TEXT NOT NULL,
            founded_date TEXT
        );

        CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            production_date TEXT,
            description TEXT,
            produced_for_country TEXT,
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS features (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS car_features (
            car_id INTEGER NOT NULL,
            feature_id INTEGER NOT NULL,
            PRIMARY KEY (car_id, feature_id),
            FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE,
            FOREIGN KEY (feature_id) REFERENCES features(feature_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, car_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            note_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, car_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
        );
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM brands')
    if cursor.fetchone()[0] == 0:
        # Add sample brands
        brands_data = [
            ('Toyota', 'Japan', '1937'),
            ('Ford', 'USA', '1903'),
            ('BMW', 'Germany', '1916'),
            ('Ferrari', 'Italy', '1939'),
            ('Tesla', 'USA', '2003'),
            ('Mercedes-Benz', 'Germany', '1926'),
            ('Honda', 'Japan', '1948'),
            ('Porsche', 'Germany', '1931')
        ]
        cursor.executemany('INSERT INTO brands (brand_name, country_of_origin, founded_date) VALUES (?, ?, ?)', brands_data)
        
        features_data = [
            ('Electric', 'Fully electric powertrain'),
            ('Hybrid', 'Combination of electric and gasoline power'),
            ('AWD', 'All-wheel drive system'),
            ('Turbo', 'Turbocharged engine'),
            ('Autopilot', 'Advanced driver assistance system'),
            ('Sunroof', 'Panoramic sunroof'),
            ('Leather Seats', 'Premium leather interior'),
            ('Navigation', 'Built-in GPS navigation system'),
            ('Bluetooth', 'Wireless connectivity'),
            ('Backup Camera', 'Rear-view camera system')
        ]
        cursor.executemany('INSERT INTO features (feature_name, description) VALUES (?, ?)', features_data)
        
        cars_data = [
            ('Camry', 1, 'XSE', '2024', 'Reliable mid-size sedan with excellent fuel economy', 'USA'),
            ('Corolla', 1, 'LE', '2024', 'Compact sedan known for reliability', 'Global'),
            ('Mustang', 2, 'GT', '2024', 'Iconic American muscle car', 'USA'),
            ('F-150', 2, 'Lariat', '2024', 'Best-selling pickup truck in America', 'USA'),
            ('3 Series', 3, '330i', '2024', 'Luxury sports sedan with precision handling', 'Germany'),
            ('X5', 3, 'xDrive40i', '2024', 'Premium mid-size luxury SUV', 'Global'),
            ('488 GTB', 4, 'Base', '2023', 'High-performance exotic sports car', 'Italy'),
            ('Model 3', 5, 'Long Range', '2024', 'Electric sedan with advanced autopilot', 'USA'),
            ('Model Y', 5, 'Performance', '2024', 'Electric SUV with impressive range', 'USA'),
            ('S-Class', 6, 'S500', '2024', 'Flagship luxury sedan with cutting-edge technology', 'Germany'),
            ('Civic', 7, 'Sport', '2024', 'Sporty compact car with great handling', 'Global'),
            ('Accord', 7, 'Touring', '2024', 'Mid-size sedan with spacious interior', 'USA'),
            ('911', 8, 'Carrera', '2024', 'Legendary sports car with timeless design', 'Germany')
        ]
        cursor.executemany('INSERT INTO cars (name, brand_id, model, production_date, description, produced_for_country) VALUES (?, ?, ?, ?, ?, ?)', cars_data)
        
        car_features_data = [
            (1, 2), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (2, 2), (2, 8), (2, 9), (2, 10),
            (3, 4), (3, 7), (3, 8), (3, 9),
            (4, 4), (4, 3), (4, 8), (4, 10),
            (5, 4), (5, 3), (5, 7), (5, 8), (5, 9),
            (6, 4), (6, 3), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10),
            (7, 4), (7, 7), (7, 8), (7, 9),
            (8, 1), (8, 5), (8, 8), (8, 9), (8, 10),
            (9, 1), (9, 5), (9, 3), (9, 6), (9, 8), (9, 9), (9, 10),
            (10, 3), (10, 6), (10, 7), (10, 8), (10, 9), (10, 10),
            (11, 4), (11, 8), (11, 9), (11, 10),
            (12, 2), (12, 6), (12, 7), (12, 8), (12, 9), (12, 10),
            (13, 4), (13, 3), (13, 7), (13, 8), (13, 9)
        ]
        cursor.executemany('INSERT INTO car_features (car_id, feature_id) VALUES (?, ?)', car_features_data)
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database on startup
init_db()

# AUTH ENDPOINTS
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not all([username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not all([username, password]):
        return jsonify({'error': 'Username and password required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        'SELECT user_id, username, email FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# BRANDS ENDPOINTS
@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get all brands"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM brands ORDER BY brand_name')
    brands = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(brands)

# FEATURES ENDPOINTS
@app.route('/api/features', methods=['GET'])
def get_features():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM features ORDER BY feature_name')
    features = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(features)

# CARS ENDPOINTS
@app.route('/api/cars', methods=['GET'])
def get_cars():
    """Get cars with optional filters"""
    brands_filter = request.args.get('brands', '')
    features_filter = request.args.get('features', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT DISTINCT c.*, b.brand_name,
               GROUP_CONCAT(f.feature_name, ',') as features
        FROM cars c
        JOIN brands b ON c.brand_id = b.brand_id
        LEFT JOIN car_features cf ON c.car_id = cf.car_id
        LEFT JOIN features f ON cf.feature_id = f.feature_id
    '''
    conditions = []
    params = []
    
    if brands_filter:
        brand_ids = brands_filter.split(',')
        placeholders = ','.join('?' * len(brand_ids))
        conditions.append(f'c.brand_id IN ({placeholders})')
        params.extend(brand_ids)
    
    if features_filter:
        feature_ids = features_filter.split(',')
        for feature_id in feature_ids:
            conditions.append(f'''
                c.car_id IN (
                    SELECT car_id FROM car_features WHERE feature_id = ?
                )
            ''')
            params.append(feature_id)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' GROUP BY c.car_id ORDER BY c.name'
    cursor.execute(query, params)
    cars = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(cars)

@app.route('/api/cars/<int:car_id>', methods=['GET'])
def get_car(car_id):
    """Get a specific car"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, b.brand_name,
               GROUP_CONCAT(f.feature_name, ',') as features
        FROM cars c
        JOIN brands b ON c.brand_id = b.brand_id
        LEFT JOIN car_features cf ON c.car_id = cf.car_id
        LEFT JOIN features f ON cf.feature_id = f.feature_id
        WHERE c.car_id = ?
        GROUP BY c.car_id
    ''', (car_id,))
    car = cursor.fetchone()
    conn.close()
    
    if car:
        return jsonify(dict(car))
    return jsonify({'error': 'Car not found'}), 404

# FAVORITES ENDPOINTS
@app.route('/api/favorites/<int:user_id>', methods=['GET'])
def get_favorites(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, b.brand_name,
               GROUP_CONCAT(f.feature_name, ',') as features
        FROM favorites fav
        JOIN cars c ON fav.car_id = c.car_id
        JOIN brands b ON c.brand_id = b.brand_id
        LEFT JOIN car_features cf ON c.car_id = cf.car_id
        LEFT JOIN features f ON cf.feature_id = f.feature_id
        WHERE fav.user_id = ?
        GROUP BY c.car_id
        ORDER BY c.name
    ''', (user_id,))
    favorites = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(favorites)

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    data = request.json
    user_id = data.get('user_id')
    car_id = data.get('car_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO favorites (user_id, car_id) VALUES (?, ?)',
            (user_id, car_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Favorite added'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Already favorited'}), 400

@app.route('/api/favorites', methods=['DELETE'])
def remove_favorite():
    data = request.json
    user_id = data.get('user_id')
    car_id = data.get('car_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM favorites WHERE user_id = ? AND car_id = ?',
        (user_id, car_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Favorite removed'}), 200

# NOTES ENDPOINTS
@app.route('/api/notes/user/<int:user_id>', methods=['GET'])
def get_user_notes(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.*, c.name as car_name
        FROM notes n
        JOIN cars c ON n.car_id = c.car_id
        WHERE n.user_id = ?
        ORDER BY n.updated_at DESC
    ''', (user_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(notes)

@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json
    user_id = data.get('user_id')
    car_id = data.get('car_id')
    note_text = data.get('note_text')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO notes (user_id, car_id, note_text) VALUES (?, ?, ?)',
        (user_id, car_id, note_text)
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'note_id': note_id}), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.json
    note_text = data.get('note_text')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE notes SET note_text = ?, updated_at = CURRENT_TIMESTAMP WHERE note_id = ?',
        (note_text, note_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Note updated'}), 200

@app.route('/api/notes/<int:note_id>', methods=['DELETE']) 
def delete_note(note_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE note_id = ?', (note_id,)) 
    conn.commit()
    conn.close()
    return jsonify({'message': 'Note deleted'}), 200 

# REVIEWS ENDPOINTS
@app.route('/api/reviews/user/<int:user_id>', methods=['GET'])
def get_user_reviews(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, c.name as car_name
        FROM reviews r
        JOIN cars c ON r.car_id = c.car_id
        WHERE r.user_id = ?
        ORDER BY r.updated_at DESC
    ''', (user_id,))
    reviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(reviews)

@app.route('/api/reviews/<int:user_id>/<int:car_id>', methods=['GET'])
def get_review(user_id, car_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, c.name as car_name
        FROM reviews r
        JOIN cars c ON r.car_id = c.car_id
        WHERE r.user_id = ? AND r.car_id = ?
    ''', (user_id, car_id))
    review = cursor.fetchone()
    conn.close()
    if review:
        return jsonify(dict(review))
    return jsonify({'error': 'Review not found'}), 404

@app.route('/api/reviews', methods=['POST'])
def create_or_update_review():
    data = request.json
    user_id = data.get('user_id')
    car_id = data.get('car_id')
    review_text = data.get('review_text')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT review_id FROM reviews WHERE user_id = ? AND car_id = ?',
        (user_id, car_id)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            'UPDATE reviews SET review_text = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND car_id = ?',
            (review_text, user_id, car_id)
        )
        message = 'Review updated'
    else:
        cursor.execute(
            'INSERT INTO reviews (user_id, car_id, review_text) VALUES (?, ?, ?)',
            (user_id, car_id, review_text)
        )
        message = 'Review created'
    
    conn.commit()
    conn.close()
    return jsonify({'message': message}), 201

@app.route('/api/reviews/<int:user_id>/<int:car_id>', methods=['DELETE'])
def delete_review(user_id, car_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reviews WHERE user_id = ? AND car_id = ?', (user_id, car_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Review deleted'}), 200

if __name__ == '__main__':
    print("Starting Carinator Backend...")
    print(f"Database located at: {DB_PATH}")
    print("Backend running on http://192.168.1.15:5000") #may vary here
    app.run(debug=True, host="0.0.0.0", port=5000)