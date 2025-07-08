# Trading System API

This repository contains the source code for a robust, production-ready Trading System API built with FastAPI. It has been refactored for stability, scalability, and easy deployment on platforms like DigitalOcean.

## Project Structure

```
.
├── Procfile              # Tells the platform how to run the app
├── config/
│   └── production.env    # Environment variables (use for reference)
├── main.py               # Main FastAPI application entry point
├── requirements.txt      # Python dependencies
└── src/
    └── api/
        ├── auth.py       # Authentication routes (/api/auth)
        ├── market.py     # Market data routes (/api/market)
        └── users.py      # User management routes (/api/v1/users)
```

## Deployment to DigitalOcean App Platform

Follow these instructions to deploy the application to a new App Platform service. This will ensure a clean environment.

**Step 1: Create a New App**

- In your DigitalOcean dashboard, go to `Apps` -> `Create App`.
- Connect your GitHub repository.
- Select the branch to deploy from (e.g., `main`).
- DigitalOcean will autodetect the Python application. Click **Next**.

**Step 2: Configure the App**

- **Edit Plan:** Choose the plan that fits your needs (e.g., Basic or Pro).
- **Resources:** You should see a single web service resource. Click on it to edit its settings.
    - **Run Command:** Ensure the run command is set to `gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`. DigitalOcean should detect this from the `Procfile`, but it's good to verify.
    - **HTTP Port:** Should be `8000`.
- **Environment Variables:**
    - Click `Edit` next to "Environment Variables".
    - Click `Bulk Edit` and paste the contents of your `config/production.env` file. **Important:** Ensure you have real values for secrets like `SECRET_KEY` and `DATABASE_URL`.
    - Make sure `CORS_ORIGINS` is set correctly for your frontend (e.g., `["http://localhost:3000", "https://your-frontend-domain.com"]`).
    - Click **Save**.

**Step 3: Launch**

- Click **Next** to review your configuration.
- Click **Launch App**.

DigitalOcean will now build and deploy your application. You can monitor the deployment logs in the "Deployments" tab. Once complete, your API will be live at the URL provided by DigitalOcean.

## Local Development

To run the application locally:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Environment Variables:**
    - Create a copy of `config/production.env` and name it `config/development.env`.
    - Fill in the values for your local development environment.

3.  **Run the App:**
    The `main.py` file is configured to load from `config/production.env`. You can temporarily change line 20 in `main.py` to `load_dotenv('config/development.env')` for local testing.
    ```bash
    python main.py
    ```
    The server will be running at `http://localhost:8000`.