#!/bin/bash

# Token Tracker Setup Script

# Function to display usage
show_usage() {
    echo "Token Tracker Setup Script"
    echo "Usage: ./setup.sh [js|python|both]"
    echo "  js     - Setup JavaScript version"
    echo "  python - Setup Python version"
    echo "  both   - Setup both versions"
    exit 1
}

# Function to setup JavaScript environment
setup_js() {
    echo "Setting up JavaScript environment..."
    npm install
    echo "JavaScript setup complete!"
}

# Function to setup Python environment
setup_python() {
    echo "Setting up Python environment..."
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    echo "Python setup complete!"
    echo "To activate the virtual environment, run: source venv/bin/activate"
}

# Function to run the appropriate version
run_tracker() {
    case $1 in
        js)
            echo "Running JavaScript version..."
            node token_tracker.js
            ;;
        python)
            echo "Running Python version..."
            source venv/bin/activate
            python token_tracker.py
            ;;
        *)
            echo "Invalid version specified. Use 'js' or 'python'."
            exit 1
            ;;
    esac
}

# Check arguments
if [[ $# -ne 1 ]]; then
    show_usage
fi

# Process based on argument
case $1 in
    js)
        setup_js
        ;;
    python)
        setup_python
        ;;
    both)
        setup_js
        setup_python
        ;;
    run-js)
        run_tracker js
        ;;
    run-python)
        run_tracker python
        ;;
    *)
        show_usage
        ;;
esac

echo "Setup completed successfully!"
echo "You can now run the token tracker using:"
echo "  For JavaScript: node token_tracker.js"
echo "  For Python: source venv/bin/activate && python token_tracker.py"
echo "  Or use: ./setup.sh run-js or ./setup.sh run-python"
