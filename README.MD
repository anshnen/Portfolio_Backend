### Features

* **RESTful API:** A well-defined API for frontend integration.
* **Robust Data Model:** A detailed database schema to accurately represent financial concepts.
* **Service-Oriented Architecture:** Business logic is decoupled from the API layer for cleaner, more testable code.
* **Database Migrations:** Uses Flask-Migrate to manage database schema changes.
* **Environment-based Configuration:** Securely manages configuration for development, testing, and production.
* **Interactive API Docs:** Integrated Swagger UI for easy API exploration and testing.

## Setup and Installation

Follow these steps to get the application running locally.

### 1. Prerequisites

* Python (3.8+ recommended)
* MySQL Server
* Git

### 2. Initial Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd portfolio-api
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Database Configuration

1.  **Create the MySQL Database:**
    Connect to your MySQL server and run:
    ```sql
    CREATE DATABASE portfolio_db;
    ```

2.  **Configure Environment Variables:**
    Create a file named `.env` in the project root directory. Copy the contents of `.env.example` (if available) or use the template below. **Update it with your actual MySQL credentials.**

    ```
    # .env
    FLASK_CONFIG=development
    SECRET_KEY="a-very-secret-and-hard-to-guess-string"

    DB_USER="your_mysql_username"
    DB_PASSWORD="your_mysql_password"
    DB_HOST="localhost"
    DB_NAME="portfolio_db"
    ```

### 4. Database Initialization

1.  **Initialize Flask-Migrate** (only needs to be run once for the project):
    ```bash
    flask db init
    ```

2.  **Generate the initial migration script:**
    ```bash
    flask db migrate -m "Initial migration."
    ```

3.  **Apply the migration to the database** (this creates the tables):
    ```bash
    flask db upgrade
    ```

## Running the Application

1.  **Seed the database with sample data:**
    ```bash
    python seed.py
    ```

2.  **Fetch initial market prices for the seeded assets:**
    ```bash
    python update_prices.py
    ```

3.  **Start the development server:**
    ```bash
    python run.py
    ```
    The API will now be running at `http://127.0.0.1:5000`.

## Testing Basic Functionality

You can test the API endpoints using a tool like Postman, Insomnia, or `curl` from your terminal.

### View API Documentation

* Open your browser and navigate to `http://127.0.0.1:5000/api/docs`. This will open the Swagger UI where you can see all available endpoints and test them interactively.

### Test with `curl`

1.  **Get Portfolio Summary:**
    Open a new terminal and run the following command to fetch the summary for portfolio with ID `1`.
    ```
http://127.0.0.1:5000/api/v1/portfolio/1/summary
    ```
    You should see a detailed JSON response with net worth, cash flow, accounts, etc.

2.  **Get All Accounts:**
    Run the following command to get a list of all accounts created by the seed script.
    ```http://127.0.0.1:5000/api/v1/portfolio/accounts
    ```
    You should see a JSON array of account objects.

