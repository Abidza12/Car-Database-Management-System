import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carinator.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

def get_db_connection():
    # FK enabled here
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input("\nPress Enter to continue...")

def print_header(title):
    clear_screen()
    print("=" * 60)
    print(f"  CARINATOR ADMIN CONSOLE - {title}")
    print("=" * 60)
    print()

# BACKUP MANAGEMENT ==============

def create_backup():
    #Create a backup of the database
    print_header("CREATE BACKUP")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        pause()
        return
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"carinator_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup created successfully!")
        print(f"Location: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")
    
    pause()

def list_backups():
    #List all available backups
    print_header("AVAILABLE BACKUPS")
    
    if not os.path.exists(BACKUP_DIR):
        print("No backups directory found.")
        pause()
        return []
    
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
    
    if not backups:
        print("No backups found.")
        pause()
        return []
    
    backups.sort(reverse=True)
    
    for idx, backup in enumerate(backups, 1):
        backup_path = os.path.join(BACKUP_DIR, backup)
        size = os.path.getsize(backup_path) / 1024  # KB
        mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
        print(f"{idx}. {backup}")
        print(f"   Size: {size:.2f} KB | Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    return backups

def restore_backup():
    #Restore database from a backup
    backups = list_backups()
    
    if not backups:
        return
    
    choice = input("\nEnter backup number to restore (0 to cancel): ").strip()
    
    if choice == '0':
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(backups):
            backup_path = os.path.join(BACKUP_DIR, backups[idx])
            
            confirm = input(f"\n⚠️  This will replace the current database. Continue? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                shutil.copy2(backup_path, DB_PATH)
                print(f"Database restored from {backups[idx]}")
            else:
                print("Restore cancelled.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error restoring backup: {e}")
    
    pause()

# BRAND MANAGEMENT ==============

def list_brands():
    #List all brands
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM brands ORDER BY brand_name')
    brands = cursor.fetchall()
    conn.close()
    
    if not brands:
        print("No brands found.")
        return []
    
    for brand in brands:
        print(f"{brand['brand_id']}. {brand['brand_name']} ({brand['country_of_origin']}) - Founded: {brand['founded_date']}")
    
    return brands

def add_brand():
    #Add a new brand
    print_header("ADD BRAND")
    
    brand_name = input("Brand Name: ").strip()
    country = input("Country of Origin: ").strip()
    founded = input("Founded Date (YYYY or leave empty): ").strip()
    
    if not brand_name or not country:
        print("Brand name and country are required.")
        pause()
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO brands (brand_name, country_of_origin, founded_date) VALUES (?, ?, ?)',
            (brand_name, country, founded if founded else None)
        )
        conn.commit()
        conn.close()
        print(f"Brand '{brand_name}' added successfully!")
    except sqlite3.IntegrityError:
        print("Error: Brand might already exist.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def delete_brand():
    #Delete a brand
    print_header("DELETE BRAND")
    list_brands()
    
    brand_id = input("\nEnter Brand ID to delete (0 to cancel): ").strip()
    
    if brand_id == '0':
        return
    
    try:
        brand_id = int(brand_id)
        
        # Check if brand has cars
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM cars WHERE brand_id = ?', (brand_id,))
        car_count = cursor.fetchone()['count']
        
        if car_count > 0:
            print(f"\n⚠️  This brand has {car_count} car(s) associated with it.")
            print("⚠️  Deleting this brand will also delete all associated cars!")
        
        confirm = input("\n⚠️  Are you sure you want to delete this brand? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute('DELETE FROM brands WHERE brand_id = ?', (brand_id,))
            conn.commit()
            print("Brand deleted successfully!")
        else:
            print("Deletion cancelled.")
        
        conn.close()
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def manage_brands():
    #Brand management menu
    while True:
        print_header("BRAND MANAGEMENT")
        print("1. List All Brands")
        print("2. Add Brand")
        print("3. Delete Brand")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            print_header("ALL BRANDS")
            list_brands()
            pause()
        elif choice == '2':
            add_brand()
        elif choice == '3':
            delete_brand()
        elif choice == '0':
            break
        else:
            print("Invalid choice.")
            pause()

# CAR MANAGEMENT ==============

def list_cars():
    #List all cars
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, b.brand_name
        FROM cars c
        JOIN brands b ON c.brand_id = b.brand_id
        ORDER BY c.name
    ''')
    cars = cursor.fetchall()
    conn.close()
    
    if not cars:
        print("No cars found.")
        return []
    
    for car in cars:
        print(f"{car['car_id']}. {car['name']} ({car['brand_name']}) - Model: {car['model']}, Year: {car['production_date']}")
    
    return cars

def add_car():
    #Add a new car
    print_header("ADD CAR")
    
    # Show brands first
    print("Available Brands:")
    brands = list_brands()
    print()
    
    if not brands:
        print("No brands available. Please add a brand first.")
        pause()
        return
    
    name = input("Car Name: ").strip()
    brand_id = input("Brand ID: ").strip()
    model = input("Model: ").strip()
    year = input("Production Year: ").strip()
    description = input("Description: ").strip()
    country = input("Produced for Country: ").strip()
    
    if not all([name, brand_id, model]):
        print("Name, Brand ID, and Model are required.")
        pause()
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cars (name, brand_id, model, production_date, description, produced_for_country)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, int(brand_id), model, year, description, country))
        conn.commit()
        conn.close()
        print(f"Car '{name}' added successfully!")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def edit_car():
    #Edit car details (name, brand, description only)
    print_header("EDIT CAR")
    list_cars()
    
    car_id = input("\nEnter Car ID to edit (0 to cancel): ").strip()
    
    if car_id == '0':
        return
    
    try:
        car_id = int(car_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,))
        car = cursor.fetchone()
        
        if not car:
            print("Car not found.")
            conn.close()
            pause()
            return
        
        print(f"\nCurrent Details:")
        print(f"Name: {car['name']}")
        print(f"Brand ID: {car['brand_id']}")
        print(f"Description: {car['description']}")
        print()
        
        name = input(f"New Name (press Enter to keep '{car['name']}'): ").strip()
        brand_id = input(f"New Brand ID (press Enter to keep '{car['brand_id']}'): ").strip()
        description = input(f"New Description (press Enter to keep current): ").strip()
        
        # Use existing values if nothing entered
        name = name if name else car['name']
        brand_id = int(brand_id) if brand_id else car['brand_id']
        description = description if description else car['description']
        
        cursor.execute('''
            UPDATE cars 
            SET name = ?, brand_id = ?, description = ?
            WHERE car_id = ?
        ''', (name, brand_id, description, car_id))
        conn.commit()
        conn.close()
        
        print("Car updated successfully!")
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def delete_car():
    #Delete a car
    print_header("DELETE CAR")
    list_cars()
    
    car_id = input("\nEnter Car ID to delete (0 to cancel): ").strip()
    
    if car_id == '0':
        return
    
    try:
        car_id = int(car_id)
        confirm = input("\nAre you sure you want to delete this car? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cars WHERE car_id = ?', (car_id,))
            conn.commit()
            conn.close()
            print("Car deleted successfully!")
        else:
            print("Deletion cancelled.")
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def manage_cars():
    #Car management menu
    while True:
        print_header("CAR MANAGEMENT")
        print("1. List All Cars")
        print("2. Add Car")
        print("3. Edit Car")
        print("4. Delete Car")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            print_header("ALL CARS")
            list_cars()
            pause()
        elif choice == '2':
            add_car()
        elif choice == '3':
            edit_car()
        elif choice == '4':
            delete_car()
        elif choice == '0':
            break
        else:
            print("Invalid choice.")
            pause()

# FEATURE MANAGEMENT ==============

def list_features():
    #List all features
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM features ORDER BY feature_name')
    features = cursor.fetchall()
    conn.close()
    
    if not features:
        print("No features found.")
        return []
    
    for feature in features:
        print(f"{feature['feature_id']}. {feature['feature_name']} - {feature['description']}")
    
    return features

def add_feature():
    #Add a new feature
    print_header("ADD FEATURE")
    
    feature_name = input("Feature Name: ").strip()
    description = input("Description: ").strip()
    
    if not feature_name:
        print("Feature name is required.")
        pause()
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO features (feature_name, description) VALUES (?, ?)',
            (feature_name, description)
        )
        conn.commit()
        conn.close()
        print(f"Feature '{feature_name}' added successfully!")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def delete_feature():
    #Delete a feature
    print_header("DELETE FEATURE")
    list_features()
    
    feature_id = input("\nEnter Feature ID to delete (0 to cancel): ").strip()
    
    if feature_id == '0':
        return
    
    try:
        feature_id = int(feature_id)
        
        # Check how many cars have this feature
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM car_features WHERE feature_id = ?', (feature_id,))
        car_count = cursor.fetchone()['count']
        
        if car_count > 0:
            print(f"\n  This feature is assigned to {car_count} car(s).")
            print("  Deleting will remove it from all cars!")
        
        confirm = input("\n  Are you sure you want to delete this feature? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute('DELETE FROM features WHERE feature_id = ?', (feature_id,))
            conn.commit()
            print("Feature deleted successfully!")
        else:
            print(" Deletion cancelled.")
        
        conn.close()
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def assign_feature_to_car():
    #Assign a feature to a car
    print_header("ASSIGN FEATURE TO CAR")
    
    print("Available Cars:")
    cars = list_cars()
    print()
    
    if not cars:
        pause()
        return
    
    print("\nAvailable Features:")
    features = list_features()
    print()
    
    if not features:
        pause()
        return
    
    car_id = input("\nEnter Car ID: ").strip()
    feature_id = input("Enter Feature ID: ").strip()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO car_features (car_id, feature_id) VALUES (?, ?)',
            (int(car_id), int(feature_id))
        )
        conn.commit()
        conn.close()
        print("Feature assigned to car successfully!")
    except sqlite3.IntegrityError:
        print("This feature is already assigned to this car.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def remove_feature_from_car():
    #Remove a feature from a car
    print_header("REMOVE FEATURE FROM CAR")
    
    print("Available Cars:")
    cars = list_cars()
    print()
    
    if not cars:
        pause()
        return
    
    car_id = input("\nEnter Car ID: ").strip()
    
    try:
        car_id = int(car_id)
        
        # Show features for this car
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.feature_id, f.feature_name
            FROM car_features cf
            JOIN features f ON cf.feature_id = f.feature_id
            WHERE cf.car_id = ?
        ''', (car_id,))
        car_features = cursor.fetchall()
        
        if not car_features:
            print("This car has no features assigned.")
            conn.close()
            pause()
            return
        
        print("\nFeatures assigned to this car:")
        for feature in car_features:
            print(f"{feature['feature_id']}. {feature['feature_name']}")
        
        feature_id = input("\nEnter Feature ID to remove: ").strip()
        feature_id = int(feature_id)
        
        cursor.execute(
            'DELETE FROM car_features WHERE car_id = ? AND feature_id = ?',
            (car_id, feature_id)
        )
        conn.commit()
        conn.close()
        print("Feature removed from car successfully!")
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def manage_features():
    #Feature management menu
    while True:
        print_header("FEATURE MANAGEMENT")
        print("1. List All Features")
        print("2. Add Feature")
        print("3. Delete Feature")
        print("4. Assign Feature to Car")
        print("5. Remove Feature from Car")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            print_header("ALL FEATURES")
            list_features()
            pause()
        elif choice == '2':
            add_feature()
        elif choice == '3':
            delete_feature()
        elif choice == '4':
            assign_feature_to_car()
        elif choice == '5':
            remove_feature_from_car()
        elif choice == '0':
            break
        else:
            print("Invalid choice.")
            pause()

# USER MANAGEMENT ==============

def list_users():
    #List all users
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, email, created_at FROM users ORDER BY username')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        print("No users found.")
        return []
    
    for user in users:
        print(f"{user['user_id']}. {user['username']} ({user['email']}) - Joined: {user['created_at']}")
    
    return users

def delete_user():
    #Delete a user
    print_header("DELETE USER")
    list_users()
    
    user_id = input("\nEnter User ID to delete (0 to cancel): ").strip()
    
    if user_id == '0':
        return
    
    try:
        user_id = int(user_id)
        # Show user stats
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM favorites WHERE user_id = ?', (user_id,))
        fav_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM notes WHERE user_id = ?', (user_id,))
        note_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM reviews WHERE user_id = ?', (user_id,))
        review_count = cursor.fetchone()['count']
        
        print(f"\nUser Statistics:")
        print(f"   Favorites: {fav_count}")
        print(f"   Notes: {note_count}")
        print(f"   Reviews: {review_count}")
        print("⚠️  All user data will be deleted!")
        
        confirm = input("\nAre you sure you want to delete this user? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            print("User deleted successfully!")
        else:
            print("Deletion cancelled.")
        
        conn.close()
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def delete_user_review():
    #Delete a specific review by a user
    print_header("DELETE USER REVIEW")
    list_users()
    
    user_id = input("\nEnter User ID (0 to cancel): ").strip()
    
    if user_id == '0':
        return
    
    try:
        user_id = int(user_id)
        
        # Show user's reviews
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.review_id, r.car_id, c.name as car_name, r.review_text
            FROM reviews r
            JOIN cars c ON r.car_id = c.car_id
            WHERE r.user_id = ?
        ''', (user_id,))
        reviews = cursor.fetchall()
        
        if not reviews:
            print("This user has no reviews.")
            conn.close()
            pause()
            return
        
        print("\nUser's Reviews:")
        for review in reviews:
            print(f"\nReview ID: {review['review_id']}")
            print(f"Car: {review['car_name']}")
            print(f"Review: {review['review_text'][:100]}...")
        
        review_id = input("\nEnter Review ID to delete: ").strip()
        review_id = int(review_id)
        
        confirm = input("\n⚠️  Delete this review? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute('DELETE FROM reviews WHERE review_id = ?', (review_id,))
            conn.commit()
            print("Review deleted successfully!")
        else:
            print("Deletion cancelled.")
        
        conn.close()
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")
    
    pause()

def manage_users():
    #User management menu
    while True:
        print_header("USER MANAGEMENT")
        print("1. List All Users")
        print("2. Delete User")
        print("3. Delete User Review")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            print_header("ALL USERS")
            list_users()
            pause()
        elif choice == '2':
            delete_user()
        elif choice == '3':
            delete_user_review()
        elif choice == '0':
            break
        else:
            print("Invalid choice.")
            pause()

# MAIN MENU ==============

def main():
    #Main menu
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        print(f"Expected location: {DB_PATH}")
        input("\nPress Enter to exit...")
        return
    while True:
        print_header("MAIN MENU")
        print(f"Database: {DB_PATH}")
        print()
        print("1. Manage Brands")
        print("2. Manage Cars")
        print("3. Manage Features")
        print("4. Manage Users")
        print("5. Create Backup")
        print("6. Restore Backup")
        print("0. Exit")
        print()
        choice = input("Enter choice: ").strip()
        if choice == '1':
            manage_brands()
        elif choice == '2':
            manage_cars()
        elif choice == '3':
            manage_features()
        elif choice == '4':
            manage_users()
        elif choice == '5':
            create_backup()
        elif choice == '6':
            restore_backup()
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice.")
            pause()

if __name__ == '__main__':
    main()