#!/usr/bin/env python
import argparse
import os
import re
import subprocess
import sys
import time
import json

def parse_size(size_str):
    """Parse size string like '10m', '1g' to bytes."""
    size_str = size_str.lower()
    if size_str.endswith('k'):
        return int(float(size_str[:-1]) * 1024)
    elif size_str.endswith('m'):
        return int(float(size_str[:-1]) * 1024 * 1024)
    elif size_str.endswith('g'):
        return int(float(size_str[:-1]) * 1024 * 1024 * 1024)
    else:
        try:
            return int(size_str)
        except ValueError:
            raise ValueError(f"Invalid size format: {size_str}")


def parse_time(time_str):
    """Parse time string like 'm:s.f' or seconds."""
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    else:
        return float(time_str)


def format_size(size_bytes):
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"


def get_video_info(filename):
    """獲取影片資訊使用 ffprobe。"""
    # 調用 ffprobe 獲取影片資訊，明確指定串流索引
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",  # 選擇第一個影片串流
        "-show_entries", "stream=width,height,bit_rate,duration",
        "-show_entries", "format=duration,size",
        "-of", "json",  # 使用 JSON 輸出格式更可靠
        filename
    ]
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        data = json.loads(output)
        
        # 從 JSON 中提取資訊
        stream_info = data.get('streams', [{}])[0]
        format_info = data.get('format', {})
        
        # 獲取寬度和高度
        width = int(stream_info.get('width', 0))
        height = int(stream_info.get('height', 0))
        
        # 獲取位元速率，優先從串流中獲取，如果沒有則從格式資訊計算
        bit_rate = None
        if 'bit_rate' in stream_info and stream_info['bit_rate'] not in (None, 'N/A'):
            bit_rate = int(stream_info['bit_rate'])
        elif 'bit_rate' in format_info and format_info['bit_rate'] not in (None, 'N/A'):
            bit_rate = int(format_info['bit_rate'])
        
        # 獲取持續時間
        duration = None
        if 'duration' in stream_info:
            duration = float(stream_info['duration'])
        elif 'duration' in format_info:
            duration = float(format_info['duration'])
        
        # 獲取檔案大小
        file_size = int(format_info.get('size', 0))
        
        # 如果位元速率沒有從 ffprobe 獲取，則進行計算
        if bit_rate is None and duration > 0:
            bit_rate = int((file_size * 8) / duration)
        
        return {
            'duration': duration,
            'size': file_size,
            'width': width,
            'height': height,
            'bit_rate': bit_rate
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError, IndexError, KeyError) as e:
        print(f"分析影片時發生錯誤: {e}")
        sys.exit(1)


def calculate_new_parameters(video_info, target_size, start_time=None, end_time=None):
    """Calculate new resolution and bitrate based on target size."""
    # Calculate actual video duration
    if start_time is None:
        start_time = 0
    if end_time is None:
        end_time = video_info['duration']
    
    output_duration = end_time - start_time
    
    # Calculate target bitrate (bits per second)
    # Target size is 97.5% to account for container overhead
    target_bitrate = int((target_size * 8 * 0.975) / output_duration)
    
    # Original aspect ratio
    aspect_ratio = video_info['width'] / video_info['height']
    
    # Calculate new resolution based on bitrate reduction
    bitrate_ratio = (target_bitrate / video_info['bit_rate'])
    
    # Resolution scaling factor (square root of bitrate ratio)
    scale_factor = max(min(bitrate_ratio ** 0.5, 1.0), 0.2)  # Limit scaling
    
    # Calculate new dimensions (must be even)
    new_width = 2 * round((video_info['width'] * scale_factor) / 2)
    new_height = 2 * round((new_width / aspect_ratio) / 2)
    
    # Ensure minimum resolution
    new_width = max(new_width, 320)
    new_height = max(new_height, 240)
    
    # Adjust bitrate if resolution couldn't be reduced enough
    adjusted_bitrate = target_bitrate
    
    return {
        'width': int(new_width),
        'height': int(new_height),
        'bit_rate': adjusted_bitrate
    }


