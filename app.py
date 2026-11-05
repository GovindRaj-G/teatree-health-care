from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'teatree_secure_secret_key_2026'

# MySQL Database Configuration (User: root, Password: root)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/teatree_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(50), unique=True, nullable=False)
    pass_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class CampRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(50))
    regno = db.Column(db.String(50))
    pid = db.Column(db.String(50))
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi = db.Column(db.Float)
    bp = db.Column(db.String(20))
    pulse = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    temp = db.Column(db.Float)
    notes = db.Column(db.String(255))
    is_abnormal = db.Column(db.Boolean)
    recorded_by = db.Column(db.String(100))
    timestamp = db.Column(db.String(50))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(userid='admin').first():
        default_admin = User(
            userid='admin',
            pass_hash=generate_password_hash('1234'),
            name='System Administrator',
            role='System Admin'
        )
        db.session.add(default_admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('health_camp_app.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(userid=data.get('userid')).first()
    if user and check_password_hash(user.pass_hash, data.get('pass')):
        session['user'] = {'userid': user.userid, 'name': user.name, 'role': user.role}
        return jsonify({"status": "success", "user": session['user']})
    return jsonify({"status": "error", "message": "Invalid User ID or Password"}), 401

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    if User.query.filter_by(userid=data.get('userid')).first():
        return jsonify({"status": "error", "message": "User ID already exists"}), 400
    
    new_user = User(
        userid=data.get('userid'),
        pass_hash=generate_password_hash(data.get('pass')),
        name=data.get('name'),
        role=data.get('role')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "message": "Account created successfully"})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return jsonify({"status": "success"})

@app.route('/api/records', methods=['GET', 'POST'])
def handle_records():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if request.method == 'POST':
        data = request.json
        new_record = CampRecord(
            record_id=data.get('id'),
            regno=data.get('regno'),
            pid=data.get('pid'),
            name=data.get('name'),
            age=data.get('age'),
            gender=data.get('gender'),
            height=data.get('details', {}).get('height'),
            weight=data.get('details', {}).get('weight'),
            bmi=data.get('details', {}).get('bmi'),
            bp=data.get('details', {}).get('bp'),
            pulse=data.get('details', {}).get('pulse'),
            spo2=data.get('details', {}).get('spo2'),
            temp=data.get('details', {}).get('temp'),
            notes=data.get('details', {}).get('notes'),
            is_abnormal=data.get('isAbnormal'),
            recorded_by=session['user']['name'],
            timestamp=data.get('timestamp')
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"status": "success", "message": "Saved to database"})
    
    records = CampRecord.query.all()
    result = []
    for r in records:
        result.append({
            "id": r.record_id,
            "regno": r.regno,
            "pid": r.pid,
            "name": r.name,
            "age": r.age,
            "gender": r.gender,
            "details": {
                "height": r.height, "weight": r.weight, "bmi": r.bmi,
                "bp": r.bp, "pulse": r.pulse, "spo2": r.spo2, "temp": r.temp, "notes": r.notes
            },
            "isAbnormal": r.is_abnormal,
            "recordedBy": r.recorded_by,
            "timestamp": r.timestamp
        })
    return jsonify(result)

@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    record = CampRecord.query.filter_by(record_id=record_id).first()
    if record:
        db.session.delete(record)
        db.session.commit()
        return jsonify({"status": "success", "message": "Record deleted"})
    return jsonify({"status": "error", "message": "Record not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5500)