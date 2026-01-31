from flask import Flask, render_template, request, jsonify, session
import numpy as np
import pickle
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load the model and scalers
model = pickle.load(open('models/model.pkl', 'rb'))
minmax_scaler = pickle.load(open('models/minmaxscaler.pkl', 'rb'))
standard_scaler = pickle.load(open('models/standscaler.pkl', 'rb'))

# Crop dictionary for mapping with additional info
crop_info = {
    1: {'name': 'rice', 'season': 'Kharif', 'water': 'High', 'ph_range': '5.0-6.5'},
    2: {'name': 'maize', 'season': 'Kharif', 'water': 'Moderate', 'ph_range': '5.5-7.0'},
    3: {'name': 'jute', 'season': 'Kharif', 'water': 'High', 'ph_range': '6.0-7.5'},
    4: {'name': 'cotton', 'season': 'Kharif', 'water': 'Moderate', 'ph_range': '5.5-7.5'},
    5: {'name': 'coconut', 'season': 'Whole Year', 'water': 'Moderate', 'ph_range': '5.0-8.0'},
    6: {'name': 'papaya', 'season': 'Whole Year', 'water': 'Moderate', 'ph_range': '5.5-7.0'},
    7: {'name': 'orange', 'season': 'Rabi', 'water': 'Moderate', 'ph_range': '6.0-7.5'},
    8: {'name': 'apple', 'season': 'Rabi', 'water': 'Moderate', 'ph_range': '5.5-7.0'},
    9: {'name': 'muskmelon', 'season': 'Summer', 'water': 'High', 'ph_range': '6.0-7.0'},
    10: {'name': 'watermelon', 'season': 'Summer', 'water': 'High', 'ph_range': '5.5-6.5'},
    11: {'name': 'grapes', 'season': 'Summer', 'water': 'Low', 'ph_range': '5.5-6.5'},
    12: {'name': 'mango', 'season': 'Summer', 'water': 'Low', 'ph_range': '5.5-7.5'},
    13: {'name': 'banana', 'season': 'Whole Year', 'water': 'High', 'ph_range': '5.5-7.0'},
    14: {'name': 'pomegranate', 'season': 'Rabi', 'water': 'Low', 'ph_range': '5.5-7.0'},
    15: {'name': 'lentil', 'season': 'Rabi', 'water': 'Low', 'ph_range': '6.0-7.0'},
    16: {'name': 'blackgram', 'season': 'Kharif', 'water': 'Moderate', 'ph_range': '6.0-7.5'},
    17: {'name': 'mungbean', 'season': 'Kharif', 'water': 'Moderate', 'ph_range': '6.0-7.5'},
    18: {'name': 'mothbeans', 'season': 'Kharif', 'water': 'Low', 'ph_range': '6.0-7.5'},
    19: {'name': 'pigeonpeas', 'season': 'Kharif', 'water': 'Low', 'ph_range': '5.0-7.0'},
    20: {'name': 'kidneybeans', 'season': 'Rabi', 'water': 'Moderate', 'ph_range': '6.0-7.5'},
    21: {'name': 'chickpea', 'season': 'Rabi', 'water': 'Low', 'ph_range': '5.5-7.0'},
    22: {'name': 'coffee', 'season': 'Whole Year', 'water': 'High', 'ph_range': '6.0-6.5'}
}

