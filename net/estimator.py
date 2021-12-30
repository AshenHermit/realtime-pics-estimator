from io import BytesIO
from os import stat
from pathlib import Path
import sys
from typing import List, Union
import requests
import urllib
import traceback
import pickle
import gzip

import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import losses
from tensorflow.keras import optimizers
from tensorflow.keras import Sequential
from tensorflow.keras.applications import ResNet50, ResNet101, ResNet50V2, InceptionResNetV2
from tensorflow import keras
import numpy as np

import PIL.Image

from images.image import Image, ImageFormatter
from images.gatherer import ImagesGatherer, AnimePicsGatherer, Rule34Gatherer
from images.library import ImagesLibrary
from storable import StorableDriver

import random


CWD = Path(__file__).parent.resolve() if "__file__" in globals() else Path("C:/Users/user/Python/anime_estimator/images")

class NetConfig():
    image_width = 256
    image_height = 256
    image_depth = 3

class DatasetPart():
    def __init__(self) -> None:
        pass
    
    def data_generator(self):
        pass

    def get_random_data(self):
        pass

class ImagesLibPart(DatasetPart):
    def __init__(self, lib:ImagesLibrary, targets:Union[float, List[float]]=0) -> None:
        self.lib:ImagesLibrary = lib
        self.targets:np.array= np.array([targets]) if type(targets)!=list else np.array(targets)
        self.images = list(map(lambda x: ImagesLibPart.image_to_tensor(x), lib.images))

    def image_to_xs_ys(self, img:PIL.Image.Image):
        for idx,img in enumerate(self.lib.images):
            img = img.convert("RGB")
            x = np.array(img)
            y = np.array([self.targets[idx]])
            yield x, y

    @staticmethod
    def image_to_tensor(img:PIL.Image.Image):
        img = img.convert("RGB")
        img = img.resize((NetConfig.image_width, NetConfig.image_height))
        x = np.array(img)
        return x

    def data_generator(self):
        for idx, img_arr in enumerate(self.images):
            x = img_arr
            y = np.array([self.targets[idx%len(self.targets)]])
            yield x, y

    def get_random_data(self):
        idx = random.randrange(len(self.images))
        x = self.images[idx]
        y = np.array([self.targets[idx%len(self.targets)]])
        return x, y

class ImagesDataset():
    def __init__(self, shuffle=False, elements_count=6000, cache_filepath:Path=None) -> None:
        self.shuffle = shuffle
        self.elements_total = elements_count
        self.cache_filepath = cache_filepath
        # or CWD/"../images_dataset.cache"
        self.dataset:tf.data.Dataset=None
        self.parts:list[DatasetPart] = []

    def add_library(self, lib:ImagesLibrary, targets=0):
        part = ImagesLibPart(lib, targets)
        self.parts.append(part)
        return part

    def data_generator(self):
        if self.shuffle:
            for i in range(self.elements_total):
                part = random.choice(self.parts)
                yield part.get_random_data()
        else:
            for part in self.parts:
                for x, y in part.data_generator():
                    yield x, y

    def make_dataset(self):
        dataset:tf.data.Dataset = tf.data.Dataset.from_generator(
            self.data_generator, 
            (tf.float32, tf.float32),
            ((NetConfig.image_width, NetConfig.image_height, NetConfig.image_depth), (1,))
        )
        
        if self.cache_filepath: dataset = dataset.cache(str(self.cache_filepath))
        # dataset = dataset.shuffle(1000)
        dataset = dataset.batch(64)
        dataset = dataset.prefetch(25)

        self.dataset = dataset
        return dataset

class EstimatorNet():
    def __init__(self, model_save_filepath:Path=None, valid_ds:tf.data.Dataset=None) -> None:
        self.model = None
        self.model_save_filepath = model_save_filepath or CWD/"estimator_net_save"
        self.validation_data = valid_ds

        self.build_model()
        self.try_load()

    def try_load(self):
        try:
            self.model.load_weights(str(self.model_save_filepath))
            print("weights successfully loaded")
        except:
            print("failed loading weights. continuing")
            pass
    
    def save(self):
        print(f"saving weights to \"{self.model_save_filepath.as_posix()}\"...")
        self.model.save_weights(str(self.model_save_filepath))
        print("saved.")

    def build_model(self):
        resnet = ResNet50(include_top=False, pooling='avg', input_shape=(NetConfig.image_width, NetConfig.image_height, NetConfig.image_depth))
        model = Sequential([
            resnet,
            layers.Dense(1024),
            layers.Dense(1)
        ])
        model.layers[0].trainable = False
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.0005),
            loss=losses.MeanSquaredError(), 
            metrics=['accuracy'] if self.validation_data is not None else None)
        model.summary()
        self.model = model
        return model

    def train(self, dataset:tf.data.Dataset, epochs=10):
        
        print("training model...")
        history = self.model.fit(
            dataset,
            validation_data=self.validation_data,
            epochs=epochs
        )
        return history

    def plot_history(self, history, plot_filepath:Path=None, epochs=10):
        acc = history.history['accuracy'] or None
        val_acc = history.history['val_accuracy'] or None

        loss = history.history['loss']
        val_loss = history.history['val_loss'] or None

        epochs_range = range(epochs)
    
        plt.figure(figsize=(8, 8))
        plt.subplot(1, 2, 1)
        if acc: plt.plot(epochs_range, acc, label='Training Accuracy')
        if val_acc: plt.plot(epochs_range, val_acc, label='Validation Accuracy')
        plt.legend(loc='lower right')
        plt.title('Training and Validation Accuracy')

        plt.subplot(1, 2, 2)
        plt.plot(epochs_range, loss, label='Training Loss')
        if val_loss: plt.plot(epochs_range, val_loss, label='Validation Loss')
        plt.legend(loc='upper right')
        plt.title('Training and Validation Loss')
        plt.savefig(str(plot_filepath))

    def estimate(self, image:PIL.Image.Image):
        image = image.convert("RGB")
        image = image.resize((NetConfig.image_width, NetConfig.image_height))
        arr = np.array(image)
        arr = np.reshape(arr, tuple([1]+list(arr.shape)))
        inputs = tf.constant(arr)
        pred = self.model(inputs)
        pred.numpy()
        return pred