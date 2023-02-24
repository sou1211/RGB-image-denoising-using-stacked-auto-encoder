# -*- coding: utf-8 -*-
"""RGB_img_denoise.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DNnhk3t0jYbBYx-b1jDYkrF1_MI96hjj
"""

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import cv2
!pip install kaggle
!apt-get install p7zip-full

from google.colab import files
files.upload() #need to upload the kaggle.json file for kaggle dataset

!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json #changing the permission for opening kaggle dataset

!kaggle competitions download -c cifar-10 #downloading the kaggle dataset

!p7zip -d train.7z

def plot_images(img):
  fig, axes = plt.subplots(2, 8, figsize=(13, 3))
  for i in range(8):
    axes[0,i].imshow(img[i])
    axes[0,i].axis('off')
    axes[1,i].imshow(img[i+8])
    axes[1,i].axis('off')

img_database = []
base_path = '/content/'
cartoon = base_path + 'train/'
for img in os.listdir(cartoon):
  try:
    img_array = cv2.imread(os.path.join(cartoon, img))
    img_database +=[img_array]

  except Exception as e:
    pass

img_database = np.array(img_database)  #converting to numpy array
print(img_database.shape) #printing the shape of the database
total_num_images = 2000 #selecting no of imgs for training purpose
img_database = np.array(img_database[0:total_num_images]) #selecting 2000 samples
orig_img = img_database.astype('float32') #changing the img datatype
orig_img = orig_img/255 #scaling the img
plot_images(orig_img) #plotting the imgs

orig_img_noisy = orig_img + 0.1 * np.random.normal(loc=0.0, scale=1.0, size= orig_img.shape) #creating noisy imgs
orig_img_noisy = np.clip(orig_img_noisy, 0, 1) #setting the magnitude b\w 0 & 1
plot_images(orig_img_noisy) #plotting the imgs

X_T = np.transpose(orig_img, (0,3,1,2)) #transposing rgb_img into 3 different independent imgs
X_T_noise = np.transpose(orig_img_noisy, (0,3,1,2))

X_flat = X_T.reshape(-1, 1024)
X_flat_noise = X_T_noise.reshape(-1, 1024) #flatted all pixels in 1 dimension

#parameters
learning_rate = 0.001
training_epochs = 10000
batch_size = 100
display_step = 100
examples_to_show = 8

#network parameters
n_hidden_1 = 512
n_hidden_2 = 256
n_hidden_3 = 128
n_input = 1024 #input img shape 32*32

#tensorflow graph input
X = tf.placeholder("float", [None, n_input])
Y = tf.placeholder("float", [None, n_input])

weights = {
    'encoder_h1': tf.Variable(tf.truncated_normal([n_input, n_hidden_1], stddev=0.01)),
    'encoder_h2': tf.Variable(tf.truncated_normal([n_hidden_1, n_hidden_2], stddev=0.01)),
    'encoder_h3': tf.Variable(tf.truncated_normal([n_hidden_2, n_hidden_3], stddev=0.01)),
    'decoder_h1': tf.Variable(tf.truncated_normal([n_hidden_3, n_hidden_2], stddev=0.01)),
    'decoder_h2': tf.Variable(tf.truncated_normal([n_hidden_2, n_hidden_1], stddev=0.01)),
    'decoder_h3': tf.Variable(tf.truncated_normal([n_hidden_1, n_input], stddev=0.01))
}
biases = {
    'encoder_b1': tf.Variable(tf.truncated_normal([n_hidden_1], stddev=0.01)),
    'encoder_b2': tf.Variable(tf.truncated_normal([n_hidden_2], stddev=0.01)),
    'encoder_b3': tf.Variable(tf.truncated_normal([n_hidden_3], stddev=0.01)),
    'decoder_b1': tf.Variable(tf.truncated_normal([n_hidden_2], stddev=0.01)),
    'decoder_b2': tf.Variable(tf.truncated_normal([n_hidden_1], stddev=0.01)),
    'decoder_b3': tf.Variable(tf.truncated_normal([n_input], stddev=0.01))
}
#Building the encoder
def encoder(x):
  #encoder hidden layer with sigmod activation
  layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['encoder_h1']), biases['encoder_b1']))
  layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['encoder_h2']), biases['encoder_b2']))
  layer_3 = tf.nn.sigmoid(tf.add(tf.matmul(layer_2, weights['encoder_h3']), biases['encoder_b3']))
  return layer_3

#building the decoder
def decoder(x):
  #decoder activation with sigmod activation
  layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['decoder_h1']), biases['decoder_b1']))
  layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['decoder_h2']), biases['decoder_b2']))
  layer_3 = tf.nn.sigmoid(tf.add(tf.matmul(layer_2, weights['decoder_h3']), biases['decoder_b3']))
  return layer_3

#contructing model
encoder_op = encoder(X)
decoder_op = decoder(encoder_op)
#prediction
y_pred = decoder_op
#define loss and optimizer, minimizing the MSE
cost = tf.reduce_mean(tf.pow(Y - y_pred, 2))
optimizer = tf.train.RMSPropOptimizer(learning_rate).minimize(cost)
#initialize the variable
init = tf.global_variables_initializer()

start = time.time()
total_batch = int(X_flat.shape[0]/batch_size)
sess = tf.Session()
sess.run(init)
#training cycle
for epoch in range(training_epochs):
  #loop over all batches
  start = 0; end = batch_size
  for i in range(total_batch-1):
    index = np.arange(start, end)
    np.random.shuffle(index)
    batch_xs = X_flat[index]
    batch_xsn = X_flat_noise[index]
    start = end; end = start+batch_size
    #run optimization op (backprop) and loss op (to get loss value)
    _, c = sess.run([optimizer, cost], feed_dict={X: batch_xsn, Y:batch_xs})
  #displaying logs per epoch step
  if (epoch%1000 == 0):
    print('Epoch: {0:05d}     loss: {1:f}'.format(epoch, c))
print("Optimization Finished")
end = time.time()
print("Time taken: {0}".format(end - start))
#random selecting some imgs for visualisation
#index are picked in orig_img.shape[0], then transfroming X_flat to corresponding RGB row
index = np.random.randint(orig_img.shape[0], size = examples_to_show)
index = np.sort(index)
RGB_index = np.concatenate((index*3, index*3+1, index*3+2))
RGB_index = np.sort(RGB_index)
denoised_image = sess.run(y_pred, feed_dict={X: X_flat_noise[RGB_index]})
#merging the RGB rows to RGB matrix
denoised_image = np.reshape(denoised_image, (examples_to_show, 3, 32, 32))
print(denoised_image.shape)
denoised_image = np.transpose(denoised_image, (0,2,3,1))
print(denoised_image.shape)
#compare original imgs with their reconstructions
f, a = plt.subplots(3, examples_to_show, figsize=(13,5))
for i in range(examples_to_show):
  a[0][i].imshow(orig_img[index[i]])
  a[0,i].axis('off')
  a[1][i].imshow(orig_img_noisy[index[i]])
  a[1,i].axis('off')
  a[2][i].imshow(denoised_image[i])
  a[2,i].axis('off')
f.show()
plt.draw()