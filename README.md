# NetComs_ChatApp

We are utilizing the PYQT for Python to create a chat application GUI.

In terms of the logic, we are using the socket library to create a client-server connection. The client will be able to send messages to the server and the server will be able to send messages to the client.

The server will be able to send messages to all connected clients. The server will be able to handle multiple clients concurrently.

The server will be able to handle client disconnections and reconnects. The server will be able to handle client connections and disconnections.

PYQT: https://doc.qt.io/qtforpython-6/

Update: Update 1.0. This Application will develop into a much better application in the future. :)

# Performance Metrics Analysis Tool

This tool demonstrates and compares different computing approaches: Sequential, Parallel, and Distributed processing. It was developed to analyze and optimize performance in a chat application context.

## Evolution of the Implementation

### 1. Sequential Processing (Initial Implementation)
- Basic implementation where tasks are executed one after another
- Simple and straightforward but not optimal for performance
- Each task must complete before the next one starts
- Good for understanding baseline performance

### 2. Parallel Processing (First Improvement)
- Implemented using Python's `concurrent.futures.ThreadPoolExecutor`
- Utilizes multiple threads to execute tasks concurrently
- Key improvements:
  - Tasks run simultaneously within the same process
  - Better utilization of CPU cores
  - Reduced total execution time
  - Particularly effective for I/O-bound tasks

### 3. Distributed Processing (Latest Enhancement)
- Implemented using Python's `multiprocessing` module
- Creates separate processes for task execution
- Key features:
  - True parallel execution across CPU cores
  - Process-based task distribution
  - Shared resource management using `Manager`
  - Queue-based task distribution system

## Performance Improvements

### Sequential vs Parallel
- Parallel processing shows significant speedup (2.13x in our tests)
- Particularly effective for:
  - I/O-bound tasks (network operations, file I/O)
  - Independent computational tasks
  - Tasks that can be executed concurrently

### Parallel vs Distributed
- Distributed processing currently shows slower performance (0.09x speedup)
- This is due to:
  - Process creation overhead
  - Inter-process communication costs
  - Task distribution overhead
- However, distributed processing is better suited for:
  - CPU-intensive tasks
  - Tasks requiring true parallel execution
  - Scenarios where memory isolation is important

## Implementation Details

### Task Types
1. **CPU-bound tasks**
   - Matrix multiplication operations
   - Heavy computational work
   - Size parameter controls complexity

2. **I/O-bound tasks**
   - Simulated network/file operations
   - Uses sleep to simulate I/O delays
   - Duration parameter controls delay

3. **Complex tasks**
   - Combination of CPU and memory operations
   - Multiple iterations of matrix operations
   - Configurable size and iterations

### Performance Metrics
- Execution time measurement
- Statistical analysis (mean, median, standard deviation)
- Speedup calculations
- Visual performance comparison using matplotlib

## Usage Example

```python
# Create tasks with specific parameters
tasks = [
    (cpu_bound_task, {'size': 800}),
    (cpu_bound_task, {'size': 800}),
    (complex_task, {'size': 500, 'iterations': 10}),
    (complex_task, {'size': 500, 'iterations': 10}),
    (io_bound_task, {'duration': 0.1})
]

# Initialize and run benchmark
metrics = PerformanceMetrics()
metrics.run_benchmark(tasks, iterations=5)

# Generate report and plot
metrics.print_report()
metrics.plot_results()
```

## Future Improvements

1. **Optimize Distributed Processing**
   - Reduce process creation overhead
   - Implement better task distribution strategies
   - Optimize inter-process communication

2. **Enhanced Task Management**
   - Dynamic task scheduling
   - Load balancing across processes
   - Better resource utilization

3. **Additional Metrics**
   - Memory usage tracking
   - CPU utilization monitoring
   - Network I/O metrics

4. **Real-world Integration**
   - Integration with actual chat application
   - Real-time performance monitoring
   - Adaptive processing strategy selection

## Requirements

- Python 3.11+
- numpy
- matplotlib
- concurrent.futures
- multiprocessing

## Installation

```bash
pip install numpy matplotlib
```

## Running the Tests

```bash
python performance_metrics.py
```

This will:
1. Run the benchmark tests
2. Generate a performance report
3. Create a visualization of the results
