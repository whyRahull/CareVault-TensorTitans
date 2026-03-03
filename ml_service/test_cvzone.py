
try:
    from cvzone.HandTrackingModule import HandDetector
    print("cvzone.HandTrackingModule imported successfully")
    detector = HandDetector(maxHands=2, detectionCon=0.8)
    print("HandDetector initialized")
except Exception as e:
    print(f"Failed to import/init cvzone: {e}")
    import traceback
    traceback.print_exc()
