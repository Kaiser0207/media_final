import cv2
import numpy as np
import threading
import queue

shape_queue = queue.Queue()

def drawing_window():
    # Create a blank canvas
    canvas = np.zeros((720, 400, 3), dtype=np.uint8)
    drawing = False
    last_point = None
    shape_detected = "None"

    def draw(event, x, y, flags, param):
        nonlocal drawing, last_point, shape_detected
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            last_point = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if last_point is not None:
                cv2.line(canvas, last_point, (x, y), (255, 255, 255), 2)
                last_point = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            last_point = None
            # Detect shape after drawing
            shape_detected = detect_shape(canvas)
            # 将检测到的形状放入队列
            shape_queue.put(shape_detected)

    def detect_shape(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
            if len(approx) == 3:
                return "Triangle"
            elif len(approx) == 4:
                return "Rectangle"
            elif len(approx) > 4:
                return "Circle"
        return "None"

    cv2.namedWindow("Drawing Window")
    cv2.setMouseCallback("Drawing Window", draw)

    while True:
        display_canvas = canvas.copy()
        cv2.putText(display_canvas, f"Shape: {shape_detected}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Drawing Window", display_canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Press 'Esc' to exit
            break
        elif key == 13:  # Press 'Enter' to clear the canvas
            canvas[:] = 0

    cv2.destroyAllWindows()

def start_drawing_thread():
    thread = threading.Thread(target=drawing_window, daemon=True)
    thread.start()

def get_shape_from_queue():
    if not shape_queue.empty():
        return shape_queue.get()
    return "None"

