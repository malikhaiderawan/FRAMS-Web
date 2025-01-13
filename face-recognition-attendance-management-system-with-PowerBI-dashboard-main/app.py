import base64
import csv
import datetime
import cv2
import os
from flask import Flask, render_template, Response, jsonify, request
import face_recognition
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from flask_mail import Mail, Message



app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'haidernawaz11220@gmail.com '  # Replace with your email
app.config['MAIL_PASSWORD'] = 'datd shwi rzfa upqv'  # Replace with your email password or app password
app.config['MAIL_DEFAULT_SENDER'] = 'haidernawaz11220@gmail.com'
mail = Mail(app)


# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

db = SQLAlchemy(app)

# Define model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)  # Time of entry
      # Store the exact time of recognition
    

    def __repr__(self):
        return f'<Attendance:{self.name}>'

# Create tables
with app.app_context():
    db.create_all()



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


class RecognizedAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)  # Time of recognition

    def __repr__(self):
        return f'<RecognizedAttendance:{self.name}>'

# Create tables for RecognizedAttendance
with app.app_context():
    db.create_all()

# Path to store captured images
IMAGE_FOLDER = 'static/uploads'
ATTENDANCE_FILE = 'attendance.csv'
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == "POST":
        print("Handling POST request")
        return render_template('new.html')
    else:
        print("Handling GET request")
        return "Everything is okay!"

@app.route('/all', methods=['GET', 'POST'])
def dataa():
    if request.method == "POST":
        rows = RecognizedAttendance.query.all()
        print("Handling POST request")
        return render_template('form3.html',rows=rows)
    else:
        print("Handling GET request")
        return "Is Everything okay!Plz Do login Admin Site!"
    
@app.route('/whole', methods=['GET', 'POST'])
def whole():
    if request.method == "POST":
        rows = Attendance.query.all()
        print("Handling POST request")
        return render_template('data.html',rows=rows)
    else:
        print("Handling GET request")
        return "Is Everything okay!Plz Do login Admin Site!"


# Load known face encodings
known_face_encodings = []
known_face_names = []


@app.route('/')
def index():
    return render_template('main.html')

@app.route('/capture', methods=['POST'])
def capture_image():

    """Capture the image from the client-side and save it."""
    try:
        data = request.get_json()
        image_data = data['image']

        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        image_path = os.path.join(IMAGE_FOLDER, f'face_{int(datetime.now().timestamp())}.jpg')

        with open(image_path, 'wb') as image_file:
            image_file.write(image_bytes)

        # Reload known faces after adding new image
        load_known_faces()
        generate_frames()

        return jsonify({
            "success": True,
            "message": "Image captured successfully!",
            "image_path": image_path
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to capture image: {str(e)}"
        })




