import time
import redis
from flask import Flask, render_template
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Docker
import base64
from io import BytesIO

load_dotenv()
cache = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, password=os.getenv("REDIS_PASSWORD", ""))
app = Flask(__name__)

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr("hits")
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

def create_survival_chart():
    """Create a bar chart showing survival by gender"""
    try:
        # Load Titanic data
        df = pd.read_csv('static/data/titanic.csv')
        
        # Group by sex and survived
        survival_data = df.groupby(['Sex', 'Survived']).size().unstack(fill_value=0)
        
        # Create the plot
        plt.figure(figsize=(10, 6))
        survival_data.plot(kind='bar', color=['#ff6b6b', '#4ecdc4'])
        plt.title('Titanic Survival by Gender', fontsize=16, color='white')
        plt.xlabel('Gender', fontsize=12, color='white')
        plt.ylabel('Number of People', fontsize=12, color='white')
        plt.legend(['Did not survive', 'Survived'], loc='upper right')
        plt.xticks(rotation=0)
        
        # Style the plot for dark theme
        plt.gca().set_facecolor('#2b3035')
        plt.gcf().set_facecolor('#212529')
        plt.gca().tick_params(colors='white')
        plt.gca().spines['bottom'].set_color('white')
        plt.gca().spines['top'].set_color('white')
        plt.gca().spines['right'].set_color('white')
        plt.gca().spines['left'].set_color('white')
        
        # Convert plot to base64 string
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', facecolor='#212529')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    except Exception as e:
        return None

@app.route("/")
def hello():
    count = get_hit_count()
    return render_template("hello.html", count=count)

@app.route("/titanic")
def titanic():
    try:
        # Load Titanic data
        df = pd.read_csv('static/data/titanic.csv')
        
        # Get first 5 rows as HTML
        table_html = df.head().to_html(classes='table', table_id='titanic-table', escape=False)
        
        # Create survival chart
        chart_url = create_survival_chart()
        
        # Calculate some stats
        total_passengers = len(df)
        survived = len(df[df['Survived'] == 1])
        survival_rate = round((survived / total_passengers) * 100, 1)
        
        return render_template("titanic.html", 
                             table_html=table_html,
                             chart_url=chart_url,
                             total_passengers=total_passengers,
                             survived=survived,
                             survival_rate=survival_rate)
    except Exception as e:
        return render_template("titanic.html", 
                             error=f"Error loading Titanic data: {str(e)}",
                             table_html="",
                             chart_url=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)