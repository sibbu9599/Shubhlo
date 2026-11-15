#!/bin/bash
# ==============================================================================
# Shubhlo Platform - Hostinger VPS 1-Click Automated Setup Script
# A venture of Sangam InfoTech Pvt. Ltd.
# ==============================================================================
set -e

echo "=========================================================="
echo " Starting Shubhlo Hostinger VPS Setup..."
echo "=========================================================="

# 1. Update system packages
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx mysql-server

# 2. Setup project directory
PROJECT_DIR="/var/www/shubhlo"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Cloning repository into $PROJECT_DIR..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo git clone https://github.com/sibbu9599/Shubhlo.git "$PROJECT_DIR"
else
    echo "Updating repository in $PROJECT_DIR..."
    cd "$PROJECT_DIR"
    sudo git pull origin main
fi

cd "$PROJECT_DIR"

# 3. Setup Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup permissions
sudo chown -R www-data:www-data "$PROJECT_DIR"
sudo chmod -R 775 "$PROJECT_DIR/static"

# 5. Configure Systemd service
echo "Configuring Systemd service..."
sudo cp "$PROJECT_DIR/shubhlo.service" /etc/systemd/system/shubhlo.service
sudo systemctl daemon-reload
sudo systemctl enable shubhlo
sudo systemctl restart shubhlo

# 6. Configure Nginx
echo "Configuring Nginx reverse proxy..."
sudo cp "$PROJECT_DIR/nginx_shubhlo.conf" /etc/nginx/sites-available/shubhlo
sudo ln -sf /etc/nginx/sites-available/shubhlo /etc/nginx/sites-enabled/shubhlo
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=========================================================="
echo " Shubhlo Platform successfully installed on Hostinger VPS!"
echo " Next steps:"
echo " 1. Configure MySQL database using: mysql -u root < schema.sql"
echo " 2. Configure .env file with your database & secret keys."
echo " 3. Run SSL setup: sudo certbot --nginx -d shubhlo.in -d www.shubhlo.in"
echo "=========================================================="
