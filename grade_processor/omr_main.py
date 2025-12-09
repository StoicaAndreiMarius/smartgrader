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


def detect_answers(img, num_questions=20, num_options=5, darkness_threshold=0.6):
    """
    Detect marked answers on OMR sheet.
    Supports both single and multiple answer detection.

    Args:
        img: Preprocessed binary image
        num_questions: Number of questions
        num_options: Number of options per question
        darkness_threshold: Fraction of bubble that must be filled (0.0-1.0)

    Returns:
        Array of detected answers - int for single, list for multiple, None for unanswered
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

        # Calculate total pixels in each bubble region
        total_pixels = cols[0].size
        threshold_pixels = total_pixels * darkness_threshold

        # Find all bubbles above threshold
        marked_options = []

        for idx, col in enumerate(cols):
            white_pixels = cv2.countNonZero(col)

            if white_pixels > threshold_pixels:
                marked_options.append(idx)

        # Return result based on number of marks detected
        if len(marked_options) == 0:
            # No marks detected - unanswered
            detected_answers.append(None)
        elif len(marked_options) == 1:
            # Single mark - return as integer for backwards compatibility
            detected_answers.append(marked_options[0])
        else:
            # Multiple marks - return as sorted list
            detected_answers.append(sorted(marked_options))

    return detected_answers


def process_omr_image(image_path, num_questions=20, num_options=5, darkness_threshold=0.6):
    """
    Process an OMR image and return detected answers

    Args:
        image_path: Path to the OMR image
        num_questions: Number of questions on the test
        num_options: Number of options per question (default 5 for A-E)
        darkness_threshold: Fraction of bubble that must be filled (default 0.6)

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

        answers = detect_answers(img_threshold, num_questions, num_options, darkness_threshold)

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


def _normalize_to_set(answer):
    """
    Normalize answer to set for comparison.
    Handles backwards compatibility with integer format.

    Args:
        answer: Answer in int, list, tuple, or None format

    Returns:
        Set of answer indices
    """
    if answer is None:
        return set()
    elif isinstance(answer, (list, tuple)):
        return set(answer)
    elif isinstance(answer, int):
        return {answer}
    else:
        return set()


def _calculate_points(detected_set, correct_set, grading_mode):
    """
    Calculate points earned for a question.

    Args:
        detected_set: Set of detected answer indices
        correct_set: Set of correct answer indices
        grading_mode: "all_or_nothing" or "partial_credit"

    Returns:
        Float between 0.0 and 1.0
    """
    # Handle unanswered questions
    if len(detected_set) == 0:
        return 0.0

    # Handle empty correct answer set (shouldn't happen)
    if len(correct_set) == 0:
        return 0.0

    if grading_mode == "all_or_nothing":
        # Must match exactly - all correct, no incorrect
        return 1.0 if detected_set == correct_set else 0.0

    elif grading_mode == "partial_credit":
        # Proportional scoring with penalty for incorrect marks
        correct_marks = len(detected_set & correct_set)  # Intersection
        incorrect_marks = len(detected_set - correct_set)  # Detected but wrong
        total_correct = len(correct_set)

        # Formula: (correct_marks - incorrect_marks) / total_correct
        # Clamped to [0, 1]
        points = (correct_marks - incorrect_marks) / total_correct
        return max(0.0, min(1.0, points))

    else:
        # Unknown mode - default to all_or_nothing
        return 1.0 if detected_set == correct_set else 0.0


def grade_submission(detected_answers, correct_answers, grading_modes=None):
    """
    Grade a submission supporting multiple correct answers.

    Args:
        detected_answers: List of detected answers (int, list, or None)
        correct_answers: List of correct answers (int or list for compatibility)
        grading_modes: List of grading modes per question (optional)

    Returns:
        dict with score, total, percentage, and per-question details
    """
    if grading_modes is None:
        grading_modes = ["all_or_nothing"] * len(correct_answers)

    score = 0.0
    total = len(correct_answers)
    details = []

    for i, (detected, correct, mode) in enumerate(zip(detected_answers, correct_answers, grading_modes)):
        # Normalize to sets for comparison
        detected_set = _normalize_to_set(detected)
        correct_set = _normalize_to_set(correct)

        # Calculate points based on grading mode
        points = _calculate_points(detected_set, correct_set, mode)
        score += points

        details.append({
            'question': i + 1,
            'detected': detected,
            'correct': correct,
            'is_correct': points == 1.0,
            'points': points,
            'grading_mode': mode
        })

    percentage = (score / total * 100) if total > 0 else 0

    return {
        'score': score,
        'total': total,
        'percentage': round(percentage, 2),
        'details': details
    }
