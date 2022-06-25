from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import imutils
import dlib
import cv2

EYE_AR_THRESH = 0.26
EYE_AR_CONSEC_FRAMES = 4
EYE_AR_CONSEC_FRAMES_CLOSED = 15
PAUSE_CONSEC_FRAMES = 35
WORD_PAUSE_CONSEC_FRAMES = 45
BREAK_LOOP_FRAMES = 60


def setup_detector_video(args):
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(args["shape_predictor"])

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    vs = VideoStream(src=0).start()
    return [vs, detector, predictor, lStart, lEnd, rStart, rEnd]


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    eye_ar = (A + B) / (2.0 * C)
    return eye_ar


class MorseClass(object):
    def __init__(self):
        args = {"shape_predictor": "shape_predictor.dat"}
        self.COUNTER = 0
        self.BREAK_COUNTER = 0
        self.EYES_OPEN_COUNTER = 0
        self.CLOSED_EYES = False
        self.WORD_PAUSE = False
        self.PAUSED = False

        (vs, detector, predictor, lStart, lEnd, rStart, rEnd) = setup_detector_video(args)

        self.vs = vs
        self.detector = detector
        self.predictor = predictor
        self.lStart = lStart
        self.lEnd = lEnd
        self.rStart = rStart
        self.rEnd = rEnd

        self.total_morse = ""
        self.morse_word = ""
        self.morse_char = ""

    def __del__(self):
        cv2.destroyAllWindows()
        self.vs.stop()

    def get_frame(self):
        frame = self.vs.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # detect faces in the grayscale frame
        rects = self.detector(gray, 0)
        for rect in rects:
            self.shape = self.predictor(gray, rect)
            self.shape = face_utils.shape_to_np(self.shape)
            self.leftEye = self.shape[self.lStart:self.lEnd]
            self.rightEye = self.shape[self.rStart:self.rEnd]
            self.left_eye_ar = eye_aspect_ratio(self.leftEye)
            self.right_eye_ar = eye_aspect_ratio(self.rightEye)
            self.eye_ar = (self.left_eye_ar + self.right_eye_ar) / 2.0
            self.leftEyeHull = cv2.convexHull(self.leftEye)
            self.rightEyeHull = cv2.convexHull(self.rightEye)
            cv2.drawContours(frame, [self.leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [self.rightEyeHull], -1, (0, 255, 0), 1)
            if self.eye_ar < EYE_AR_THRESH:
                self.COUNTER += 1
                self.BREAK_COUNTER += 1
                if self.COUNTER >= EYE_AR_CONSEC_FRAMES:
                    self.CLOSED_EYES = True
                if not self.PAUSED:
                    morse_char = ""
                if self.BREAK_COUNTER >= BREAK_LOOP_FRAMES:
                    break
            else:
                if self.BREAK_COUNTER < BREAK_LOOP_FRAMES:
                    self.BREAK_COUNTER = 0
                self.EYES_OPEN_COUNTER += 1
                if self.COUNTER >= EYE_AR_CONSEC_FRAMES_CLOSED:
                    self.morse_word += "-"
                    self.total_morse += "-"
                    self.morse_char += "-"
                    self.COUNTER = 0
                    self.CLOSED_EYES = False
                    self.PAUSED = True
                    self.EYES_OPEN_COUNTER = 0
                elif self.CLOSED_EYES:
                    self.morse_word += "."
                    self.total_morse += "."
                    self.morse_char += "."
                    self.COUNTER = 1
                    self.CLOSED_EYES = False
                    self.PAUSED = True
                    self.EYES_OPEN_COUNTER = 0
                elif self.PAUSED and (self.EYES_OPEN_COUNTER >=
                                      PAUSE_CONSEC_FRAMES):
                    self.morse_word += "/"
                    self.total_morse += "/"
                    self.morse_char = "/"
                    self.PAUSED = False
                    self.WORD_PAUSE = True
                    self.CLOSED_EYES = False
                    self.EYES_OPEN_COUNTER = 0
                    # keyboard.write(morse_code.from_morse(morse_word))
                    morse_word = ""
                elif self.WORD_PAUSE and self.EYES_OPEN_COUNTER >= WORD_PAUSE_CONSEC_FRAMES:
                    self.total_morse += "¦/"
                    self.morse_char = ""
                    self.WORD_PAUSE = False
                    self.CLOSED_EYES = False
                    self.EYES_OPEN_COUNTER = 0
                    # keyboard.write(morse_code.from_morse("¦/"))
            cv2.putText(frame, "EAR: {:.2f}".format(self.eye_ar), (300, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "{}".format(self.morse_char), (100, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        if self.BREAK_COUNTER >= BREAK_LOOP_FRAMES:
            self.BREAK_COUNTER = 0
        ret, img = cv2.imencode('.jpg', frame)
        return img.tobytes()
