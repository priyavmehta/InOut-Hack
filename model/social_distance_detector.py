# import the necessary packages
from model.yolo import social_distancing_config as config
from model.yolo.detection import detect_people
from scipy.spatial import distance as dist
import numpy as np
import argparse
import imutils
import cv2
import os

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", type=str, default="", help="path to (optional) input image file")
ap.add_argument("-d", "--display", type=int, default=1, help="whether output be displayed")
args = vars(ap.parse_args())

# load the COCO class labels our YOLO model was trained on
labelsPath = 'model/' + os.path.sep.join([config.MODEL_PATH, "coco.names"])
print(labelsPath)
LABELS = open(labelsPath).read().strip().split("\n")

# derive the paths to the YOLO weights and model configuration
weightsPath = 'model/' +os.path.sep.join([config.MODEL_PATH, "yolov3.weights"])
configPath = 'model/' +os.path.sep.join([config.MODEL_PATH, "yolov3.cfg"])

# load our YOLO object detector trained on COCO dataset (80 classes)
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

# check if we are going to use GPU
if config.USE_GPU:
	# set CUDA as the preferable backend and target
	print("[INFO] setting preferable backend and target to CUDA...")
	net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
	net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# determine only the *output* layer names that we need from YOLO
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# initialize the video stream and pointer to output video file
# img = cv2.imread(args["input"] if args["input"] else 0)
# writer = None


# resize the frame and then detect people (and only people) in it
def detectSocialDistancing(img):
	img = imutils.resize(img, width=700)
	results = detect_people(img, net, ln, personIdx=LABELS.index("person"))

	# initialize the set of indexes that violate the minimum social
	# distance
	violate = set()

	# ensure there are *at least* two people detections (required in
	# order to compute our pairwise distance maps)
	if len(results) >= 2:
		# extract all centroids from the results and compute the
		# Euclidean distances between all pairs of the centroids
		centroids = np.array([r[2] for r in results])
		D = dist.cdist(centroids, centroids, metric="euclidean")

		# loop over the upper triangular of the distance matrix
		for i in range(0, D.shape[0]):
			for j in range(i + 1, D.shape[1]):
				# check to see if the distance between any two
				# centroid pairs is less than the configured number
				# of pixels
				if D[i, j] < config.MIN_DISTANCE:
					# update our violation set with the indexes of
					# the centroid pairs
					violate.add(i)
					violate.add(j)

	print(len(results))
	print(len(violate))
	return [len(violate), len(results)]

# # loop over the results
# for (i, (prob, bbox, centroid)) in enumerate(results):
# 	# extract the bounding box and centroid coordinates, then
# 	# initialize the color of the annotation
# 	(startX, startY, endX, endY) = bbox
# 	(cX, cY) = centroid
# 	color = (0, 255, 0)

# 	# if the index pair exists within the violation set, then
# 	# update the color
# 	if i in violate:
# 		color = (0, 0, 255)

# 	# draw (1) a bounding box around the person and (2) the
# 	# centroid coordinates of the person,
# 	cv2.rectangle(img, (startX, startY), (endX, endY), color, 2)
# 	cv2.circle(img, (cX, cY), 5, color, 1)

# # draw the total number of social distancing violations on the
# # output img
# text = "Social Distancing Violations: {}".format(len(violate))
# cv2.putText(img, text, (10, img.shape[0] - 25),
# 	cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)

# if args["display"] > 0:
# 	# show the output img
# 	cv2.imshow("img", img)
# 	key = cv2.waitKey(0) & 0xFF

# # USAGE
# # python social_distance_detector.py --input pedestrians.jpg