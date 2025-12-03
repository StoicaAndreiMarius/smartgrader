import cv2
import numpy as np


# Function to order points clockwise: top-left, top-right, bottom-right, bottom-left
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left (smallest sum)
    rect[2] = pts[np.argmax(s)]  # Bottom-right (largest sum)
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right (smallest difference)
    rect[3] = pts[np.argmax(diff)]  # Bottom-left (largest difference)
    
    return rect


def find_rect(contours, img_original):
    # Find the largest rectangular contour
    largest_area = 0
    largest_contour = None

    for contour in contours:
        # Approximate contour to reduce number of points
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # Check if it's a rectangle (4 sides)
        if len(approx) == 4:
            area = cv2.contourArea(contour)
            if area > largest_area:
                largest_area = area
                largest_contour = approx

    if largest_contour is not None:
        # Reshape and order the points
        pts = largest_contour.reshape(4, 2)
        rect = order_points(pts)
        
        # Calculate width and height of the rectangle
        (tl, tr, br, bl) = rect
        
        output_width = 550
        output_height = 700
        
        # Define destination points for the rectangle
        dst = np.array([
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1]
        ], dtype="float32")
        
        # Get perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # Apply perspective transform (use your original image, not the canny edge)
        warped = cv2.warpPerspective(img_original, M, (output_width, output_height))
        
        return warped
    else:
        print("No rectangle found!")
        
def split_rows(img):
    rows = np.vsplit(img, 20)
    return rows

def ans_matrix(img):
    matrix = []
    rows = split_rows(img)
    for row in rows:
        col = np.hsplit(row, 5)
        matrix.append(col)
    return matrix

def ans_matrix_val(img):
    return_mat = []
    matrix = ans_matrix(img)
    for row in matrix:
        temp_col_values = []
        for col in row:
            white_pixels = cv2.countNonZero(col)
            total_pixels = col.size
            if(white_pixels > ((20/100)*total_pixels)):
                temp_col_values.append(1)
            else:
                temp_col_values.append(0)
            # print(f"{white_pixels},{total_pixels}", end=" ")
        # print()
        return_mat.append(temp_col_values)
    return return_mat