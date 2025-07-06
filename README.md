# Invoice Management System

A comprehensive invoice management system built with Django and Bootstrap 5, inspired by fakturuj.si.

## Features

- **Dashboard**: Overview of key metrics and recent activities
- **Invoices**: Create, view, edit, and manage invoices
- **Clients**: Manage client information and history
- **Products/Services**: Maintain a catalog of products and services
- **Reports**: Generate various financial reports
- **User Authentication**: Secure login and user management
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project1
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open your browser and go to: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Project Structure

```
project1/
├── core/                   # Core app (homepage, dashboard)
├── invoices/               # Invoices app
├── clients/                # Clients management
├── products/               # Products/Services catalog
├── reports/                # Reporting functionality
├── settings_app/           # User settings
├── project1/               # Project settings
├── static/                 # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/              # Base templates
├── manage.py
└── README.md
```

## Configuration

1. Copy `.env.example` to `.env` and update the settings:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

2. For production, set `DEBUG=False` and configure:
   - Database settings
   - Email settings
   - Static files serving
   - Security settings

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Django](https://www.djangoproject.com/)
- [Bootstrap 5](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [fakturuj.si](https://www.fakturuj.si/) for inspiration
