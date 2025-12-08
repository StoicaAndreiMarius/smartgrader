import cv2
import numpy as np

def order_points(pts):
    """Order points clockwise: top-left, top-right, bottom-right, bottom-left"""
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  
    rect[3] = pts[np.argmax(diff)]  
    
    return rect


def find_answer_sheet(contours, img_original):
    """Find the largest rectangular contour (answer sheet)"""
    largest_area = 0
    largest_contour = None
    
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            area = cv2.contourArea(contour)
            if area > largest_area:
                largest_area = area
                largest_contour = approx
    
    if largest_contour is not None:
        pts = largest_contour.reshape(4, 2)
        rect = order_points(pts)
        
        output_width = 550
        output_height = 700
        
        dst = np.array([
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img_original, M, (output_width, output_height))
        
        return warped
    else:
        return None


def detect_answers(img, num_questions=20, num_options=5):
    """
    Detect marked answers on OMR sheet
    Returns array of selected answer indices for each question
    """
    height, width = img.shape
    
    target_height = (height // num_questions) * num_questions
    target_width = (width // num_options) * num_options
    
    if height != target_height or width != target_width:
        img = cv2.resize(img, (target_width, target_height))
    
    rows = np.vsplit(img, num_questions)
    detected_answers = []
    
    for row in rows:

        cols = np.hsplit(row, num_options)
        max_white_pixels = 0
        selected_option = -1
        
        for idx, col in enumerate(cols):
            white_pixels = cv2.countNonZero(col)
            if white_pixels > max_white_pixels:
                max_white_pixels = white_pixels
                selected_option = idx
        
        detected_answers.append(selected_option if selected_option != -1 else None)
    
    return detected_answers


def process_omr_image(image_path, num_questions=20, num_options=5):
    """
    Process an OMR image and return detected answers
    
    Args:
        image_path: Path to the OMR image
        num_questions: Number of questions on the test
        num_options: Number of options per question (default 5 for A-E)
    
    Returns:
        dict with 'success', 'answers', and 'error' keys
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {'success': False, 'error': 'Could not read image file'}
        
        imgWidth = 550
        imgHeight = 700
        img = cv2.resize(img, (imgWidth, imgHeight))

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)
    
        img_canny = cv2.Canny(img_blur, 10, 50)
        
        contours, _ = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        answer_sheet = find_answer_sheet(contours, img_gray)
        
        if answer_sheet is None:
            return {'success': False, 'error': 'Could not find answer sheet rectangle in image'}

        _, img_threshold = cv2.threshold(answer_sheet, 150, 255, cv2.THRESH_BINARY_INV)
        
        answers = detect_answers(img_threshold, num_questions, num_options)
        
        return {
            'success': True,
            'answers': answers,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing image: {str(e)}',
            'answers': None
        }


def grade_submission(detected_answers, correct_answers):
    """
    Grade a submission by comparing detected answers with correct answers
    
    Args:
        detected_answers: List of detected answer indices
        correct_answers: List of correct answer indices from test
    
    Returns:
        dict with score, total, percentage, and details
    """
    score = 0
    total = len(correct_answers)
    details = []
    
    for i, (detected, correct) in enumerate(zip(detected_answers, correct_answers)):
        is_correct = detected == correct
        if is_correct:
            score += 1
        
        details.append({
            'question': i + 1,
            'detected': detected,
            'correct': correct,
            'is_correct': is_correct
        })
    
    percentage = (score / total * 100) if total > 0 else 0
    
    return {
        'score': score,
        'total': total,
        'percentage': round(percentage, 2),
        'details': details
    }
