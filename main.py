"""
Main entry point for the Standalone Chirona Mouse Controller.

Initializes the webcam, hand pose tracking models, and MouseController
to manipulate the OS cursor based on hand gestures without sign language bloat.
"""

import cv2
import time
import sys
import logging
import tkinter as tk
from tkinter import ttk

from core.config_manager import config_mgr
from core.hand_detector import HandDetector
from controllers.mouse_controller import MouseController

from config import (
    CAMERA_INDEX, CAM_WIDTH, CAM_HEIGHT,
    COLOR_PRIMARY, WINDOW_TITLE
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChironaMouseApp:
    def __init__(self):
        self._setup()
        
    def _setup(self):
        """Initialize models, controllers, and hardware."""
        self.mouse_controller = MouseController()
        
        # Initialize hand detector strictly for single hand mode
        self.detector = HandDetector(max_hands=1)
            
        # Initialize webcam
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        
        if not self.cap.isOpened():
            logging.error("Failed to open camera")
            sys.exit(1)
            
        # Runtime state variables
        self.prev_time = 0
        self.frame_count = 0

    def _handle_keypress(self):
        """Handle keyboard input. Returns False if app should exit."""
        key = cv2.waitKey(1) & 0xFF
            
        if key == ord('s'):
            # Toggle settings visibility
            if self.is_hidden:
                self.root.deiconify()
                self.is_hidden = False
            else:
                self.root.withdraw()
                self.is_hidden = True
            
        # Exit on Escape key or window close
        if key == 27 or cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
            return False
            
        return True

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Mouse Settings", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Helpers
        def create_slider(label, key, from_, to, resolution=1.0):
            frame = ttk.Frame(main_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            val_label = ttk.Label(frame, text=f"{config_mgr.get(key):.2f}")
            val_label.pack(side=tk.RIGHT)
            
            var = tk.DoubleVar(value=config_mgr.get(key))
            
            def on_change(*args):
                v = var.get()
                if resolution >= 1.0: v = int(v)
                val_label.config(text=f"{v:.2f}")
                config_mgr.set(key, v)
                
            slider = ttk.Scale(frame, from_=from_, to=to, variable=var, command=on_change)
            slider.pack(side=tk.BOTTOM, fill=tk.X, expand=True)
            return var
            
        create_slider("Smoothing Alpha", "SMOOTHING_ALPHA", 0.05, 1.0, 0.01)
        create_slider("Pinch Distance", "PINCH_DISTANCE", 10, 150, 1.0)
        create_slider("Scroll X Speed", "SCROLL_SPEED_MULTIPLIER_X", 0.1, 5.0, 0.1)
        create_slider("Scroll Y Speed", "SCROLL_SPEED_MULTIPLIER_Y", 0.1, 5.0, 0.1)
        create_slider("Click Cooldown", "CLICK_COOLDOWN", 0.1, 2.0, 0.05)
        create_slider("Finger Visual", "FINGER_CIRCLE_RADIUS", 5.0, 30.0, 1.0)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(main_frame, text="MediaPipe Settings (Requires Apply)").pack()
        
        self.det_conf_var = create_slider("Detection Conf", "DETECTION_CONFIDENCE", 0.1, 1.0, 0.01)
        self.trk_conf_var = create_slider("Tracking Conf", "TRACKING_CONFIDENCE", 0.1, 1.0, 0.01)
        
        def apply_mp():
            self.detector.update_settings(
                self.det_conf_var.get(),
                self.trk_conf_var.get()
            )
            config_mgr.set('DETECTION_CONFIDENCE', self.det_conf_var.get())
            config_mgr.set('TRACKING_CONFIDENCE', self.trk_conf_var.get())
        ttk.Button(main_frame, text="Apply MediaPipe Changes", command=apply_mp).pack(pady=10)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        def save_state():
            config_mgr.save_config()
        ttk.Button(main_frame, text="Save Configuration Defaults", command=save_state).pack(pady=5)
        
        ttk.Label(main_frame, text="Press 's' in video feed to toggle this module", foreground="gray").pack(side=tk.BOTTOM, pady=5)

    def update_frame(self):
        """Timer-driven frame processor fired by Tkinter."""
        success, frame = self.cap.read()
        if not success:
            logging.error("Failed to read frame")
            self.cleanup_and_exit()
            return

        frame = cv2.flip(frame, 1)
        hands_data = self.detector.detect(frame)
        frame = self.detector.draw_hands(frame, hands_data)
        
        self.frame_count += 1

        # Process first detected hand strictly for mouse control
        if hands_data:
            first_hand = hands_data[0]
            self.mouse_controller.process_frame(frame, first_hand, self.detector)

        # Calculate FPS
        current_time = time.time()
        fps = 1 / (current_time - self.prev_time) if self.prev_time > 0 else 0
        self.prev_time = current_time

        # Display info text overlays
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_PRIMARY, 2)
        cv2.putText(frame, 'Mode: Mouse Only', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_PRIMARY, 2)
        
        cv2.imshow(WINDOW_TITLE, frame)

        # Break loop if _handle_keypress asks to exit
        if not self._handle_keypress():
            self.cleanup_and_exit()
            return
            
        # Recursive native loop
        self.root.after(10, self.update_frame)

    def cleanup_and_exit(self):
        self.cleanup()
        self.root.quit()

    def run(self):
        """Main application runtime loop."""
        self.root = tk.Tk()
        self.root.title("Mouse Controller Settings")
        self.root.geometry("380x600")
        
        self.is_hidden = False
        self.setup_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_exit)
        self.root.after(10, self.update_frame)
        self.root.mainloop()

        self.cleanup()

    def cleanup(self):
        """Release resources."""
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = ChironaMouseApp()
    app.run()