@app.route('/submit', methods=['POST'])
def submit():
    # Get form data
    name = request.form['name']
    department = request.form['department']
    phone = request.form['phone']
    email = request.form['email']

    # Get the base64-encoded image data
    image_data = request.form['imageData']

    # Decode the image (base64 to bytes)
    try:
        # Remove the prefix "data:image/jpeg;base64," if it exists
        if image_data.startswith('data:image/jpeg;base64,'):
            image_data = image_data.replace('data:image/jpeg;base64,', '')
        
        # Decode base64 to raw image data
        img_bytes = base64.b64decode(image_data)

        # Save the raw image data to a file (as a .jpg)
        filename = (f"{name}.jpg")  # Securely create filename using name
        file_path = os.path.join(IMAGE_FOLDER, filename)
        
        with open(file_path, 'wb') as f:
            f.write(img_bytes)

        # Create a new entry in the database
        new_attendance = Attendance(
            name=name,
            department=department,
            phone=phone,
            email=email,
            image_path=file_path,
            
            
               )

        # Add the record to the database and commit the transaction
        db.session.add(new_attendance)
        db.session.commit()

        # Return success response
        return jsonify({"success": True, "message": "Form submitted successfully!"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


def generate_frames():
    """Generate video frames from the webcam."""
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            

         
         #For CSV file 

# def mark_attendance(name, department, phone, email):
#     """Mark attendance in a CSV file with additional user details."""
#     date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     attendance_file = 'attendance.csv'
    
#     # Check if the attendance file exists and write headers if not
#     if not os.path.exists(attendance_file):
#         with open(attendance_file, mode='w', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow(['Name', 'Department', 'Phone No', 'Email', 'Time'])

#     # Append the attendance record
#     with open(attendance_file, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow([name, department, phone, email, date_str])


@app.route('/video_feed')
def video_feed():
    """Stream the video feed."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reco', methods=['GET', 'POST'])
def reco():
    if request.method == "POST":
        return render_template('reco.html')
    else:
        return "Everything is okay!"


# This will hold the known face encodings and names in memory to reduce repeated loading

def load_known_faces():
    """Load known face encodings from the database folder."""
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []
    
    # Load faces from images in IMAGE_FOLDER (Only load once at app start or periodically)
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            image_path = os.path.join(IMAGE_FOLDER, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:  # Only add encoding if a face was detected
                encoding = encodings[0]
                known_face_encodings.append(encoding)
                known_face_names.append(os.path.splitext(filename)[0])
            else:
                print(f"No faces found in {filename}, skipping this image.")
    print(f"Loaded {len(known_face_encodings)} known faces.")



@app.route('/recoo', methods=['GET', 'POST'])
def recognize_face():
    today_date = datetime.now().date()
    # Ensure known faces are loaded
    camera = cv2.VideoCapture(0)
    load_known_faces() 
    
    success, frame = camera.read()
    
    if not success:
        return jsonify({"success": False, "message": "Failed to access the camera."})

    rgb_frame = frame[:, :, ::-1]
    
    # Detect face locations in the current frame
    face_locations = face_recognition.face_locations(rgb_frame)
    print(f"Found {len(face_locations)} faces in the frame.")

    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    if len(face_encodings) == 0:
        return jsonify({"success": False, "message": "No faces found in the frame."})
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        
        if True in matches:
            matched_idx = matches.index(True)
            name = known_face_names[matched_idx]
            
            # Fetch user details for the recognized person
            user_details = Attendance.query.filter_by(name=name).first()  # Fetch specific user by name

            if user_details:
                # Get the start and end of today for comparison
                start_of_day = datetime.combine(today_date, datetime.min.time())
                end_of_day = datetime.combine(today_date, datetime.max.time())
                
                # Check if the user has already marked attendance today
                existing_attendance = RecognizedAttendance.query.filter(
                    RecognizedAttendance.name == name,
                    RecognizedAttendance.recognition_time >= start_of_day,
                    RecognizedAttendance.recognition_time <= end_of_day
                ).first()

                if existing_attendance:
                    return jsonify({"success": False, "message": f"Attendance already marked for today."})

                # Insert recognized user details into the RecognizedAttendance model
                new_recognition = RecognizedAttendance(
                    name=user_details.name,
                    department=user_details.department,
                    phone=user_details.phone,
                    email=user_details.email,
                    image_path=user_details.image_path,
                    recognition_time=datetime.utcnow()  # Time when the recognition happened
                )
                db.session.add(new_recognition)
                db.session.commit()

                # Send an email to the user
                try:
                    msg = Message(
                        subject="Attendance Marked",
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[user_details.email],
                        body=f"Hello {name},\n\nYour attendance has been successfully recorded at {datetime.utcnow()}.\nThank you!"
                    )
                    mail.send(msg)
                    print(f"Email sent to {user_details.email}")
                except Exception as e:
                    print(f"Failed to send email: {str(e)}")

                return jsonify({"success": True, "message": f"Your attendance has been successfully recorded! A confirmation email has been sent.Plz Check Yours Mail!"})
            else:
                return jsonify({"success": False, "message": f"Your details not found in the database."})

    return jsonify({"success": False, "message": "No faces recognized."})





@app.route('/how',methods=["GET","POST"])
def how():
    return render_template('form.html')


@app.route('/data', methods=["GET", "POST"])
def data():
    if request.method == 'POST':
        user = request.form['username']
        pass1 = request.form['pass']
        
        if user == "Farooq" and pass1 == "1234":
            # Get today's date
            today_date = datetime.now().date()  # Get today's date
            
            # Query records in the RecognizedAttendance table for today's recognized users
            rows = RecognizedAttendance.query.filter(
                RecognizedAttendance.recognition_time >= datetime.combine(today_date, datetime.min.time()),  # Start of the day
                RecognizedAttendance.recognition_time < datetime.combine(today_date, datetime.max.time())  # End of the day
            ).all()
            
            if rows:
                return render_template('form2.html', message='Successfully Logged in', rows=rows)
            else:
                return render_template('form2.html', message='No recognition records for today.')
    
    return render_template('form1.html')




if __name__ == '__main__':
    app.run(debug=True)
