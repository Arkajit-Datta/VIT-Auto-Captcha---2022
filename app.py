'''
FastAPI app to make the api end points
'''
'''
    ERROR DOCUMENTATIONS:
        1. (-1) -- Image file not sent or uploaded for processing
        2. (-2) -- Image file could not be saved in the server (Error at server side)
        3. (-3) -- Error in Processing the Image, send the request again to the server
        4. (-4) -- Error in OCR, Send the Image again to the server
        5. (-5) -- Error in receiving the OCR response 
'''
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import shutil
import os
import json
import requests
from Captcha_Image_Proc import CaptchaImageProc


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("pipeline").setLevel(logging.INFO)

app = FastAPI(title="VIT-AutoCaptcha-2022", version="1.0.0 beta")

#allowing the API to all the specefic orgins
origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8080",
]

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    logging.info("This api is up")
    return JSONResponse(
        status_code=200,
        content={
            "message": "The API is alive"
        }
    )

@app.post("/recogniseCaptcha/")
def recognise(captchaImg: UploadFile = File(...)):
    path_captcha_storage = "CaptchaImages"
    
    if captchaImg != None:
        captchaImg_filename = "captcha.png" #giving all the captchas the same name in order to manage space 
        path_captcha_storage_final = os.path.join(path_captcha_storage, captchaImg_filename)
        try:
            logging.info("Storing the Captcha Image")
            with open(path_captcha_storage_final,"wb") as buffer:
                shutil.copyfileobj(captchaImg.file, buffer)  
                logging.info("Captcha saved in storage")   
        except Exception as e:
            logging.error(e)
            logging.error("the file saving process didnt work properly")
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Image coulde not be saved properly",
                    "error_message": -2
                }
            )
    else:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Image not uploaded",
                "error_message": -1
            }
        )
    
    #now sending the image for image processing 
    captcha_img_proc = CaptchaImageProc(path_captcha_storage_final)
    try:
        captcha_img_proc.process()
    except Exception as e:
        logging.exception("error in processing the image")
        return JSONResponse(
            status_code=404,
            content={
                "message": "Error in Image processing",
                "error_message": -3
            }
        )
    #sending the captcha for OCR 
    captcha_img_file = open("CaptchaImages/captcha.png", "rb")
    ocr_url = "http://127.0.0.1:5000/doOcr/"
    try:
        response = requests.post(ocr_url, files={"captchaImg": captcha_img_file})
    except Exception as e:
        logging.exception("Error in OCR")
        return JSONResponse(
            status_code=404,
            content={
                "message": "Error in OCR",
                "error_message": -4
            }
        )
    if response.ok:
        result_dict = json.loads(response.text)
        logging.info(result_dict)
        if "error_message" in result_dict:
            logging.exception("Error in OCR, Error in the OCR Server")
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Error in OCR",
                    "error_message": -4
                }
            )
        else:
            logging.info("Successful OCR in Server Recieved the Results")
            captcha_res = result_dict["captcha"]
            return JSONResponse(
                status_code=200,
                content={
                    "captcha": captcha_res,
                    "message":"Successfull in extracting the captcha"
                }
            )
    else:
        return JSONResponse(
                status_code=404,
                content={
                    "message": "Error in OCR",
                    "error_message": -5
                }
            )
        
if __name__ == "__main__":
    uvicorn.run(
        app,
        port=8080,
        host="127.0.0.1",
    )