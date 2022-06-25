import logging
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy.signal import find_peaks, find_peaks_cwt
from random import random
from collections import Counter


class CaptchaImageProc:
    def __init__(self,img_path) -> None:
        img = cv2.imread(img_path)
        self.img_path = img_path
    
    def read_img(self):
        logging.info("Reading the Image")
        img = cv2.imread(self.img_path)
        return img
    
    def save_img(self, img_obj) -> None:
        logging.info("Writing the Image")
        cv2.imwrite(self.img_path, img_obj)
        
    def background_removal(self, noise_margin = 0, brightness = 1.5, contrast = 64) -> None:
        '''
        TODO: Reconginse multiple peaks from the histogram and clean all of them
        '''
        #Reading the image
        try:
            img = self.read_img()
        except Exception as e:
            logging.exception("Error in reading the image")
            return 
        logging.info("Started Background removal")
        hist = sorted([(intensity, freq) for intensity, freq in Counter(img.ravel()).items()], key=lambda x: x[0])[:-2]
        x = np.array([item[1] for item in hist])
        med = np.median(x)
        peaks, _ = find_peaks(x, height=med, distance=5)
        np.diff(peaks)
        peaks = sorted(peaks, reverse=True)
        og_shape = img.shape
        if noise_margin > 0:
            img = [((random()*noise_margin) + (255-noise_margin)) if x > peaks[1] else x for x in img.reshape(-1)]
        else:
            img = [255 if x > peaks[1] else x for x in img.reshape(-1)]

        img = np.array(img)
        img = img.reshape(og_shape)
        # alpha, beta = 1.5, -64  # Arrived at by testing with multiple cheques across a range of values. Details in google sheet titled "Cheque Key-Value Tests"
        img = brightness*img + contrast
        logging.info("Background removal completed")
        #saving the img
        try:
            self.save_img(img)
        except Exception as e:
            logging.exception("Error in saving the image")
            return
        return
    
    def inscrease_constrast(self, factor = 1):
        '''
        TODO: Creating an intelligent way to guess where to increase the contrast
        NOTE: Defaulting to 1 for all images now
        '''
        img = Image.open(self.img_path)
        enhancer = ImageEnhance.Contrast(img)
        img_output = enhancer.enhance(factor=factor)
        img_output.save(self.img_path)
    
    def convert_to_grayscale(self, img_obj):
        img = cv2.cvtColor(img_obj, cv2.COLOR_BGR2GRAY)
        return img

    def adaptive_thresholding(self, img_obj):
        img = cv2.adaptiveThreshold(img_obj, 255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 201, 15)
        return img
    
    def erossion(self, img, kernel_number = 3):
        kernel_to_erode = np.ones((kernel_number, kernel_number), np.uint8)
        erode = cv2.erode(img, kernel_to_erode) 
        return erode
    
    def dilate(self, img, kernel_number = 2):
        kernel_to_dilate = np.ones((kernel_number, kernel_number), np.uint8) 
        dilate = cv2.dilate(img, kernel_to_dilate)
        return dilate
    
    def noise_removal(self, img):
        img = cv2.bilateralFilter(img, 15, 75, 75)
        return img
    
    def clean_image(self):
        '''
        NOTE: This function aims at further cleaning, noise removal and thresholding the image for better OCR
        
            The Flow of the function 
                1. Noise Removal (Bilateral Filtering)
                2. Converting the Image into GrayScale
                3. Adaptive Thresholding (Gaussian)
                4. Erosion
                5. Dilation
        NOTE: The flow is subjected to further enhancements in future 
        '''
        
        #Reading the Image
        try:
            img = self.read_img()
        except Exception as e:
            logging.exception("Error in reading the image")
            return 
        
        logging.info("Started Cleaning the Image")
        noise_removed_img = self.noise_removal(img=img)
        grayscale_img = self.convert_to_grayscale(img_obj=noise_removed_img)
        thresholding = self.adaptive_thresholding(img_obj=grayscale_img)
        eroded_img = self.erossion(img=thresholding)
        dilated_img = self.dilate(img=eroded_img)
        logging.info("Completed Cleaning the Image")
        #saving the image
        try:
            self.save_img(dilated_img)
        except Exception as e:
            logging.exception("Error in saving the image")
            return
        return
    
    def process(self):
        '''
        NOTE: This the main function to use all the internal methods in order to process the image
        '''
        logging.info("Started processing the Image")
        self.background_removal()
        self.inscrease_constrast()
        self.clean_image()
        logging.info("Image Processing is ready, Image is ready for OCR!")


        
        