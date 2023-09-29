import cv2
import numpy as np

from PIL import Image
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionPredictor
from img2vec_pytorch import Img2Vec
from agentware.agent_logger import Logger

logger = Logger()


class Object:
    def __init__(self, image=None, visual_embedding=None, description=""):
        self.image = image
        self.visual_embedding = visual_embedding
        self.description = description

    def __repr__(self) -> str:
        return f"{self.description}"


class ObjectTracker:
    DEFAULT_TRACK_MODEL = 'yolov8n.pt'

    def __init__(self, objects=[]) -> None:
        self.model = YOLO(self.DEFAULT_TRACK_MODEL)
        self.objects = objects
        self.img2vec = Img2Vec(cuda=False)

    def get_embedding(self, image):
        pil_image = Image.fromarray(image)
        # Get a vector from img2vec, returned as a torch FloatTensor
        vec = self.img2vec.get_vec(pil_image, tensor=False)
        return vec

    def cosine_similarity(self, array1, array2):
        dot_product = np.dot(array1, array2)
        norm_array1 = np.linalg.norm(array1)
        norm_array2 = np.linalg.norm(array2)
        cosine_similarity = dot_product / (norm_array1 * norm_array2)
        logger.debug(f"Cosine Similarity: {cosine_similarity}")
        return cosine_similarity

    def object_exists(self, object):
        pass

    def get_objects(self, image):
        result = self.model.track(image, persist=True)[0]
        print("names are", result.names)
        all_classes = result.names
        boxes = result.boxes
        # print("boxes are", boxes)
        # print("num boxes are", len(boxes.data))
        # print("classes are", [all_classes[c.item()] for c in boxes.cls])
        # Construct local objects
        objects = []
        for i in range(len(boxes.data)):
            x1, y1, x2, y2 = boxes.xyxy[i].numpy().astype(int)
            print(x1, y1, x2, y2)
            object_roi = image[y1:y2, x1:x2]
            # cv2.imwrite(f"./object_{i}.png", object_roi)
            # compare with stored objects
            # id = boxes.id[i].item()
            # print("id is", id)
            # Use class name as initial description.
            object_class_name = all_classes[boxes.cls[i].item()]
            objects.append(
                Object(image=object_roi, description=object_class_name))
        return objects

    def track_image(self, image):
        # Construct local objects
        objects = self.get_objects(image)
        for object in objects:
            if not object.visual_embedding:
                object.visual_embedding = self.get_embedding(object.image)
            similarity_threshold = 0.8
            object_is_new = True
            logger.debug(f"Looking for object {object} in existing list")
            for o in self.objects:
                similarity = self.cosine_similarity(
                    o.visual_embedding, object.visual_embedding)
                if similarity > similarity_threshold:
                    logger.info(f"object {object} exists")
                    object_is_new = False
                    break
            if object_is_new:
                logger.debug(f"Object {object} is new. Adding to list")
                self.objects.append(object)

    def track_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        all_results = []
        # Loop through the video frames
        while cap.isOpened():
            # Read a frame from the video
            success, frame = cap.read()

            if success:
                # Run YOLOv8 tracking on the frame, persisting tracks between frames
                objects = self.track_image(frame)
                # Visualize the results on the frame
                # annotated_frame = results[0].plot()
                all_results.append(results)
                # Display the annotated frame
                print("result is", results[0])
                # Get objects and their images
                # return the object images for object construction and comparison
                break
                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                # Break the loop if the end of the video is reached
                break

        # Release the video capture object and close the display window
        cap.release()
        cv2.destroyAllWindows()
        return all_results