def process_video(input_file, target_size, start_time=None, end_time=None, iteration=1, max_iterations=3):
    """Process video to match target size."""
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return None
    
    video_info = get_video_info(input_file)
    
    # Calculate output duration
    if start_time is None:
        start_time = 0
    if end_time is None:
        end_time = video_info['duration']
    
    output_duration = end_time - start_time
    
    # Display original video information
    print(f"\nOriginal Video Information:")
    print(f"Resolution: {video_info['width']}x{video_info['height']}")
    print(f"Bit Rate: {video_info['bit_rate']/1000:.2f} Kbps")
    print(f"Duration: {video_info['duration']:.2f} seconds")
    print(f"File Size: {format_size(video_info['size'])}")
    print(f"Size per second: {format_size(video_info['size']/video_info['duration'])}/s")
    print(f"Size per minute: {format_size(video_info['size']/video_info['duration']*60)}/min")
    
    # Calculate new parameters
    new_params = calculate_new_parameters(video_info, target_size, start_time, end_time)
    
    # Display target information
    print(f"\nTarget Information:")
    print(f"Target Size: {format_size(target_size)}")
    print(f"Target Duration: {output_duration:.2f} seconds")
    print(f"Calculated Resolution: {new_params['width']}x{new_params['height']}")
    print(f"Calculated Bit Rate: {new_params['bit_rate']/1000:.2f} Kbps")
    print(f"Estimated Size per second: {format_size(new_params['bit_rate']/8)}/s")
    print(f"Estimated Size per minute: {format_size(new_params['bit_rate']/8*60)}/min")
    
    # Create output filename
    base_name, ext = os.path.splitext(input_file)
    output_file = f"{base_name}_{new_params['width']}x{new_params['height']}_{int(new_params['bit_rate']/1000)}kbps{ext}"
    
    # Prepare ffmpeg command
    cmd = ["ffmpeg", "-y"]
    
    # Add time parameters if specified
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    
    cmd.extend(["-i", input_file])
    
    if end_time < video_info['duration']:
        cmd.extend(["-t", str(output_duration)])
    
    cmd.extend([
        "-c:v", "libx264",
        "-b:v", f"{new_params['bit_rate']}",
        "-maxrate", f"{int(new_params['bit_rate'] * 1.5)}",
        "-bufsize", f"{int(new_params['bit_rate'] * 3)}",
        "-vf", f"scale={new_params['width']}:{new_params['height']}",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_file
    ])
    
    print(f"\nProcessing video... (Iteration {iteration})")
    # print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        
        # Check resulting file size
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            output_percentage = (output_size / target_size) * 100
            
            print(f"Output file: {output_file}")
            print(f"Output size: {format_size(output_size)} ({output_percentage:.2f}% of target)")
            
            # Check if we need to try again
            if output_percentage > 100:  # Too large
                if iteration < max_iterations:
                    print(f"File is too large. Trying again with more aggressive settings...")
                    # Adjust target size down to compensate
                    adjusted_target = int(target_size * (target_size / output_size) * 0.95)
                    return process_video(input_file, adjusted_target, start_time, end_time, iteration + 1)
                else:
                    print("Max iterations reached. Using best result.")
            elif output_percentage < 95:  # Too small
                if iteration < max_iterations:
                    print(f"File is too small. Trying again with less aggressive settings...")
                    # Adjust target size up to get closer to target
                    adjusted_target = int(target_size * (target_size / output_size) * 1.05)
                    return process_video(input_file, adjusted_target, start_time, end_time, iteration + 1)
                else:
                    print("Max iterations reached. Using best result.")
            
            return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error processing video: {e}")
        return None


def play_video(filename):
    """Play video with system default player."""
    print(f"\nPlaying: {filename}")
    
    if sys.platform == "win32":
        os.startfile(filename)
    elif sys.platform == "darwin":
        subprocess.call(["open", filename])
    else:
        subprocess.call(["xdg-open", filename])


def cleanup_files(successful_file):
    """Clean up intermediate files."""
    base_dir = os.path.dirname(successful_file)
    base_name, ext = os.path.splitext(os.path.basename(successful_file))
    
    # Extract original filename pattern
    original_pattern = re.match(r'^(.+?)_\d+x\d+_\d+kbps', base_name)
    if not original_pattern:
        return
    
    original_name = original_pattern.group(1)
    
    # Find all similar files
    for file in os.listdir(base_dir):
        if file.endswith(ext) and file.startswith(original_name) and file != os.path.basename(successful_file):
            if re.search(r'_\d+x\d+_\d+kbps', file):
                file_path = os.path.join(base_dir, file)
                print(f"Removing: {file}")
                os.remove(file_path)


def main():
    parser = argparse.ArgumentParser(description="Reduce MP4 file size to target size.")
    parser.add_argument("target_size", help="Target file size (e.g. 10m, 1g)")
    parser.add_argument("input_file", help="Input MP4 file")
    parser.add_argument("start_time", nargs="?", help="Start time (m:s.f or seconds)", default=None)
    parser.add_argument("end_time", nargs="?", help="End time (m:s.f or seconds)", default=None)
    
    args = parser.parse_args()
    
    # Parse target size
    try:
        target_size = parse_size(args.target_size)
    except ValueError as e:
        print(e)
        return
    
    # Parse time arguments
    start_time = None
    end_time = None
    
    if args.start_time:
        try:
            start_time = parse_time(args.start_time)
        except ValueError as e:
            print(e)
            return
    
    if args.end_time:
        try:
            end_time = parse_time(args.end_time)
        except ValueError as e:
            print(e)
            return
    
    # Process video
    output_file = process_video(args.input_file, target_size, start_time, end_time)
    
    if output_file and os.path.exists(output_file):
        # Play the output file
        play_video(output_file)
        
        # Wait for video to play and ask about cleanup
        input("\nPress Enter when you're done watching the video...")
        
        choice = input("Do you want to clean up intermediate files? (y/n): ")
        if choice.lower() == 'y':
            cleanup_files(output_file)
            print("Cleanup completed.")


if __name__ == "__main__":
    main()