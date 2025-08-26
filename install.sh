#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Helper Functions ---
print_header() {
    echo "================================================================="
    echo "$1"
    echo "================================================================="
}

# --- Installation Functions ---

get_user_input() {
    print_header "Gathering Configuration Details"

    read -p "Enter the desired installation directory [/var/www/aitoolkit]: " APP_DIR
    APP_DIR=${APP_DIR:-/var/www/aitoolkit}

    read -p "Enter your server's domain name or IP address: " SERVER_NAME
    while [ -z "$SERVER_NAME" ]; do
        echo "Server name/IP cannot be empty." >&2
        read -p "Enter your server's domain name or IP address: " SERVER_NAME
    done

    echo "---"
    echo "Configuration:"
    echo "Installation Directory: $APP_DIR"
    echo "Server Name/IP: $SERVER_NAME"
    echo "Database: SQLite (default)"
    echo "---"
    read -p "Is this correct? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
}

install_system_deps() {
    print_header "Installing System Dependencies"
    apt-get update
    # Install base dependencies and curl
    apt-get install -y python3-pip python3-venv apache2 libapache2-mod-wsgi-py3 curl

    # Use NodeSource repository for a stable version of Node.js and npm
    echo "Setting up NodeSource repository for Node.js..."
    # The -fsSL flags make curl silent on success and fail on error
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -

    echo "Installing Node.js (which includes npm)..."
    apt-get install -y nodejs

    echo "System dependencies installed."
}

setup_application() {
    print_header "Setting Up Application Files"

    echo "Creating installation directory at $APP_DIR..."
    mkdir -p $APP_DIR

    echo "Copying application files..."
    rsync -av --progress . $APP_DIR --exclude ".git"

    echo "Setting up Python virtual environment..."
    python3 -m venv $APP_DIR/backend/venv

    echo "Installing Python dependencies..."
    $APP_DIR/backend/venv/bin/pip install -r $APP_DIR/backend/requirements.txt

    echo "Installing frontend dependencies..."
    (cd $APP_DIR/frontend && npm install)

    echo "Building React application..."
    (cd $APP_DIR/frontend && npm run build)

    echo "Creating project .env file in the root directory..."
    # The DATABASE_URL is now omitted, so the app will use its default SQLite config.
    cat <<EOF > $APP_DIR/.env
FLASK_APP=backend.wsgi
# For production, you should set a strong, random JWT_SECRET_KEY here
# JWT_SECRET_KEY=your_super_secret_key
EOF
    echo "Application setup complete."
}

configure_apache() {
    print_header "Configuring Apache2"
    TEMPLATE_CONF="apache.conf"
    APACHE_CONF_PATH="/etc/apache2/sites-available/aitoolkit.conf"
    echo "Creating Apache configuration file at $APACHE_CONF_PATH..."
    sed -e "s|your_server_domain_or_ip|$SERVER_NAME|g" \
        -e "s|/path/to/your/project|$APP_DIR|g" \
        "$TEMPLATE_CONF" > "$APACHE_CONF_PATH"
    echo "Apache configuration file created."
}

finalize_setup() {
    print_header "Finalizing Setup"

    echo "Ensuring clean state for database setup..."
    rm -f $APP_DIR/backend/app.db
    if [ -d "$APP_DIR/migrations" ]; then
        echo "Removing existing migrations directory..."
        rm -rf $APP_DIR/migrations
    fi

    echo "Initializing database schema..."
    (
        export FLASK_APP=backend.wsgi
        cd $APP_DIR/backend &&

        echo "Initializing database migrations repository..." &&
        venv/bin/flask db init --directory $APP_DIR/migrations &&

        echo "Generating initial database migration..." &&
        venv/bin/flask db migrate -m "Initial database schema" --directory $APP_DIR/migrations &&

        echo "Applying database migration..." &&
        venv/bin/flask db upgrade --directory $APP_DIR/migrations
    )
    echo "Enabling Apache site and modules..."
    a2ensite aitoolkit.conf
    a2enmod rewrite
    a2enmod wsgi
    echo "Restarting Apache2 service..."
    systemctl restart apache2
    echo "Setup finalized."
}

set_final_permissions() {
    print_header "Setting Final Ownership and Permissions"
    chown -R www-data:www-data $APP_DIR
    echo "Setting directory permissions to 755 and file permissions to 644..."
    find $APP_DIR -type d -exec chmod 755 {} \;
    find $APP_DIR -type f -exec chmod 644 {} \;
    echo "Setting execute permissions for venv and install scripts..."
    chmod +x $APP_DIR/backend/venv/bin/*
    chmod +x $APP_DIR/install.sh
    echo "Permissions set."
}

# --- Main Execution ---
main() {
    print_header "AI Toolkit Interactive Installer"
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use 'sudo ./install.sh'" >&2
        exit 1
    fi

    get_user_input
    install_system_deps
    setup_application
    set_final_permissions
    finalize_setup
    configure_apache

    print_header "Installation Complete!"
    echo "You should now be able to access the application at your specified domain/IP."
}

# Run the main function
main
