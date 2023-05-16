import sys
import os
import csv
import pandas as pd
import plotly.graph_objs as go
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math

def load_csv_data(csv_file):
    timestamps = []
    values = []

    with open(csv_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            timestamp = pd.to_datetime(row[3], unit='s')
            timestamps.append(timestamp)
            values.append(float(row[4]))

    return pd.DataFrame({'ds': timestamps, 'y': values})

def process_workload(csv_file, workload_name):
    data = load_csv_data(csv_file)

    # Split the data into training (75%) and validation (25%) sets
    train_size = int(len(data) * 0.75)
    train_data = data.iloc[:train_size]
    validation_data = data.iloc[train_size:]

    # Train the Prophet model
    model = Prophet()
    model.fit(train_data)

    # Make predictions for the validation period
    future = model.make_future_dataframe(periods=len(validation_data), freq='30S')
    forecast = model.predict(future)

    # Plot the results using Plotly
    observed_trace = go.Scatter(x=data['ds'], y=data['y'], mode='lines', name='Observed')
    predicted_trace = go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Predicted')

    layout = go.Layout(
        title='Prophet Model Forecast vs Observed - ' + workload_name,
        xaxis=dict(title='Timestamp'),
        yaxis=dict(title='CPU Usage'),
    )

    fig = go.Figure(data=[observed_trace, predicted_trace], layout=layout)
    fig.write_image(f"plots/{workload_name}.png", format='png', width=1600, height=1200, scale=1.5)  # Save the figure as a static image
    fig.show()  # Display the figure

    # Calculate accuracy metrics
    actual = validation_data['y'].values
    predicted = forecast.iloc[-len(validation_data):]['yhat'].values

    # Calculate MAE, MSE, and RMSE as percentages
    mae = mean_absolute_error(actual, predicted) / max(actual) * 100
    mse = mean_squared_error(actual, predicted) / max(actual*actual) * 100
    rmse = math.sqrt(mse) / max(actual) * 100

    return mae, mse, rmse


if len(sys.argv) != 2:
    print("Usage: python3 scriptname.py folder_path")
else:
    folder_path = sys.argv[1]
    output_file = "accuracy_metrics.csv"

    if not os.path.exists("plots"):
        os.mkdir("plots")

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Workload', 'MAE', 'MSE', 'RMSE'])

        for file in os.listdir(folder_path):
            if file.endswith(".csv"):
                workload_name = file[:-4]
                csv_file = os.path.join(folder_path, file)
                mae, mse, rmse = process_workload(csv_file, workload_name)
                print(f"{workload_name}: MAE={mae:.2f}, MSE={mse:.2f}, RMSE={rmse:.2f}")
                writer.writerow([workload_name, mae, mse, rmse])
