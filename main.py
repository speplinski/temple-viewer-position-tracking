import depthai as dai
import time
import cv2
import sys

from config import Config
from depth_tracker import DepthTracker
from terminal_utils import TerminalUtils
from visualizer import Visualizer
from column_analyzer import ColumnAnalyzer

class DepthApplication:
    def __init__(self):
        self.config = Config()
        self.depth_tracker = DepthTracker()
        self.visualizer = Visualizer(self.config)
        self.column_analyzer = ColumnAnalyzer(self.config)
        
        # Initialize counters
        self.frame_count = 0
        self.start_time = time.time()
        self.last_stats_update = 0
        self.stats_initialized = False
        
        # Initialize visualization buffer
        self.prev_buffer = self.visualizer.create_buffer()

    def create_pipeline(self):
        pipeline = dai.Pipeline()

        # Define sources and outputs
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)
        spatialLocationCalculator = pipeline.create(dai.node.SpatialLocationCalculator)

        xoutDepth = pipeline.create(dai.node.XLinkOut)
        xoutSpatialData = pipeline.create(dai.node.XLinkOut)
        xinSpatialCalcConfig = pipeline.create(dai.node.XLinkIn)

        # Set stream names
        xoutDepth.setStreamName("depth")
        xoutSpatialData.setStreamName("spatialData")
        xinSpatialCalcConfig.setStreamName("spatialCalcConfig")

        # Configure cameras
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoLeft.setCamera("left")
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoRight.setCamera("right")

        # Configure stereo depth
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DEFAULT)
        stereo.setLeftRightCheck(True)
        stereo.setSubpixel(True)
        spatialLocationCalculator.inputConfig.setWaitForMessage(False)

        # Configure spatial calculator ROIs
        for y in range(self.config.nV):
            for x in range(self.config.nH):
                config = dai.SpatialLocationCalculatorConfigData()
                config.depthThresholds.lowerThreshold = 200
                config.depthThresholds.upperThreshold = 10000
                config.roi = dai.Rect(
                    dai.Point2f((x)/self.config.nH, y/self.config.nV),
                    dai.Point2f((x+1)/self.config.nH, (y+1)/self.config.nV)
                )
                spatialLocationCalculator.initialConfig.addROI(config)

        # Link nodes
        monoLeft.out.link(stereo.left)
        monoRight.out.link(stereo.right)
        spatialLocationCalculator.passthroughDepth.link(xoutDepth.input)
        stereo.depth.link(spatialLocationCalculator.inputDepth)
        spatialLocationCalculator.out.link(xoutSpatialData.input)
        xinSpatialCalcConfig.out.link(spatialLocationCalculator.inputConfig)

        return pipeline

    def initialize_stats_display(self):
        """Initialize the static parts of the stats display"""
        print("\033[2J")  # Clear screen
        print("\033[?25l")  # Hide cursor
        
        # Draw frame
        TerminalUtils.move_cursor(1, 1)
        print("┏" + "━" * (self.config.nH * 2) + "┓")
        for i in range(self.config.nV):
            TerminalUtils.move_cursor(1, i + 2)
            print("┃" + " " * (self.config.nH * 2) + "┃")
        TerminalUtils.move_cursor(1, self.config.nV + 2)
        print("┗" + "━" * (self.config.nH * 2) + "┛")
        
        # Print static content
        TerminalUtils.move_cursor(1, self.config.nV + 4)
        print(f"Range: {self.config.MIN_THRESHOLD:.1f}m to {self.config.MAX_THRESHOLD:.1f}m")
        TerminalUtils.move_cursor(1, self.config.nV + 5)
        print("Controls:")
        TerminalUtils.move_cursor(1, self.config.nV + 6)
        print("  'q' - Exit")
        TerminalUtils.move_cursor(1, self.config.nV + 7)
        print("  'w' - Toggle window")
        TerminalUtils.move_cursor(1, self.config.nV + 8)
        print("  's' - Toggle stats")
        TerminalUtils.move_cursor(1, self.config.nV + 9)
        print("  'm' - Toggle mirror mode")
        
        # Initialize stats area
        TerminalUtils.move_cursor(1, self.config.nV + 11)
        print("FPS: 0.0")
        TerminalUtils.move_cursor(1, self.config.nV + 12)
        print(f"Mirror: {'ON' if self.config.MIRROR_MODE else 'OFF'}")
        TerminalUtils.move_cursor(1, self.config.nV + 13)
        print("Columns: 0,0,0,0,0,0,0,0,0,0")
        TerminalUtils.move_cursor(1, self.config.nV + 14)
        print("Counters: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]")

    def update_stats(self, distances, column_presence):
        if not self.stats_initialized:
            self.initialize_stats_display()
            self.stats_initialized = True
            return

        if not self.config.SHOW_STATS:
            return
            
        # Update FPS
        current_time = time.time()
        fps = self.frame_count / (current_time - self.start_time)
        
        # Update display
        TerminalUtils.move_cursor(1, self.config.nV + 11)
        print(f"FPS: {fps:.1f}        ", end='', flush=True)
        TerminalUtils.move_cursor(1, self.config.nV + 12)
        print(f"Mirror: {'ON' if self.config.MIRROR_MODE else 'OFF'}    ", end='', flush=True)
        
        # Update columns and counters
        current_columns = ','.join(map(str, column_presence))
        current_counters = str(self.depth_tracker.position_counters)
        
        TerminalUtils.move_cursor(1, self.config.nV + 13)
        print(f"Columns: {current_columns}     ", end='', flush=True)
        TerminalUtils.move_cursor(1, self.config.nV + 14)
        print(f"Counters: {current_counters}     ", end='', flush=True)

    def handle_key(self, key):
        """Handle key press events"""
        if key == 'q':
            return False
        elif key == 'w':
            self.config.DISPLAY_WINDOW = not self.config.DISPLAY_WINDOW
            if not self.config.DISPLAY_WINDOW:
                cv2.destroyAllWindows()
        elif key == 's':
            self.config.SHOW_STATS = not self.config.SHOW_STATS
            if not self.config.SHOW_STATS:
                # Clear stats area
                for i in range(11, 15):
                    TerminalUtils.move_cursor(1, self.config.nV + i)
                    print(" " * 50)
        elif key == 'm':
            self.config.MIRROR_MODE = not self.config.MIRROR_MODE
            # Update mirror mode display immediately
            if self.config.SHOW_STATS:
                TerminalUtils.move_cursor(1, self.config.nV + 12)
                print(f"Mirror: {'ON' if self.config.MIRROR_MODE else 'OFF'}    ", end='', flush=True)
        return True

    def run(self):
        try:
            pipeline = self.create_pipeline()
            
            with dai.Device(pipeline) as device:
                device.setIrLaserDotProjectorIntensity(0.5)
                
                depthQueue = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
                spatialCalcQueue = device.getOutputQueue(name="spatialData", maxSize=4, blocking=False)
                
                try:
                    old_terminal_settings = TerminalUtils.init_terminal()
                    running = True
                    self.last_stats_update = time.time()  # Initialize timer
                    
                    while running:
                        current_time = time.time()
                        self.frame_count += 1
                        
                        # Get depth data
                        inDepth = depthQueue.get()
                        spatialData = spatialCalcQueue.get().getSpatialLocations()
                        
                        distances = [depthData.spatialCoordinates.z / 1000 for depthData in spatialData]
                        
                        # Process data
                        column_presence = self.column_analyzer.analyze_columns(distances, self.config.MIRROR_MODE)
                        self.depth_tracker.update(column_presence)
                        
                        # Update UI at fixed intervals
                        if current_time - self.last_stats_update >= self.config.UI_REFRESH_INTERVAL:
                            self.prev_buffer = self.visualizer.create_console_heatmap(
                                distances, 
                                self.prev_buffer, 
                                self.config.MIRROR_MODE
                            )
                            self.update_stats(distances, column_presence)
                            self.last_stats_update = current_time  # Update timer
                        
                        # Handle window and keys
                        if self.config.DISPLAY_WINDOW:
                            heatmap = self.visualizer.create_heatmap(distances, self.config.MIRROR_MODE)
                            cv2.imshow("Depth Heatmap", heatmap)
                            key = cv2.waitKey(1)
                            if key != -1:
                                key = chr(key & 0xFF)
                            else:
                                key = None
                        else:
                            key = TerminalUtils.get_key()

                        if key:
                            running = self.handle_key(key)

                finally:
                    TerminalUtils.restore_terminal(old_terminal_settings)
                    print("\033[?25h")
                    if self.config.DISPLAY_WINDOW:
                        cv2.destroyAllWindows()
                    
        except RuntimeError as e:
            print("\nError: Cannot access the OAK-D camera!")
            print("Please check if another application is using the camera")
            print("or try reconnecting the device.\n")

if __name__ == "__main__":
    app = DepthApplication()
    app.run()