import os
import random
import argparse
import subprocess
from tqdm import tqdm
import shlex
from datetime import datetime, date, timedelta

# Define directories
INPUT_DIR = r"/Volumes/video/Ford F150 Lightning Dashcam"
OUTPUT_DIR = "output"
OUTPUT_FILENAME = r"compiled-video.mp4"

# Constants
CLIP_DURATION_RANGE = (3, 5)  # Range for individual clip durations (min, max) in seconds

def get_user_input(prompt, default=None, validator=None):
    """Get user input with optional default value and validation."""
    while True:
        if default:
            user_input = input(f"{prompt} (default: {default}): ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if not user_input:
            print("Input cannot be empty. Please try again.")
            continue
            
        if validator:
            try:
                user_input = validator(user_input)
                break
            except ValueError as e:
                print(f"Invalid input: {e}")
                continue
        else:
            break
            
    return user_input

def validate_duration(value):
    """Validate duration input."""
    try:
        duration = float(value)
        if duration <= 0:
            raise ValueError("Duration must be greater than 0 seconds")
        return duration
    except ValueError:
        raise ValueError("Duration must be a positive number")

def validate_directory(value):
    """Validate directory input."""
    if not os.path.isdir(value):
        raise ValueError("Directory does not exist")
    return value

def get_mp4_files(directory):
    """Recursively scan the directory and return a list of MP4 file paths."""
    mp4_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith('.mp4'):
                filepath = os.path.join(root, f)
                mp4_files.append(filepath)
    
    if not mp4_files:
        raise ValueError(f"No matching MP4 files found in {directory} or its subdirectories")
    return mp4_files

def get_video_duration(video_path):
    """Get the duration of a video file using FFmpeg."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            shlex.quote(video_path)
        ]
        
        result = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error getting duration for {video_path}: {result.stderr}")
            return None
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Failed to get duration for {video_path}: {str(e)}")
        return None

def get_random_clip(video_path, clip_duration_range):
    """Extract a random clip of specified duration range from the video."""
    video_duration = get_video_duration(video_path)
    
    if video_duration is None:
        print(f"Skipping {video_path}: Could not determine video duration")
        return None
    
    # Ensure the video is long enough for the minimum clip duration
    if video_duration < clip_duration_range[0]:
        print(f"Skipping {video_path}: Video duration ({video_duration}s) is too short")
        return None
    
    # Randomly select clip duration within the range
    clip_duration = random.uniform(clip_duration_range[0], clip_duration_range[1])
    
    # Ensure the clip duration doesn't exceed the video duration
    clip_duration = min(clip_duration, video_duration)
    
    # Randomly select start time, ensuring the clip fits within the video
    max_start_time = video_duration - clip_duration
    start_time = random.uniform(0, max_start_time)
    
    # Create a temporary clip file
    temp_clip = f"temp_clip_{random.randint(1000, 9999)}.mp4"
    
    try:
        # Extract the clip using FFmpeg
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-t', str(clip_duration),
            '-i', shlex.quote(video_path),
            '-c', 'copy',  # Copy streams without re-encoding
            '-y',  # Overwrite output file if it exists
            shlex.quote(temp_clip)
        ]
        
        result = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error creating clip from {video_path}: {result.stderr}")
            if os.path.exists(temp_clip):
                os.remove(temp_clip)
            return None
            
        # Verify the clip was created and has content
        if not os.path.exists(temp_clip) or os.path.getsize(temp_clip) == 0:
            print(f"Failed to create clip from {video_path}: Output file is missing or empty")
            return None
            
        return temp_clip
    except Exception as e:
        print(f"Failed to create clip from {video_path}: {str(e)}")
        if os.path.exists(temp_clip):
            os.remove(temp_clip)
        return None

def compile_clips(clips, target_duration, output_path):
    """Compile clips into a single video using FFmpeg."""
    if not clips:
        raise ValueError("No clips to compile")
    
    print(f"\nAttempting to compile {len(clips)} clips...")
    
    # Create a temporary file with the list of clips
    with open('clips.txt', 'w') as f:
        for clip in clips:
            # Escape single quotes in the path and wrap in single quotes
            escaped_path = clip.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    try:
        # Concatenate clips using FFmpeg
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', 'clips.txt',
            '-c', 'copy',
            '-y',
            shlex.quote(output_path)
        ]
        
        print(f"Writing output video to {output_path}...")
        result = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error during compilation: {result.stderr}")
            raise ValueError("Failed to compile clips")
            
        # Verify the output file was created and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ValueError("Output file is missing or empty")
            
        print(f"Successfully compiled video saved to {output_path}")
    except Exception as e:
        print(f"Failed to compile clips: {str(e)}")
        raise
    finally:
        # Clean up temporary files
        if os.path.exists('clips.txt'):
            os.remove('clips.txt')
        for clip in clips:
            if os.path.exists(clip):
                os.remove(clip)

def extract_date_from_filename(filename):
    """Extract date from filename with format YYYYMMDDHHMMSS_*."""
    try:
        # Get just the filename without path
        basename = os.path.basename(filename)
        
        # Extract the date part (first 8 characters should be YYYYMMDD)
        if len(basename) >= 8 and basename[:8].isdigit():
            date_str = basename[:8]  # YYYYMMDD
            return datetime.strptime(date_str, '%Y%m%d').date()
        else:
            return None
    except ValueError:
        return None

def filter_files_by_date_range(files, start_date=None, end_date=None):
    """Filter files based on date range extracted from filenames."""
    filtered_files = []
    
    for file_path in files:
        file_date = extract_date_from_filename(file_path)
        
        if file_date is None:
            # If we can't extract date, include the file (preserve old behavior)
            print(f"Warning: Could not extract date from {os.path.basename(file_path)}, including in selection")
            filtered_files.append(file_path)
            continue
        
        # Check if file date is within the specified range
        include_file = True
        
        if start_date and file_date < start_date:
            include_file = False
        
        if end_date and file_date > end_date:
            include_file = False
        
        if include_file:
            filtered_files.append(file_path)
    
    return filtered_files

def parse_date_input(date_str):
    """Parse date input in various formats (YYYY-MM-DD, YYYY-MM, YYYYMMDD)."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    try:
        # Try YYYY-MM-DD format
        if len(date_str) == 10 and date_str.count('-') == 2:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Try YYYY-MM format (for month-based filtering)
        elif len(date_str) == 7 and date_str.count('-') == 1:
            return datetime.strptime(date_str, '%Y-%m').date()
        
        # Try YYYYMMDD format
        elif len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d').date()
        
        # Try YYYYMM format
        elif len(date_str) == 6 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m').date()
        
        else:
            raise ValueError("Unsupported date format")
    
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD, YYYY-MM, YYYYMMDD, or YYYYMM. Error: {e}")

def main(input_dir, target_duration, output_filename, start_date=None, end_date=None):
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Get list of MP4 files
    mp4_files = get_mp4_files(input_dir)
    print(f"\nFound {len(mp4_files)} MP4 files in {input_dir}")
    
    # Filter files by date range if specified
    if start_date or end_date:
        print(f"Filtering files by date range...")
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")
        
        mp4_files = filter_files_by_date_range(mp4_files, start_date, end_date)
        print(f"After date filtering: {len(mp4_files)} files remain")
        
        if not mp4_files:
            raise ValueError("No files match the specified date range")
    
    # Estimate how many clips are needed to reach the target duration
    avg_clip_duration = (CLIP_DURATION_RANGE[0] + CLIP_DURATION_RANGE[1]) / 2
    estimated_clips_needed = int(target_duration / avg_clip_duration) + 1
    
    # Randomly select files (ensure we don't select more than available)
    num_files_to_select = min(estimated_clips_needed, len(mp4_files))
    selected_files = random.sample(mp4_files, num_files_to_select)
    
    # Extract random clips from selected files with a progress bar
    clips = []
    total_duration = 0
    skipped_count = 0
    print(f"Attempting to extract clips from {len(selected_files)} videos...")
    
    for video_path in tqdm(selected_files, desc="Processing videos"):
        clip = get_random_clip(video_path, CLIP_DURATION_RANGE)
        if clip:
            clips.append(clip)
            clip_duration = get_video_duration(clip)
            if clip_duration:
                total_duration += clip_duration
                print(f"Added clip: {clip} (duration: {clip_duration:.1f}s)")
        else:
            skipped_count += 1
        
        # Stop adding clips if we've exceeded the target duration
        if total_duration >= target_duration:
            break
    
    print(f"\nProcessing complete:")
    print(f"- Successfully created {len(clips)} clips")
    print(f"- Skipped {skipped_count} videos")
    print(f"- Total duration: {total_duration:.1f}s (target: {target_duration}s)")
    
    if not clips:
        raise ValueError("No valid clips were generated. Check your input videos.")
    
    # Compile the clips into a single video
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    compile_clips(clips, target_duration, output_path)

def parse_arguments():
    """Parse command-line arguments and prompt for missing values."""
    parser = argparse.ArgumentParser(description="Compile random clips from MP4 files into a single video.")
    parser.add_argument(
        "--duration", 
        type=float,
        help="Target duration of the final video in seconds"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output filename for the compiled video"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Input directory containing MP4 files"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for filtering files (formats: YYYY-MM-DD, YYYY-MM, YYYYMMDD, YYYYMM)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for filtering files (formats: YYYY-MM-DD, YYYY-MM, YYYYMMDD, YYYYMM)"
    )
    parser.add_argument(
        "--month",
        type=str,
        help="Filter for specific month (format: YYYY-MM or YYYYMM). Overrides start-date and end-date."
    )
    
    args = parser.parse_args()
    
    # Handle month filtering (convenience option)
    if args.month:
        try:
            month_date = parse_date_input(args.month)
            # Set start date to first day of month
            args.start_date = month_date.replace(day=1).strftime('%Y-%m-%d')
            # Set end date to last day of month
            if month_date.month == 12:
                next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)
            last_day = (next_month - timedelta(days=1))
            args.end_date = last_day.strftime('%Y-%m-%d')
            print(f"Month filter: {args.month} -> {args.start_date} to {args.end_date}")
        except ValueError as e:
            print(f"Invalid month format: {e}")
            exit(1)
    
    # Parse date arguments
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = parse_date_input(args.start_date)
        except ValueError as e:
            print(f"Invalid start date: {e}")
            exit(1)
    
    if args.end_date:
        try:
            end_date = parse_date_input(args.end_date)
        except ValueError as e:
            print(f"Invalid end date: {e}")
            exit(1)
    
    # Prompt for missing values
    if args.input_dir is None:
        args.input_dir = get_user_input(
            "Enter the input directory path",
            default=INPUT_DIR,
            validator=validate_directory
        )
    
    if args.duration is None:
        args.duration = get_user_input(
            "Enter the target duration in seconds",
            default="30",
            validator=validate_duration
        )
    
    if args.output is None:
        args.output = get_user_input(
            "Enter the output filename",
            default=OUTPUT_FILENAME
        )
    
    # Ensure output filename has .mp4 extension
    if not args.output.lower().endswith('.mp4'):
        args.output += '.mp4'
    
    # Store parsed dates in args for easier access
    args.start_date_parsed = start_date
    args.end_date_parsed = end_date
    
    return args

if __name__ == "__main__":
    try:
        # Parse command-line arguments and get user input
        args = parse_arguments()
        
        print(f"\nUsing the following settings:")
        print(f"Input directory: {args.input_dir}")
        print(f"Target duration: {args.duration} seconds")
        print(f"Output filename: {args.output}")
        if args.start_date_parsed:
            print(f"Start date: {args.start_date_parsed}")
        if args.end_date_parsed:
            print(f"End date: {args.end_date_parsed}")
        print()
        
        main(args.input_dir, args.duration, args.output, args.start_date_parsed, args.end_date_parsed)
    except Exception as e:
        print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")