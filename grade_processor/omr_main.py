import cv2
import numpy as np
import utils

path = "../img/test2.png"
json = "../pdf_generator/questions.json"
imgWidth = 550
imgHeight = 700
img_og = cv2.imread(path)



img_og = cv2.resize(img_og, (imgWidth, imgHeight))
img_contours = img_og.copy()
img_grayscale = cv2.cvtColor(img_og, cv2.COLOR_BGR2GRAY)
img_blur = cv2.GaussianBlur(img_grayscale, (5,5), 1)
img_canny = cv2.Canny(img_blur, 10, 50)
contours, hierrarchy = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cv2.drawContours(img_contours, contours, -1, (0,255,0), 2)


rect = utils.find_rect(contours, img_grayscale)
rect_threshold = cv2.threshold(rect, 150, 255, cv2.THRESH_BINARY_INV)[1]


# cv2.imshow("original", img_og)
# cv2.imshow("grayscale", img_grayscale)
# cv2.imshow("blur", img_blur)
# cv2.imshow("canny", img_canny)
# cv2.imshow("contours", img_contours)
# cv2.imshow("answers", rect)
cv2.imshow("answers_threshold", rect_threshold)
# cv2.imshow("answer[0][0]", utils.ans_matrix(rect_threshold)[0][0])
# utils.ans_matrix_val(rect_threshold)

ans_matrix = utils.ans_matrix_val(rect_threshold, json)
cnt = 1
for row in ans_matrix:
    print(f"{cnt}. ", end="")
    cnt += 1
    for col in row:
        print(col, end=" ")
    print()

print(utils.qr_decoder(img_og))

cv2.waitKey(0)