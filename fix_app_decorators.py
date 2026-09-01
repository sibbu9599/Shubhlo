import re, py_compile

route_mappings = {
    'home': ["@app.route('/')", "@app.route('/home')"],
    'login': ["@app.route('/login', methods=['GET', 'POST'])"],
    'signup': ["@app.route('/signup', methods=['GET', 'POST'])", "@app.route('/register', methods=['GET', 'POST'])"],
    'logout': ["@app.route('/logout')"],
    'services': ["@app.route('/services')"],
    'about': ["@app.route('/about')"],
    'terms': ["@app.route('/terms')"],
    'privacy': ["@app.route('/privacy')"],
    'contact': ["@app.route('/contact', methods=['GET', 'POST'])"],
    'forget_password': ["@app.route('/forget-password', methods=['GET', 'POST'])"],
    'verify_reset_otp': ["@app.route('/verify-reset-otp', methods=['POST'])"],
    'reset_password': ["@app.route('/reset-password', methods=['POST'])"],
    'get_allowed_locations': ["@app.route('/api/allowed-locations')"],
    'booking1': ["@app.route('/booking1', methods=['GET', 'POST'])"],
    'booking2': ["@app.route('/booking2', methods=['GET', 'POST'])"],
    'confirm_booking': ["@app.route('/confirm_booking', methods=['GET', 'POST'])"],
    'pay': ["@app.route('/pay', methods=['GET', 'POST'])"],
    'process_payment': ["@app.route('/process-payment', methods=['POST'])"],
    'booking_invoice': ["@app.route('/booking/invoice/<int:booking_id>')"],
    'cancel_booking': ["@app.route('/booking/cancel/<int:booking_id>', methods=['POST'])"],
    'rating': ["@app.route('/rating', methods=['GET', 'POST'])"],
    'dashboard': ["@app.route('/dashboard')"],
    'quick_inquiry': ["@app.route('/quick_inquiry', methods=['POST'])"],
    'user_respond_counter_offer': ["@app.route('/customer/accept_counter_offer/<int:booking_id>')"],
    'vendor_login': ["@app.route('/vendor/login', methods=['GET', 'POST'])"],
    'vendor_register': ["@app.route('/vendor_register', methods=['GET', 'POST'])"],
    'vendor_register_new': ["@app.route('/vendor/register', methods=['GET', 'POST'])", "@app.route('/vendor_register', methods=['GET', 'POST'])"],
    'vendor_dashboard': ["@app.route('/vendor/dashboard')"],
    'vendor_verify_otp': ["@app.route('/vendor/verify_otp', methods=['POST'])"],
    'vendor_update': ["@app.route('/vendor/update', methods=['POST'])"],
    'vendor_update_pricing': ["@app.route('/vendor/update_pricing', methods=['POST'])"],
    'vendor_switch_service': ["@app.route('/vendor/switch_service', methods=['POST'])"],
    'vendor_add_service': ["@app.route('/vendor/add_service', methods=['POST'])"],
    'vendor_toggle_date_availability': ["@app.route('/vendor/toggle_date_availability', methods=['POST'])"],
    'vendor_counter_offer': ["@app.route('/vendor/counter_offer/<int:booking_id>', methods=['POST'])"],
    'vendor_logout': ["@app.route('/vendor/logout')"],
    'admin_dashboard': ["@app.route('/admin/dashboard')"],
    'admin_approve_booking': ["@app.route('/admin/approve_booking/<int:booking_id>', methods=['GET', 'POST'])"],
    'admin_reject_booking': ["@app.route('/admin/reject_booking/<int:booking_id>', methods=['POST'])"],
    'admin_delete_booking': ["@app.route('/admin/booking/delete/<int:booking_id>', methods=['POST'])"],
    'admin_approve_vendor': ["@app.route('/admin/vendor/approve/<int:vendor_id>', methods=['POST'])"],
    'admin_reject_vendor': ["@app.route('/admin/vendor/reject/<int:vendor_id>', methods=['POST'])"],
    'admin_delete_vendor': ["@app.route('/admin/vendor/delete/<int:vendor_id>', methods=['POST'])"],
    'admin_edit_vendor': ["@app.route('/admin/vendor/edit/<int:vendor_id>', methods=['POST'])"],
    'admin_add_allowed_location': ["@app.route('/admin/allowed-locations/add', methods=['POST'])"],
    'admin_delete_allowed_location': ["@app.route('/admin/allowed-locations/delete/<int:loc_id>', methods=['POST'])"],
    'admin_delete_message': ["@app.route('/admin/message/delete/<int:msg_id>', methods=['POST'])"],
    'admin_delete_sms': ["@app.route('/admin/sms/delete/<int:sms_id>', methods=['POST'])"],
    'admin_clear_all_sms': ["@app.route('/admin/sms/clear-all', methods=['POST'])"],
    'admin_blacklist_add': ["@app.route('/admin/blacklist/add', methods=['POST'])"],
    'admin_blacklist_delete': ["@app.route('/admin/blacklist/delete/<int:blacklist_id>', methods=['POST'])"],
    'admin_update_system_settings': ["@app.route('/admin/update_system_settings', methods=['POST'])"],
    'admin_toggle_system_setting': ["@app.route('/admin/toggle_system_setting', methods=['POST'])"],
    'admin_toggle_master_control': ["@app.route('/admin/toggle_master_control', methods=['POST'])"],
    'admin_reassign_booking': ["@app.route('/admin/reassign_booking/<int:booking_id>', methods=['POST'])"],
    'reassign_booking': ["@app.route('/admin/reassign_booking/<int:booking_id>', methods=['POST'])"],
    'booking_verification': ["@app.route('/admin/booking_verification/<int:booking_id>', methods=['GET', 'POST'])"],
    'advertisement': ["@app.route('/advertisement')"],
    'ad_video': ["@app.route('/ad-video')"],
    'youtube': ["@app.route('/youtube')"],
    'youtube_hub': ["@app.route('/youtube')"],
    'promo_video': ["@app.route('/promo-video')"]
}

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.splitlines()
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    m = re.match(r'^(def\s+([a-zA-Z0-9_]+)\s*\(.*)$', line)
    if m:
        func_name = m.group(2)
        if func_name in route_mappings:
            # Check if previous lines already contain @app.route
            has_route = False
            for check_idx in range(len(new_lines)-1, max(-1, len(new_lines)-5), -1):
                if new_lines[check_idx].strip().startswith('@app.route'):
                    has_route = True
                    break
            if not has_route:
                for dec in route_mappings[func_name]:
                    new_lines.append(dec)
    new_lines.append(line)
    i += 1

updated_content = '\n'.join(new_lines)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Updated app.py with route decorators. Compiling...")
py_compile.compile('app.py', doraise=True)
print("SUCCESS: app.py compiled cleanly with all route decorators intact!")
