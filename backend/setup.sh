#!/bin/bash
# LabelGen Initial Setup Script

echo "🏷️  LabelGen Setup Script"
echo "=========================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "✓ Installing Django and dependencies..."
    pip install -r requirements.txt
else
    echo "✓ Django is already installed"
fi

# Run migrations
echo "✓ Running database migrations..."
python manage.py migrate

# Check if superuser exists
echo ""
echo "=========================="
echo "Setup complete! ✅"
echo ""
echo "Next steps:"
echo "1. Create a superuser (if not already created):"
echo "   python manage.py createsuperuser"
echo ""
echo "2. Create initial Config record via Django admin"
echo ""
echo "3. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "4. Open http://127.0.0.1:8000/ in your browser"
echo ""
