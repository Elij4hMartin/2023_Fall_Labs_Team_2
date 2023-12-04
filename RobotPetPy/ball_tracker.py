import cv2
import math
import numpy as np
from pupil_apriltags import Detector


class vision:
    def __init__(self, vid_device):
        self.tags_list = []
        self.objects = []
        self.tag_in_frame = False
        self.obj_in_frame = False
        self.vid = cv2.VideoCapture(vid_device)
        self.frame = None
        self.at_detector = Detector(
        families="tag36h11",
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
   )

    def getFrame(self):
        ret, self.frame = self.vid.read() 
        return self.frame

    def drawCross(self,img,center):
        height = img.shape[0]
        width = img.shape[1]

        heightB = round(center[1])
        widthB = round(center[0])
        # Drawing the lines'
        # print(heightB)
        cv2.line(img, (0, heightB), (width, heightB), (0, 0, 255), 2)
        cv2.line(img, (widthB, 0), (widthB, height), (0, 0, 255), 2)
        return img

    def getTag(self):
      self.getFrame()
      gray_image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY) 
      fx = ( gray_image.shape[0] / 2.0 ) / math.tan( (math.pi * 120/180.0 )/2.0 )
      fy = ( gray_image.shape[1] / 2.0 ) / math.tan( (math.pi * 120/180.0 )/2.0 )
      cx = gray_image.shape[0]/2
      cy = gray_image.shape[1]/2


      tags = self.at_detector.detect(gray_image, estimate_tag_pose=True, camera_params=[fx,fy,cx,cy], tag_size=1)
      self.tags_list = []
      # rotation matrix \
      if(len(tags) > 0):
         self.tag_in_frame = True
         temp_tag = tags[0]
         for tag in tags:
            Id = tags[0].tag_id
            # tag_center = tags[0].center
            if(tag.corners.sum() > temp_tag.corners.sum()):
               temp_tag = tag
         # print(tags[0].corners.sum())
         # self.drawCross(temp_tag.center)
         # print(temp_tag.tag_id)
         return temp_tag.tag_id
      else:
         # print("no tag detected")
         self.tag_in_frame = False
         return None

    def __del__(self):
        self.vid.release()
        cv2.destroyAllWindows() 
        print('Destructor called, vision deleted')

    def colorTrack(self):
        img = self.frame

        # convert to hsv colorspace
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # lower bound and upper bound for Green color
        lower_bound = np.array([20, 116, 137])	 
        upper_bound = np.array([53, 255, 255])

        # find the colors within the boundaries
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        #define kernel size  
        kernel = np.ones((7,7),np.uint8)

        # Remove unnecessary noise from mask

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.erode(mask,kernel,iterations = 1)


        # Segment only the detected region
        segmented_img = cv2.bitwise_and(img, img, mask=mask)

        # Find contours from the mask

        contours, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 1:
            print(len(contours[0])) 
            maxContour = contours[0]
            for obj in  contours:
                if len(obj) > len(maxContour):
                    maxContour = obj
                    contours = []
                    contours.append(maxContour)

        # print(len(contours))
        if  len(contours) == 0:
            print("no object detected")
            center = None
        else:
            center = self.findcenter(contours)
            print("center:{}".format(center))


        #     # print(len(contours[0]))


        output = cv2.drawContours(segmented_img, contours, -1, (0, 0, 255), 3)

        # Showing the output
        scale_percent = 30 # percent of original size
        width = int(output.shape[1] * scale_percent / 100)
        height = int(output.shape[0] * scale_percent / 100)
        dim = (width, height)
        
        # resize image
        resized = cv2.resize(output, dim, interpolation = cv2.INTER_AREA)
        if(center != None):
           output = self.drawCross(output,center)
        return output,center
        # cv2.imshow("Output", resized)                trackLego(ep_chassis,img,center)

        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
   
    def findcenter(self,contours):
        center= []
        leftTx = np.min(contours[0],axis=0)
        leftTy = np.min(contours[0],axis=0)

        rightTx = np.max(contours[0],axis=0)
        Bottomy = np.max(contours[0],axis=0)
        # print(Bottomy[0][1])
        center.append((leftTx[0][0]+rightTx[0][0])/2)
        center.append((leftTy[0][1]+Bottomy[0][1])/2)
        return center


if __name__ == '__main__':
    cam = vision(2)

    while True:
        cam.getFrame()
        output,center = cam.colorTrack()
        # output = cam.drawCross(output)
        cv2.imshow("img", output)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
    del cam
    print('Exiting')
    exit(1)