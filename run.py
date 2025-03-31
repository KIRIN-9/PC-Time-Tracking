from app import app
import os

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    try:
        # Run the application
        app.run(
            host='127.0.0.1',  # Localhost
            port=5000,         # Default Flask port
            debug=True        # Enable debug mode
        )
    except Exception as e:
        print(f"Error starting the application: {str(e)}")