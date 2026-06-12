import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No se pudo abrir la camara en indice 0")
    exit(1)

for _ in range(10):
    cap.read()

ok, frame = cap.read()
if ok:
    cv2.imwrite("test_camera.jpg", frame)
    print("Foto guardada como test_camera.jpg")
else:
    print("No se pudo capturar el frame")

cap.release()
