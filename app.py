from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import cv2
import numpy as np
import os
import json
import datetime
import pickle
import time
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "attendance_system_secret_key"

# Admin credentials
ADMIN_USERNAME = "admin_star"
ADMIN_PASSWORD = "locked_star"

# Class schedule
schedule = {
    'Monday': {
        '09-10': {'class': 'C:PES319', 'room': 'R: 37-806', 'section': 'S:K22HU'},
        '10-11': {'class': 'C:CSE332', 'room': 'R: 37-806', 'section': 'S:K22HU'},
        '11-12': {'class': 'C:PSY292', 'room': 'R: 36-705', 'section': 'S:KO084'},
        '02-03': {'class': 'C:PEAS02', 'room': 'R: 36-801', 'section': 'S:9R11K'}
    },
    'Tuesday': {
        '10-11': {'class': 'C:PES319', 'room': 'R: 38-818', 'section': 'S:K22HU'},
        '11-12': {'class': 'C:PES319', 'room': 'R: 38-818', 'section': 'S:K22HU'},
        '02-03': {'class': 'C:INT345', 'room': 'R: 26-307', 'section': 'S:K22HU'},
        '03-04': {'class': 'C:INT345', 'room': 'R: 26-307', 'section': 'S:K22HU'},
        '01-02': {'class': 'C:PSY292', 'room': 'R: 36-705', 'section': 'S:KO084'},
        '04-05': {'class': 'C:PEAS02', 'room': 'R: 36-801', 'section': 'S:9R11K'}
    },
    'Wednesday': {
        '10-11': {'class': 'C:CSE358', 'room': 'R: 38-816', 'section': 'S:K22HU'},
        '11-12': {'class': 'C:CSE358', 'room': 'R: 38-816', 'section': 'S:K22HU'},
        '01-02': {'class': 'C:PSY292', 'room': 'R: 36-705', 'section': 'S:KO084'},
        '03-04': {'class': 'C:PEAS02', 'room': 'R: 36-801', 'section': 'S:9R11K'}
    },
    'Thursday': {
        '01-02': {'class': 'C:PSY292', 'room': 'R: 36-705', 'section': 'S:KO084'},
        '02-03': {'class': 'C:CSE358', 'room': 'R: 25-304', 'section': 'S:K22HU'},
        '03-04': {'class': 'C:CSE358', 'room': 'R: 25-304', 'section': 'S:K22HU'},
        '04-05': {'class': 'C:CSE332', 'room': 'R: 25-304', 'section': 'S:K22HU'},
        '09-10': {'class': 'C:PEAS02', 'room': 'R: 36-801', 'section': 'S:9R11K'}
    },
    'Friday': {
        '10-11': {'class': 'C:INT345', 'room': 'R: 38-817', 'section': 'S:K22HU'},
        '11-12': {'class': 'C:INT345', 'room': 'R: 38-817', 'section': 'S:K22HU'},
        '01-02': {'class': 'C:PSY292', 'room': 'R: 36-705', 'section': 'S:KO084'},
        '02-03': {'class': 'C:CSE358', 'room': 'R: 38-815', 'section': 'S:K22HU'},
        '03-04': {'class': 'C:CSE358', 'room': 'R: 38-815', 'section': 'S:K22HU'},
        '04-05': {'class': 'C:PEAS02', 'room': 'R: 36-801', 'section': 'S:9R11K'}
    }
}