# Optimal ranges for parameters (for validation)
optimal_ranges = {
    'N': (0, 140),
    'P': (5, 145),
    'K': (5, 205),
    'temperature': (8.8, 43.7),
    'humidity': (14.3, 99.9),
    'ph': (3.5, 9.9),
    'rainfall': (20.2, 298.6)
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Show user history if available
    history = session.get('prediction_history', [])
    return render_template('dashboard.html', history=history)

@app.route('/recommendation')
def recommendation_page():
    return render_template('recommendation.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/crops')
def crops():
    return render_template('crops.html', crop_info=crop_info)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get form data
        print(f"Received prediction request at {datetime.now()}")
        N = float(request.form['nitrogen'])
        P = float(request.form['phosphorus'])
        K = float(request.form['potassium'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])
        
        # Validate inputs against optimal ranges
        validation_errors = validate_inputs(N, P, K, temperature, humidity, ph, rainfall)
        
        if validation_errors:
            print(f"Validation failed: {len(validation_errors)} errors found")
            return render_template('recommendation.html', 
                                 errors=validation_errors,
                                 form_data=request.form)
        
        # Prepare features for prediction
        print("Preprocessing features...")
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        
        # Scale the features
        features_minmax = minmax_scaler.transform(features)
        features_standard = standard_scaler.transform(features_minmax)
        
        # Make prediction
        print("Running model prediction...")
        prediction = model.predict(features_standard)
        crop_id = prediction[0]
        crop_data = crop_info.get(crop_id, {'name': 'Unknown Crop'})
        
        # Get probabilities for all crops
        probabilities = model.predict_proba(features_standard)[0]
        top_crops = get_top_crops(probabilities, crop_info, 3)
        
        print(f"Prediction complete. Recommended: {crop_data['name']}")
        
        # Save to session history

        history_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'crop': crop_data['name'],
            'parameters': {
                'N': N, 'P': P, 'K': K,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall
            }
        }
        
        if 'prediction_history' not in session:
            session['prediction_history'] = []
        
        session['prediction_history'].insert(0, history_entry)
        # Keep only last 10 predictions
        if len(session['prediction_history']) > 10:
            session['prediction_history'] = session['prediction_history'][:10]
        
        session.modified = True
        
        return render_template('results.html', 
                             prediction=crop_data['name'],
                             crop_data=crop_data,
                             top_crops=top_crops,
                             parameters=history_entry['parameters'])
    
    except Exception as e:
        return render_template('results.html', prediction=f"Error: {str(e)}")

def validate_inputs(N, P, K, temperature, humidity, ph, rainfall):
    errors = []
    params = [
        ('Nitrogen', N, optimal_ranges['N']),
        ('Phosphorus', P, optimal_ranges['P']),
        ('Potassium', K, optimal_ranges['K']),
        ('Temperature', temperature, optimal_ranges['temperature']),
        ('Humidity', humidity, optimal_ranges['humidity']),
        ('pH', ph, optimal_ranges['ph']),
        ('Rainfall', rainfall, optimal_ranges['rainfall'])
    ]
    
    for name, value, (min_val, max_val) in params:
        if value < min_val or value > max_val:
            errors.append(f"{name} value {value} is outside the typical range ({min_val}-{max_val})")
    
    return errors

def get_top_crops(probabilities, crop_info, n=3):
    crop_ids = list(crop_info.keys())
    sorted_indices = np.argsort(probabilities)[::-1]
    top_crops = []
    
    for i in range(min(n, len(crop_ids))):
        idx = sorted_indices[i]
        crop_id = idx + 1  # Adjust for 0-indexed array
        if crop_id in crop_info:
            top_crops.append({
                'name': crop_info[crop_id]['name'],
                'probability': round(probabilities[idx] * 100, 2)
            })
    
    return top_crops

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.get_json()
        
        N = float(data['nitrogen'])
        P = float(data['phosphorus'])
        K = float(data['potassium'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        ph = float(data['ph'])
        rainfall = float(data['rainfall'])
        
        # Prepare features for prediction
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        
        # Scale the features
        features_minmax = minmax_scaler.transform(features)
        features_standard = standard_scaler.transform(features_minmax)
        
        # Make prediction
        prediction = model.predict(features_standard)
        crop_id = prediction[0]
        crop_data = crop_info.get(crop_id, {'name': 'Unknown Crop'})
        
        # Get probabilities for all crops
        probabilities = model.predict_proba(features_standard)[0]
        top_crops = get_top_crops(probabilities, crop_info, 5)
        
        return jsonify({
            'success': True,
            'recommended_crop': crop_data['name'],
            'crop_data': crop_data,
            'top_crops': top_crops
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)