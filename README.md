# Viewer Position Tracking

Real-time viewer position tracking system using OAK-D camera for The Most Polish Landscape installation.

## Requirements

- Python 3.8 or newer
- OAK-D camera
- Linux or macOS (terminal-based UI)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/speplinski/tmpl-viewer-position-tracking.git
cd tmpl-viewer-position-tracking
```

2. Create and activate virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Connect OAK-D camera

2. Run the application:
```bash
python main.py
```

3. Controls:
- 'q' - Exit application
- 'w' - Toggle OpenCV window view
- 's' - Toggle statistics display
- 'm' - Toggle mirror mode

## Display Elements

- Heatmap: Shows real-time depth data visualization
- FPS: Current frames per second
- Mirror: Current mirror mode status (ON/OFF)
- Columns: Binary array showing current viewer presence (1) or absence (0) in each column
- Counters: Array showing sustained presence count for each column

## Data Logging

The application logs state changes to `tmpl.log` file. Each line contains an array of counters representing sustained presence in each column.

## Configuration

Key parameters can be adjusted in `config.py`:
- MIN_THRESHOLD: Minimum detection distance (0.4m default)
- MAX_THRESHOLD: Maximum detection distance (1.8m default)
- UI_REFRESH_INTERVAL: UI update rate (40ms default)
- COUNTER_INCREMENT_INTERVAL: Counter update interval (500ms default)