# Database functions
def load_users():
    try:
        with open('database/users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open('database/users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_attendance():
    try:
        with open('database/attendance_records.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_attendance(attendance):
    with open('database/attendance_records.json', 'w') as f:
        json.dump(attendance, f, indent=4)

# Helper functions
def get_current_day_time():
    now = datetime.datetime.now()
    day = now.strftime('%A')
    
    hour = now.hour
    if 9 <= hour < 10:
        time_slot = '09-10'
    elif 10 <= hour < 11:
        time_slot = '10-11'
    elif 11 <= hour < 12:
        time_slot = '11-12'
    elif 12 <= hour < 13:
        time_slot = '12-01'
    elif 13 <= hour < 14:
        time_slot = '01-02'
    elif 14 <= hour < 15:
        time_slot = '02-03'
    elif 15 <= hour < 16:
        time_slot = '03-04'
    elif 16 <= hour < 17:
        time_slot = '04-05'
    else:
        time_slot = None
    
    return day, time_slot

def get_current_class():
    day, time_slot = get_current_day_time()
    if day in schedule and time_slot in schedule[day]:
        return schedule[day][time_slot]
    return None

def get_classes_for_section(section):
    section_code = f"S:{section}"
    classes = []
    
    day, current_time_slot = get_current_day_time()
    
    if day in schedule:
        for time_slot, class_info in schedule[day].items():
            if class_info['section'] == section_code:
                class_id = f"{day}_{time_slot}_{class_info['class']}"
                
                # Format class name and room
                class_name = class_info['class'].replace('C:', '')
                room = class_info['room'].replace('R:', '')
                
                # Check if this is the current class
                is_current = (time_slot == current_time_slot)
                
                classes.append({
                    'id': class_id,
                    'name': class_name,
                    'room': room,
                    'time': time_slot,
                    'section': section,
                    'current': is_current
                })
    
    return classes

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('sections'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/sections')
def sections():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get current day and time
    current_day = datetime.datetime.now().strftime('%A')
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    
    # Get current class if any
    current_class = get_current_class()
    
    # Count students in each section
    users = load_users()
    k22hu_count = sum(1 for user in users.values() if user.get('section') == 'K22HU')
    ko084_count = sum(1 for user in users.values() if user.get('section') == 'KO084')
    r11k_count = sum(1 for user in users.values() if user.get('section') == '9R11K')
    
    return render_template('section.html', 
                          current_day=current_day,
                          current_time=current_time,
                          current_class=current_class,
                          k22hu_count=k22hu_count,
                          ko084_count=ko084_count,
                          r11k_count=r11k_count)

@app.route('/select_section/<section>')
def select_section(section):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Store the selected section in the session
    session['selected_section'] = section
    
    # Get classes for this section
    classes = get_classes_for_section(section)
    
    # Get current day and time
    current_day = datetime.datetime.now().strftime('%A')
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    
    return render_template('class_selection.html', 
                          section=section, 
                          classes=classes,
                          current_day=current_day,
                          current_time=current_time)

@app.route('/mark_attendance/<class_id>')
def mark_attendance(class_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Parse class_id to get day, time_slot, and class_name
    day, time_slot, class_name = class_id.split('_', 2)
    
    # Get the section from session
    section = session.get('selected_section')
    if not section:
        return redirect(url_for('sections'))
    
    # Get current time
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    
    # Create class info object
    class_info = {
        'class': class_name,
        'section': section,
        'room': schedule[day][time_slot]['room'].replace('R:', ''),
        'time': time_slot,
        'date': datetime.datetime.now().strftime('%Y-%m-%d')
    }
    
    return render_template('capture_face.html', 
                          section=section,
                          current_class=class_info,
                          current_time=current_time,
                          admin_username=ADMIN_USERNAME,
                          admin_password=ADMIN_PASSWORD)

@app.route('/process_attendance', methods=['POST'])
def process_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get data from request
    data = request.get_json()
    student_id = data.get('student_id')
    section = data.get('section')
    
    if not student_id or not section:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
    
    # Record attendance
    attendance = load_attendance()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    current_class = get_current_class()
    
    if not current_class:
        return jsonify({'success': False, 'message': 'No class in session'}), 400
    
    if today not in attendance:
        attendance[today] = {}
    
    class_key = f"{current_class['class']}_{current_class['section']}"
    if class_key not in attendance[today]:
        attendance[today][class_key] = {'automatic': [], 'manual': []}
    
    if student_id not in attendance[today][class_key]['automatic']:
        attendance[today][class_key]['automatic'].append(student_id)
        save_attendance(attendance)
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    else:
        return jsonify({'success': False, 'message': 'Attendance already marked'})

@app.route('/process_manual_attendance', methods=['POST'])
def process_manual_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get data from request
    data = request.get_json()
    student_id = data.get('student_id')
    section = data.get('section')
    reason = data.get('reason', 'Not specified')
    admin_password = data.get('admin_password')
    
    if not student_id or not section:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
    
    # Verify admin password for manual entries after the first one
    if data.get('requires_auth', False) and admin_password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': 'Invalid admin password'}), 403
    
    # Record attendance
    attendance = load_attendance()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    current_class = get_current_class()
    
    if not current_class:
        return jsonify({'success': False, 'message': 'No class in session'}), 400
    
    if today not in attendance:
        attendance[today] = {}
    
    class_key = f"{current_class['class']}_{current_class['section']}"
    if class_key not in attendance[today]:
        attendance[today][class_key] = {'automatic': [], 'manual': []}
    
    # For manual entries, we store additional information
    if 'manual_entries' not in attendance[today][class_key]:
        attendance[today][class_key]['manual_entries'] = []
    
    # Check if already marked
    existing_entry = next((entry for entry in attendance[today][class_key]['manual_entries'] 
                          if entry['student_id'] == student_id), None)
    
    if not existing_entry:
        # Add manual entry with reason
        attendance[today][class_key]['manual_entries'].append({
            'student_id': student_id,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
            'reason': reason
        })
        save_attendance(attendance)
        return jsonify({'success': True, 'message': 'Manual attendance marked successfully'})
    else:
        return jsonify({'success': False, 'message': 'Attendance already marked manually'})

@app.route('/view_attendance')
def view_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    attendance = load_attendance()
    users = load_users()
    
    # Get current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Sample data for the template
    # In a real app, you would process the attendance data to create these records
    daily_records = []
    students = []
    classes = []
    
    # Process attendance data to create records
    if current_date in attendance:
        for class_key, class_attendance in attendance[current_date].items():
            class_name, section_code = class_key.split('_')
            section = section_code.replace('S:', '')
            
            # Process automatic attendance
            for student_id in class_attendance.get('automatic', []):
                if student_id in users:
                    daily_records.append({
                        'id': student_id,
                        'name': users[student_id]['name'],
                        'class': class_name.replace('C:', ''),
                        'time': datetime.datetime.now().strftime('%I:%M %p'),
                        'status': 'present',
                        'section': section,
                        'method': 'face'
                    })
            
            # Process manual attendance
            for entry in class_attendance.get('manual_entries', []):
                student_id = entry['student_id']
                if student_id in users:
                    daily_records.append({
                        'id': student_id,
                        'name': users[student_id]['name'],
                        'class': class_name.replace('C:', ''),
                        'time': entry['timestamp'],
                        'status': 'manual',
                        'section': section,
                        'method': 'manual'
                    })
    
    # Create sample student attendance data
    for user_id, user_info in users.items():
        # Count attendance for this student
        present_count = sum(1 for record in daily_records if record['id'] == user_id and record['status'] in ['present', 'manual'])
        total_classes = 5  # Sample value
        absent_count = total_classes - present_count
        percentage = round((present_count / total_classes * 100) if total_classes > 0 else 0)
        
        students.append({
            'id': user_id,
            'name': user_info['name'],
            'section': user_info['section'],
            'total_classes': total_classes,
            'present': present_count,
            'absent': absent_count,
            'percentage': percentage
        })
    
    # Create sample class attendance data
    for day, day_schedule in schedule.items():
        for time_slot, class_info in day_schedule.items():
            class_name = class_info['class'].replace('C:', '')
            section = class_info['section'].replace('S:', '')
            
            # Count students in this section
            section_students = sum(1 for user in users.values() if user.get('section') == section)
            
            # Count present students (sample data)
            present_students = round(section_students * 0.85)  # 85% attendance rate
            absent_students = section_students - present_students
            percentage = round((present_students / section_students * 100) if section_students > 0 else 0)
            
            classes.append({
                'name': class_name,
                'section': section,
                'date': current_date,
                'time': time_slot,
                'total_students': section_students,
                'present': present_students,
                'absent': absent_students,
                'percentage': percentage
            })
    
    # Summary statistics
    total_students = len(users)
    avg_attendance = round(sum(student['percentage'] for student in students) / len(students) if students else 0)
    low_attendance = sum(1 for student in students if student['percentage'] < 75)
    classes_conducted = len(classes)
    
    # Students with low attendance
    low_attendance_students = [student for student in students if student['percentage'] < 75]
    
    return render_template('view_attendance.html', 
                          daily_records=daily_records,
                          students=students,
                          classes=classes,
                          current_date=current_date,
                          total_students=total_students,
                          avg_attendance=avg_attendance,
                          low_attendance=low_attendance,
                          classes_conducted=classes_conducted,
                          low_attendance_students=low_attendance_students)

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        registration_number = request.form.get('registration_number')
        name = request.form.get('name')
        section = request.form.get('section')
        phone = request.form.get('phone')
        admin_password = request.form.get('admin_password')
        
        # Validate admin password
        if admin_password != ADMIN_PASSWORD:
            flash('Invalid admin password', 'danger')
            return redirect(url_for('register_student'))
        
        # Check if registration number already exists
        users = load_users()
        if registration_number in users:
            flash('Registration number already exists', 'danger')
            return redirect(url_for('register_student'))
        
                # Handle photo uploads
        photos = []
        photo_dir = os.path.join('DATASETS', 'registered_users', registration_number)
        
        # Create directory if it doesn't exist
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)
        
        # Save each photo
        for i in range(1, 5):
            photo = request.files.get(f'photo{i}')
            if photo:
                filename = secure_filename(f'photo{i}.jpg')
                photo_path = os.path.join(photo_dir, filename)
                photo.save(photo_path)
                photos.append(photo_path)
        
        # Save student info
        users[registration_number] = {
            'name': name,
            'section': section,
            'phone': phone,
            'photos': photos,
            'registration_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users(users)
        
        flash('Student registered successfully!', 'success')
        return redirect(url_for('sections'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('database', exist_ok=True)
    os.makedirs('DATASETS/registered_users', exist_ok=True)
    
    # Initialize files if they don't exist
    if not os.path.exists('database/users.json'):
        save_users({})
    if not os.path.exists('database/attendance_records.json'):
        save_attendance({})
    
    app.run(debug=True)