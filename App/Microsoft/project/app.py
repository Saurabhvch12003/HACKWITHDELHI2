from flask import Flask, render_template, request, jsonify, Response
import cv2
import numpy as np
import base64
from datetime import datetime
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import time
from ultralytics import YOLO
from PIL import Image
import io
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
import smtplib
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from datetime import timedelta


# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'space_tools')

EMAIL_SENDER = "chanchal053btcse22@igdtuw.ac.in"
EMAIL_PASSWORD = "dcompgffjspiflkv"  # ⚠ Keep private
EMAIL_RECEIVER = "chanchalchaudhary0101@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

ALERT_THROTTLE_MINUTES = int(os.getenv('ALERT_THROTTLE_MINUTES', 10))  # avoid spamming

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    detections_collection = db['detections']
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = None

# Global variables for camera and model
camera = None
model = None
detection_active = False
using_custom_model = False

#email imnmtegration
# ---- PDF Generation ----
def generate_pdf(messages_list, output_path):
   
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Safety Report / Alert", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 12))
    for i, msg in enumerate(messages_list, start=1):
        story.append(Paragraph(f"<b>{i}.</b> {msg}", styles['Normal']))
        story.append(Spacer(1, 6))
    doc.build(story)
    return output_path

# ---- Email Send ----
def send_email(subject, body, to_email=None, attachment_path=None, sender_name="Space Tools System"):
    to_email = to_email or EMAIL_RECEIVER
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("❌ Email credentials not set in environment. Skipping send.")
        return False

    msg = EmailMessage()
    msg['From'] = formataddr((sender_name, EMAIL_SENDER))
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            data = f.read()
            msg.add_attachment(data, maintype='application', subtype='pdf', filename=os.path.basename(attachment_path))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {to_email} : {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# ---- Alert Throttling ----
def can_send_alert(throttle_minutes=ALERT_THROTTLE_MINUTES):
    if db is None:
        return True
    since = datetime.now() - timedelta(minutes=throttle_minutes)
    count = detections_collection.count_documents({
        'timestamp': {'$gte': since},
        'alert_sent': True
    })
    return count == 0
  
# Load YOLOv8 model
def load_model():
    global model, using_custom_model
    try:

        model_path = r"C:\Users\Chanchal\Desktop\Hackathon_Dataset\HackByte_Dataset\runs\detect\train10\weights\best.pt"
        print("🔍 Looking for model at:", model_path)
        print("📁 Exists:", os.path.exists(model_path))

        # Try to load custom trained model first
        if os.path.exists(model_path):
            model = YOLO(model_path)
            using_custom_model = True
            print("✅ Custom YOLOv8 model loaded successfully")
            print("Classes:", model.names)
        else:
            # Fallback to pretrained model
            print(f"❌ Model file not found at {model_path}")
            using_custom_model = False
            return False
        
        return True
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False
    #         model = YOLO('model_path')
    #         print("✅ Pretrained YOLOv8 model loaded successfully")
    #     return True
    # except Exception as e:
    #     print(f"❌ Model loading failed: {e}")
    #     return False

# Initialize model on startup
load_model()

# Space tool classes mapping
SPACE_TOOLS = {
    0: 'Fire Extinguisher',
    1: 'Toolbox', 
    2: 'Oxygen Tank'
}

# For pretrained model, map some classes to our space tools
YOLO_TO_SPACE_TOOLS = {
    39: 'Fire Extinguisher',  # bottle -> Fire Extinguisher
    73: 'Toolbox',            # book -> Toolbox  
    67: 'Oxygen Tank'         # cell phone -> Oxygen Tank
}




def detect_tools(image):
    global using_custom_model
    """Detect tools in image using YOLOv8"""
    if model is None:
        return []
    
    try:
        results = model(image, conf=0.3)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Map class to space tool
                    # if os.path.exists('yolov8/best.pt'):
                    if using_custom_model:
                        tool_name = model.names.get(class_id, f'Unknown_{class_id}')
                        # Custom model
                        # tool_name = SPACE_TOOLS.get(class_id, f'Unknown_{class_id}')
                    else:
                        # Pretrained model mapping
                        tool_name = YOLO_TO_SPACE_TOOLS.get(class_id)
                    
                    if tool_name:
                        detections.append({
                            'tool': tool_name,
                            'confidence': float(confidence),
                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                        })
        
        return detections
    except Exception as e:
        print(f"Detection error: {e}")
        return []

# def save_detection(detections, image_source="webcam"):
#     """Save detection to MongoDB"""
#     if db is None:
#         return False
    
#     try:
#         detection_record = {
#             'timestamp': datetime.now(),
#             'source': image_source,
#             'detections': detections,
#             'tool_count': len(detections),
#             'tools_detected': [d['tool'] for d in detections],
#             'alert_status': 'normal' if len(detections) >= 2 else 'missing_tools'
#         }
        
#         detections_collection.insert_one(detection_record)
#         return True
#     except Exception as e:
#         print(f"Database save error: {e}")
#         return False

def save_detection(detections, image_source="webcam"):
    """Save detection to MongoDB and trigger alert if necessary"""
    if db is None:
        return False

    try:
        detection_record = {
            'timestamp': datetime.now(),
            'source': image_source,
            'detections': detections,
            'tool_count': len(detections),
            'tools_detected': [d['tool'] for d in detections],
            'alert_status': 'normal' if len(detections) >= 2 else 'missing_tools',
            'alert_sent': False
        }
        res = detections_collection.insert_one(detection_record)

        # --- Email Alert Logic: Only if alert_status = missing_tools ---
        if detection_record['alert_status'] == 'missing_tools':
            messages = []
            if len(detections) == 0:
                messages.append("All monitored tools are missing or not detected in the current frame.")
            else:
                messages.append(f"Detected tools: {', '.join(detection_record['tools_detected'])} (count={len(detections)})")
                missing = [t for t in ['Fire Extinguisher', 'Toolbox', 'Oxygen Tank'] if t not in detection_record['tools_detected']]
                if missing:
                    messages.append("Missing tools: " + ", ".join(missing))
                else:
                    messages.append("Some tools detected but count is less than expected.")

            messages.append(f"Source: {image_source}")
            messages.append(f"Time: {detection_record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

            urgent = len(detections) <= 1

            # Environment variables for email creds
            sender_email = os.getenv("EMAIL_SENDER", "SENDER_EMAIL@example.com")
            sender_password = os.getenv("EMAIL_PASSWORD", "YOURPASSWORD")
            to_email = os.getenv("EMAIL_RECEIVER", "receiver@example.com")

            if can_send_alert():
                pdf_path = f"alerts/alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                generate_pdf(messages, pdf_path)
                subject = ("⚠ URGENT: Multiple Safety Items Missing" if urgent else "⚠ Alert: Missing Safety Item(s)")
                body = "\n".join(messages)
                sent = send_email(subject, body, to_email=to_email, attachment_path=pdf_path)
                detections_collection.update_one({'_id': res.inserted_id}, {'$set': {'alert_sent': bool(sent)}})
            else:
                print("Alert suppressed due to throttle (recent alert sent).")
        return True
    except Exception as e:
        print(f"Database save error: {e}")
        return False


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/project')
def project():
    return render_template('project.html')

@app.route('/results')
def results():
    recent_detections = []
    if db is not None:
        try:
            recent = detections_collection.find().sort('timestamp', -1).limit(10)
            recent_detections = list(recent)
            for detection in recent_detections:
                detection['_id'] = str(detection['_id'])
                detection['timestamp'] = detection['timestamp'].isoformat()
        except Exception as e:
            print("⚠️ Error fetching detections:", e)

    return render_template('results.html', recent_detections=recent_detections)

 

@app.route('/usecase')
def usecase():
    return render_template('usecase.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/start_camera')
def start_camera():
    global camera, detection_active
    try:
        if camera is None:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                return jsonify({'success': False, 'error': 'Camera not accessible'})
        
        detection_active = True
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_camera')
def stop_camera():
    global camera, detection_active
    detection_active = False
    if camera:
        camera.release()
        camera = None
    return jsonify({'success': True})

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        global camera, detection_active
        
        while detection_active and camera:
            success, frame = camera.read()
            if not success:
                break
            
            # Detect tools in frame
            detections = detect_tools(frame)
            
            # Draw bounding boxes
            for detection in detections:
                x1, y1, x2, y2 = detection['bbox']
                confidence = detection['confidence']
                tool = detection['tool']
                
                # Draw rectangle
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"{tool}: {confidence:.2f}"
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Save detections if any found
            if detections:
                save_detection(detections, "webcam_live")
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_live_detections')
def get_live_detections():
    global camera
    if not detection_active or not camera:
        return jsonify({'detections': [], 'active': False})
    
    try:
        success, frame = camera.read()
        if success:
            detections = detect_tools(frame)
            return jsonify({'detections': detections, 'active': True})
    except:
        pass
    
    return jsonify({'detections': [], 'active': False})

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    try:
        # Read image
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect tools
        detections = detect_tools(cv_image)
        
        # Save to database
        save_detection(detections, f"upload_{file.filename}")
        
        # Encode image with detections for display
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{detection['tool']}: {detection['confidence']:.2f}"
            cv2.putText(cv_image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Convert back to base64 for frontend
        _, buffer = cv2.imencode('.jpg', cv_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'detections': detections,
            'image': f"data:image/jpeg;base64,{img_base64}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_stats')
def get_stats():
    if db is None:
        return jsonify({
            'total_detections': 0,
            'tools_summary': {},
            'recent_alerts': 0,
            'detection_trend': []
        })
    
    try:
        # Total detections
        total = detections_collection.count_documents({})
        
        # Tools summary
        pipeline = [
            {"$unwind": "$tools_detected"},
            {"$group": {"_id": "$tools_detected", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        tools_data = list(detections_collection.aggregate(pipeline))
        tools_summary = {item['_id']: item['count'] for item in tools_data}
        
        # Recent alerts (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_alerts = detections_collection.count_documents({
            'timestamp': {'$gte': yesterday},
            'alert_status': 'missing_tools'
        })
        
        # Detection trend (last 7 days)
        trend_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": datetime.now() - timedelta(days=7)}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        trend_data = list(detections_collection.aggregate(trend_pipeline))
        detection_trend = [{"date": item['_id'], "count": item['count']} for item in trend_data]
        
        return jsonify({
            'total_detections': total,
            'tools_summary': tools_summary,
            'recent_alerts': recent_alerts,
            'detection_trend': detection_trend
        })
        
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({
            'total_detections': 0,
            'tools_summary': {},
            'recent_alerts': 0,
            'detection_trend': []
        })
if __name__ == '__main__':
    print("🚀 Starting Space Station Tool Detection System...")
    print("📊 MongoDB:", "✅ Connected" if db is not None else "❌ Not Connected")
    print("🤖 YOLOv8 Model:", "✅ Loaded" if model else "❌ Not Loaded")
    print("🌐 Server starting on http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)

