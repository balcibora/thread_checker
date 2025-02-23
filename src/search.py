import requests
import base64
import re
import os
from typing import Tuple, List
from thread_flags import find_thread_flags
directory = ""

def get_files_from_directory(directory, extensions={".py", ".cpp", ".h", ".r", ".java", ".js", ".c", ".hpp"}):
    """Recursively find all source code files in a directory."""
    source_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                source_files.append(os.path.join(root, file))
    return source_files

def search_in_file(file_path):
    """Reads a file and searches for threading-related patterns."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, {}

    keyword_matches = find_thread_flags(file_content)
    return bool(keyword_matches), keyword_matches

# Function to analyze file content for threading support & line numbers
def find_thread_flags(text: str) -> dict:
    
    thread_keywords = {
        # CLI flags
        '-t', '--threads', '-threads', '--thread', '-thread', '--nthreads', '-nthreads', '--num-threads', '-n',
        '--cores', '-cores', '--num-cores', '-p', '--processes', '-processes', 
        '--parallel', '-parallel', '--jobs', '-j', '--workers', '-w', '--cpus', '-cpus',
        '--threads-per-process', '--tpp',
        
        # Common threading library imports/includes
        'import threading', 'import multiprocessing', 'import concurrent.futures',
        '#include <thread>', '#include <pthread.h>', 'use threads', 'require threads', 'import java.util.concurrent',
        'from concurrent.futures', 'from multiprocessing', 'from threading',
        
        # Common threading classes/functions
        'Thread(', 'threading.Thread', 'ThreadPoolExecutor', 'ProcessPoolExecutor', 'multiprocessing.Pool', 'Pool(',
        'pthread_create', 'pthread_join', 'std::thread', 'boost::thread', 'java.util.concurrent.Thread', 'System.Threading',
        'goroutine', 'go func', 'async/await', 'Promise.all', 'spawn_link',  # Erlang/Elixir
        'GenServer',   # Erlang/Elixir
        'parallel do', # Ruby
        'Parallel.map', # Ruby
        'OpenMP', '#pragma omp parallel',
        '@parallel',  # Julia
        'Threads.@threads', # Julia
        
        # R threading
        'library(parallel)', 'library(foreach)', 'library(doParallel)', 'library(future)',
        'mclapply', 'makeCluster', 'registerDoParallel', 'plan(multisession)', 'foreach', '%dopar%', 'future_map', 'future_apply',
        
        # Perl threading
        'use threads',
        'use Thread',
        'threads->create',
        'threads->new',
        'fork()',
        'Thread::Queue',
        'Thread::Pool',
        'Parallel::ForkManager',
        'MCE::Map',
        'MCE::Loop',
    }

    thread_patterns = {
        # CLI patterns
        r'-t\s*\d+',
        r'--threads\s*\d+',
        r'--thread\s*\d+',
        r'-n\s*\d+',
        r'--num-threads\s*\d+',
        r'--cores\s*\d+',
        r'-p\s*\d+',
        r'--processes\s*\d+',
        r'--parallel\s*\d*',
        r'-j\s*\d+',
        r'--jobs\s*\d+',
        r'--workers\s*\d+',
        r'--cpus\s*\d+',
        r'--threads-per-process\s*\d+',
        
        # Code patterns
        r'new\s+Thread\(',
        r'ThreadPool\(\d*\)',
        r'ProcessPool\(\d*\)',
        r'num_threads\s*=\s*\d+',
        r'max_workers\s*=\s*\d+',
        r'pool\s*=\s*Pool\(\d*\)',
        r'#pragma\s+omp\s+parallel(\s+for)?',
        r'goroutines?\s*:\s*\d+',
        
        # R patterns
        r'mclapply\s*\([^)]*mc\.cores\s*=\s*\d+',
        r'makeCluster\s*\(\s*\d+\s*\)',
        r'plan\s*\(\s*multisession\s*,\s*workers\s*=\s*\d+\s*\)',
        r'registerDoParallel\s*\(\s*\d+\s*\)',
        r'future::plan\s*\([^)]*workers\s*=\s*\d+',
        
        # Perl patterns
        r'threads->create\s*\([^)]*\)',
        r'threads->new\s*\([^)]*\)',
        r'MCE::Map->new\s*\([^)]*chunk_size\s*=>\s*\d+',
        r'Parallel::ForkManager->new\s*\(\s*\d+\s*\)',
        r'MCE::Loop->new\s*\([^)]*max_workers\s*=>\s*\d+',
    }

    threading_indicators = {
        'parallel', 'multithread', 'multi-thread', 'multi thread', 
        'concurrent', 'cpu cores', 'processor cores',
        'parallel processing', 'thread pool', 'threadpool',
        'multithreading', 'parallelization', 'concurrent processing',
        'distributed computing', 'parallel computation',
        'asynchronous', 'async/await', 'coroutine',
        'worker pool', 'task queue', 'job queue',
        'concurrent execution', 'parallel execution',
        'threaded', 'multi-core', 'multicore',
    }

    found_flags = {}

    # Search for exact keyword matches and store line numbers
    for i, line in enumerate(text.splitlines(), start=1):
        for keyword in thread_keywords:
            if keyword in line:
                if keyword not in found_flags:
                    found_flags[keyword] = []
                found_flags[keyword].append(i)

        for pattern in thread_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if match not in found_flags:
                    found_flags[match] = []
                found_flags[match].append(i)

        for indicator in threading_indicators:
            if indicator in line:
                if indicator not in found_flags:
                    found_flags[indicator] = []
                found_flags[indicator].append(i)

    return found_flags


# --- Main Execution --- #

# directory = input("Enter the directory containing source code: ").strip()
directory = os.path.abspath("./test")

# if not os.path.isdir(directory):
#     print("Invalid directory. Please enter a valid directory path.")
#     exit()

print("\nScanning directory for source files...\n")
source_files = get_files_from_directory(directory)

if not source_files:
    print("No source files found in the given directory.")
    exit()

print(f"Found {len(source_files)} source files. Analyzing for threading-related patterns...\n")

threading_results = {}

for file_path in source_files:
    has_threading, keyword_matches = search_in_file(file_path)
    
    if has_threading:
        threading_results[file_path] = keyword_matches
    else:
        print(f"No threading patterns found in {file_path}")

# Save results to a file
folder_name = os.path.basename(directory)
output_file = "search_results_" + folder_name + ".txt"
with open(output_file, "w") as output:
    if threading_results:
        # output.write("Files containing threading-related flags:\n\n")
        for file, matches in threading_results.items():
            output.write(f"{file}:\n")
            for keyword, lines in matches.items():
                line_numbers = ", ".join(map(str, lines))
                output.write(f"  - {keyword}: Found on line(s) {line_numbers}\n")
            output.write("\n")
    else:
        output.write("No threading-related flags found in the source files.\n")

print(f"\nSearch completed! Results saved in {output_file}")