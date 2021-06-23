# -*- coding: utf-8 -*-
"""Denpasar Temp  Timeseries Subbmission 2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kkd9ExcqmW_vYAArN8FC2hsxKj2j5_ax

Akbar
Submission 2
"""

# Menginstal package kaggle
!pip install -q kaggle

from google.colab import files

# Mengupload file json dari profile kaggle
files.upload()

# Membuat direktory dan mengubah izin file
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!ls ~/.kaggle

# Mendownload dataset
!kaggle datasets download -d cornflake15/denpasarbalihistoricalweatherdata

# Ekstrak file zip dan melihat isi dataset
!mkdir denpasarbalihistoricalweatherdata
!unzip denpasarbalihistoricalweatherdata.zip -d denpasarbalihistoricalweatherdata
!ls denpasarbalihistoricalweatherdata

import numpy as np
import pandas as pd

# Mengubah dataset menjadi dataframe
df = pd.read_csv('denpasarbalihistoricalweatherdata/openweatherdata-denpasar-1990-2020v0.1.csv')

df.head()

# Melihat isi total dari data
df.shape

# Mengecek nilai null
df.isnull().sum()

# Memilih kolom yang akan digunakan
df = df.iloc[200000:264924][['dt_iso', 'temp']]

# Konversi dt_iso ke Datetime Format
df['dt_iso'] = pd.to_datetime(df['dt_iso'])

# Mengubah nama kolom dt_iso
df.rename(columns={'dt_iso':'date'}, inplace=True)
df.head()

df.isnull().sum()

new_df = df[['date', 'temp']].copy()
new_df.set_index('date', inplace= True)

#resampling data menjadi mean tiap tanggal
new_df = new_df.resample('D').mean()
new_df.head()

df.isnull().sum()

import matplotlib.pyplot as plt

dates = df['date'].values
temp = df['temp'].values

# Membuat plot data
plt.figure(figsize=(15,5))
plt.plot(dates, temp)
plt.title('Temperature average', fontsize=20)

plt.figure(figsize=(35, 10))
plt.plot(new_df, linewidth=.5)
plt.grid()
plt.title('Denpasar Weather Temp 1990-2019')
plt.xlabel('Date')
plt.ylabel('Temperature')
plt.show()

from sklearn.model_selection import train_test_split

# Membagi dataset menjadi train dan test
X_train, X_test, Y_train, Y_test = train_test_split(temp, dates, test_size=0.2, shuffle=False)

print(len(X_train), len(X_test))

# merubah data menjadi format yang dapat diterima oleh model
def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

import tensorflow as tf
from keras.layers import Dense, LSTM

train_set = windowed_dataset(X_train, window_size=32, batch_size=64, shuffle_buffer=1000)
val_set = windowed_dataset(X_test, window_size=32, batch_size=64, shuffle_buffer=1000)

model = tf.keras.models.Sequential([                               
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.LSTM(64),
  tf.keras.layers.Dense(32, activation="relu"),
  tf.keras.layers.Dense(16, activation="relu"),
  tf.keras.layers.Dense(1)
])

optimizer = tf.keras.optimizers.SGD(learning_rate=1.0000e-04, momentum=0.9)

model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=['mae'])

min_mae = (new_df['temp'].max() - new_df['temp'].min()) * 0.1
print(min_mae)

# Membuat custom callbacks
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae') < min_mae):
      print('\nMAE has reach < 10% from total data!')
      self.model.stop_training = True

cust_callbacks = myCallback()

from keras.callbacks import ReduceLROnPlateau

hist = model.fit(train_set, validation_data=val_set, 
                 epochs=100, callbacks=[cust_callbacks, ReduceLROnPlateau()])

plt.plot(hist.history['mae'])
plt.plot(hist.history['val_mae'])
plt.title('Mean Absolut Error Model')
plt.ylabel('mae')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.title('Loss Model')
plt.xlabel('epoch')
plt.ylabel('loss')
plt.legend(['train', 'test'], loc='upper left')
plt.show()