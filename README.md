# Dashcam Video Compiler

A Python script that creates a compilation video by extracting and combining random clips from multiple MP4 files.

## Features

- Recursively scans directories for MP4 files
- Extracts random clips of configurable duration from source videos
- Combines clips into a single compilation video
- Preserves original video quality using stream copy
- Supports both command-line arguments and interactive input
- Progress tracking with status updates
- **Date-based filtering**: Filter clips by date range based on filename timestamps
- **Month filtering**: Convenient option to filter clips for a specific month

## Prerequisites

- Python 3.x
- FFmpeg (must be installed and accessible in system PATH)
- Required Python packages:
  ```
  tqdm
  ```

## Installation

1. Clone this repository or download the script
2. Install the required Python package:
   ```bash
   pip install tqdm
   ```
3. Ensure FFmpeg is installed on your system

## Usage

You can run the script in two ways:

### Interactive Mode

Simply run the script without arguments:

```bash
python main.py
```

The script will prompt you for:
- Input directory containing MP4 files
- Target duration for the final compilation
- Output filename

### Command-line Mode

Run the script with command-line arguments:

```bash
python main.py --input-dir "/path/to/videos" --duration 30 --output "compilation.mp4"
```

Arguments:
- `--input-dir`: Directory containing MP4 files (default: "/Volumes/video/Ford F150 Lightning Dashcam")
- `--duration`: Target duration in seconds for the final video
- `--output`: Output filename (default: "compiled-video.mp4")
- `--start-date`: Start date for filtering files (formats: YYYY-MM-DD, YYYY-MM, YYYYMMDD, YYYYMM)
- `--end-date`: End date for filtering files (formats: YYYY-MM-DD, YYYY-MM, YYYYMMDD, YYYYMM)
- `--month`: Filter for specific month (format: YYYY-MM or YYYYMM). Overrides start-date and end-date.

#### Date Filtering Examples

Filter clips from May 2025:
```bash
python main.py --month "2025-05" --duration 60 --output "may-compilation.mp4"
```

Filter clips from a specific date range:
```bash
python main.py --start-date "2025-05-01" --end-date "2025-05-31" --duration 60
```

Filter clips from May 1st to June 15th, 2025:
```bash
python main.py --start-date "20250501" --end-date "20250615" --duration 90
```

## Configuration

The script has some built-in constants that can be modified in the code:

- `CLIP_DURATION_RANGE`: Tuple defining the minimum and maximum duration (in seconds) for individual clips (default: 3-5 seconds)
- `OUTPUT_DIR`: Directory where the final video will be saved (default: "output")

## Output

- The script creates random clips from the source videos
- Clips are temporarily stored and then combined into a single video
- The final compilation is saved in the `output` directory
- Temporary files are automatically cleaned up after processing

## Error Handling

The script includes comprehensive error handling for:
- Invalid input directories
- Missing or corrupt video files
- FFmpeg processing errors
- Insufficient video duration
- File system issues

## Notes

- The script uses FFmpeg's stream copy mode for faster processing and to maintain original video quality
- Progress is displayed using a progress bar and status messages
- The actual duration of the final video might slightly exceed the target duration due to clip selection 