 Hotel Booking API

Hey! This is my test task for the Junior Backend Developer (Python) position. It's a simple API for booking hotel rooms, built with Django and DRF.

Tech Stack
*   Python 3.12
*   Django & DRF
*   PostgreSQL (but works with others too)

How to Run It

1.  Clone the repo:
    ```bash
    git clone <repository_url>
    cd BookingApp
    ```

2.  Install dependencies:
    I included a `requirements.txt` file, so just run:
    ```bash
    pip install -r requirements.txt
    ```

3.  Database Setup:
    I'm using `dj-database-url` to handle the database connection. You'll need to set the `DATABASE_URL` environment variable.
    
      Linux:
        ```bash
        export DATABASE_URL=postgresql://user:password@localhost:5432/booking_db
        ```
       Window:
        ```powershell
        $env:DATABASE_URL="postgresql://user:password@localhost:5432/booking_db"
        ```
    
    If you don't set this, it might try to look for a default config, so better set it up!

4.  Run Migrations:
    ```bash
    python manage.py migrate
    ```

5.  Create an Admin User:
    You'll need this to manage rooms and bookings from the admin panel.
    ```bash
    python manage.py createsuperuser
    ```

6.  Start the Server like usual django app
    ```bash
    python manage.py runserver
    ```    
That's it! The API should be up at `http://127.0.0.1:8000/`.

Documentation

I added Swagger/Redoc so you can easily test the endpoints:

Redoc: `http://127.0.0.1:8000/api/redoc/`
Schema: `http://127.0.0.1:8000/api/schema/`

Features Implemented

   Rooms: You can view all rooms and filter them by capacity or price.
   Booking: Registered users can book rooms. I added validation so you can't double-book a room or pick invalid dates.
   Search: Check which rooms are free for specific dates.
    Auth: Standard registration and JWT token authentication.

Let me know if you have any questions!
