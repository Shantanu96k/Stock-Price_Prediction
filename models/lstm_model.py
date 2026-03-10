import numpy as np
import pandas as pd
import io
import base64
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objs as go
import plotly.io as pio

def plotly_forecast_plot(actual_dates, actual_data, future_dates, predicted_prices):
    trace1 = go.Scatter(x=actual_dates, y=actual_data.flatten(), mode='lines', name='Historical')
    trace2 = go.Scatter(x=future_dates, y=predicted_prices.flatten(), mode='lines+markers', name='Forecast')
    layout = go.Layout(title='LSTM Forecast (Interactive)', xaxis_title='Date', yaxis_title='Price')
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    return pio.to_html(fig, full_html=False)

def predict_lstm(data, n_days=30):   
    data = data.copy()
    data['Close'] = data['Close'].astype(str).str.replace(',', '').astype(float)
    dataset = data['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(dataset)
    X, y = [], []
    for i in range(60, len(scaled_data)):
        X.append(scaled_data[i-60:i])
        y.append(scaled_data[i])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(60, 1)))
    model.add(LSTM(units=50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=100, batch_size=32, verbose=0)    
    prediction_input = scaled_data[-60:]
    predictions = []
    for _ in range(n_days):
        pred = model.predict(prediction_input.reshape(1, 60, 1), verbose=0)[0][0]
        predictions.append(pred)
        prediction_input = np.append(prediction_input[1:], [[pred]], axis=0)
    predicted_prices = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))    
    future_dates = pd.date_range(data.index[-1], periods=n_days + 1, freq='B')[1:]
    plot_html = plotly_forecast_plot(data.index, dataset, future_dates, predicted_prices)
    return plot_html, predicted_prices.flatten()