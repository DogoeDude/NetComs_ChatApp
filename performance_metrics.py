import time
import threading
import queue
import statistics
from typing import List, Callable, Dict, Any, Tuple
import matplotlib.pyplot as plt
import numpy as np
import concurrent.futures
import multiprocessing
from multiprocessing import Pool, Process, Manager
import os
from functools import partial
import socket
import json
import pickle

class PerformanceMetrics:
    def __init__(self):
        self.results = {
            'sequential': [],
            'parallel': [],
            'distributed': []
        }
        self.num_cores = multiprocessing.cpu_count()
        self.server_host = 'localhost'
        self.server_port = 8000
        
    def measure_execution_time(self, func: Callable, *args, **kwargs) -> float:
        """Measure the execution time of a function."""
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time

    def sequential_processing(self, tasks: List[Tuple[Callable, dict]], *args, **kwargs) -> float:
        """Execute tasks sequentially and return total execution time."""
        start_time = time.time()
        for task, task_kwargs in tasks:
            task(**task_kwargs)
        end_time = time.time()
        return end_time - start_time

    def parallel_processing(self, tasks: List[Tuple[Callable, dict]], *args, **kwargs) -> float:
        """Execute tasks in parallel using ThreadPoolExecutor for better performance."""
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_cores) as executor:
            futures = [executor.submit(task, **task_kwargs) for task, task_kwargs in tasks]
            concurrent.futures.wait(futures)
        end_time = time.time()
        return end_time - start_time

    def distributed_processing(self, tasks: List[Tuple[Callable, dict]], *args, **kwargs) -> float:
        """Execute tasks using distributed computing pattern with multiple processes."""
        start_time = time.time()
        
        with Manager() as manager:
            task_queue = manager.Queue()
            result_queue = manager.Queue()
            
            for task, task_kwargs in tasks:
                task_queue.put((task.__name__, task_kwargs))
            
            processes = []
            for _ in range(self.num_cores):
                p = Process(target=self._distributed_worker, 
                          args=(task_queue, result_queue))
                processes.append(p)
                p.start()
            
            for p in processes:
                p.join()
            
            while not result_queue.empty():
                result_queue.get()
                
        end_time = time.time()
        return end_time - start_time

    def _distributed_worker(self, task_queue: multiprocessing.Queue, 
                          result_queue: multiprocessing.Queue):
        """Worker process for distributed computing."""
        while not task_queue.empty():
            try:
                task_name, task_kwargs = task_queue.get_nowait()
                task = globals()[task_name]
                result = task(**task_kwargs)
                result_queue.put(result)
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error in worker: {e}")
                break

    def run_benchmark(self, tasks: List[Tuple[Callable, dict]], iterations: int = 5):
        """Run benchmark tests comparing sequential, parallel, and distributed processing."""
        for _ in range(iterations):
            seq_time = self.sequential_processing(tasks)
            self.results['sequential'].append(seq_time)
            
            par_time = self.parallel_processing(tasks)
            self.results['parallel'].append(par_time)
            
            dist_time = self.distributed_processing(tasks)
            self.results['distributed'].append(dist_time)

    def calculate_statistics(self) -> dict:
        """Calculate statistical metrics for the benchmark results."""
        stats = {}
        for mode in ['sequential', 'parallel', 'distributed']:
            times = self.results[mode]
            stats[mode] = {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times)
            }
        return stats

    def plot_results(self, save_path: str = 'performance_comparison.png'):
        """Plot the benchmark results using matplotlib."""
        plt.figure(figsize=(12, 6))
        
        x = np.arange(len(self.results['sequential']))
        width = 0.25
        
        plt.bar(x - width, self.results['sequential'], width, label='Sequential')
        plt.bar(x, self.results['parallel'], width, label='Parallel')
        plt.bar(x + width, self.results['distributed'], width, label='Distributed')
        
        plt.xlabel('Iteration')
        plt.ylabel('Execution Time (seconds)')
        plt.title('Sequential vs Parallel vs Distributed Processing Performance')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(save_path)
        plt.close()

    def print_report(self):
        """Print a detailed performance report."""
        stats = self.calculate_statistics()
        
        print("\n=== Performance Benchmark Report ===")
        print(f"\nNumber of CPU Cores: {self.num_cores}")
        
        for mode in ['sequential', 'parallel', 'distributed']:
            print(f"\n{mode.title()} Processing:")
            for metric, value in stats[mode].items():
                print(f"{metric.replace('_', ' ').title()}: {value:.4f} seconds")
        
        par_speedup = stats['sequential']['mean'] / stats['parallel']['mean']
        dist_speedup = stats['sequential']['mean'] / stats['distributed']['mean']
        print(f"\nParallel Speedup: {par_speedup:.2f}x")
        print(f"Distributed Speedup: {dist_speedup:.2f}x")

# Real-world chat application tasks
def send_message_to_server(message: str, host: str = 'localhost', port: int = 8000):
    """Send a message to the chat server."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(json.dumps({'type': 'message', 'content': message}).encode())
            response = s.recv(1024)
            return response.decode()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def receive_messages(host: str = 'localhost', port: int = 8000, duration: float = 1.0):
    """Simulate receiving messages from the server."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.settimeout(duration)
            messages = []
            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    data = s.recv(1024)
                    if data:
                        messages.append(data.decode())
                except socket.timeout:
                    break
            return messages
    except Exception as e:
        print(f"Error receiving messages: {e}")
        return []

def broadcast_message(message: str, num_clients: int = 5):
    """Simulate broadcasting a message to multiple clients."""
    results = []
    for _ in range(num_clients):
        result = send_message_to_server(message)
        if result:
            results.append(result)
    return results

# Example usage
if __name__ == "__main__":
    # Create real-world chat application tasks
    tasks = [
        (send_message_to_server, {'message': 'Hello, World!', 'host': 'localhost', 'port': 8000}),
        (send_message_to_server, {'message': 'How are you?', 'host': 'localhost', 'port': 8000}),
        (receive_messages, {'host': 'localhost', 'port': 8000, 'duration': 1.0}),
        (broadcast_message, {'message': 'Broadcast test', 'num_clients': 5}),
        (receive_messages, {'host': 'localhost', 'port': 8000, 'duration': 0.5})
    ]
    
    # Initialize and run benchmark
    metrics = PerformanceMetrics()
    
    print("Starting real-world chat application performance test...")
    print("Make sure the chat server is running on localhost:8000")
    
    try:
        metrics.run_benchmark(tasks, iterations=5)
        metrics.print_report()
        metrics.plot_results()
    except Exception as e:
        print(f"Error during benchmark: {e}")
        print("Please ensure the chat server is running before running the performance test.") 