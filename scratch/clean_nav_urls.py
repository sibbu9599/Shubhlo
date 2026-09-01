import re

def clean_template(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Replace url_for('login') -> /login
    content = content.replace("{{ url_for('login') }}", "/login")
    content = content.replace("{{ url_for('signup') }}", "/signup")
    content = content.replace("{{ url_for('home') }}", "/home")
    content = content.replace("{{ url_for('services') }}", "/services")
    content = content.replace("{{ url_for('booking1') }}", "/booking1")
    content = content.replace("{{ url_for('booking') }}", "/booking")
    content = content.replace("{{ url_for('about') }}", "/about")
    content = content.replace("{{ url_for('contact') }}", "/contact")
    content = content.replace("{{ url_for('terms') }}", "/terms")
    content = content.replace("{{ url_for('privacy') }}", "/privacy")
    content = content.replace("{{ url_for('vendor_login') }}", "/vendor_login")
    content = content.replace("{{ url_for('vendor_register') }}", "/vendor_register")
    content = content.replace("{{ url_for('vendor_dashboard') }}", "/vendor_dashboard")
    content = content.replace("{{ url_for('admin_dashboard') }}", "/admin/dashboard")
    content = content.replace("{{ url_for('dashboard') }}", "/dashboard")
    content = content.replace("{{ url_for('logout') }}", "/logout")
    content = content.replace("{{ url_for('advertisement') }}", "/advertisement")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

clean_template("templates/home.html")
clean_template("templates/services.html")
print("Templates home.html and services.html cleaned successfully!")
