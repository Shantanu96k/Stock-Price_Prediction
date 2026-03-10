import pandas as pd

def preprocess_data(df):
    df = df.dropna()
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df.sort_index()
    return df[['Close']]  # use Close prices
