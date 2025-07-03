from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def seed_users():
    """Seeds the database with initial users."""
    app = create_app()
    with app.app_context():
        # Check if users already exist to prevent duplicates if run multiple times
        if User.query.first():
            print("Users already seeded.")
            return

        users_data = [
            {"username": "prof_smith", "password": "password123", "email": "prof.smith@example.com", "role": "professor"},
            {"username": "alice_wonder", "password": "password123", "email": "alice.wonder@example.com", "role": "student"},
            {"username": "bob_builder", "password": "password123", "email": "bob.builder@example.com", "role": "student"},
            {"username": "employer_x", "password": "password123", "email": "hr@employcorp.com", "role": "employer"},
            {"username": "admin_user", "password": "password123", "email": "admin@example.com", "role": "admin"}
        ]

        for user_data in users_data:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"]
            )
            user.set_password(user_data["password"]) # Use the method from the User model
            db.session.add(user)
            print(f"Adding user: {user_data['username']}")

        try:
            db.session.commit()
            print("Users seeded successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding users: {e}")

if __name__ == "__main__":
    seed_users()
