# tasks/scheduler.py
# 实现一个简单的任务队列（例如 Python 的 queue.Queue）。
# 提供添加任务和手动触发执行的接口。

import queue
import threading # For a simple background worker, if desired
import time
from typing import Callable, Any, List, Tuple, Dict

# Define a type for a task. A task could be a function and its arguments.
# Using Callable for the function part, and Tuple for args, Dict for kwargs.
Task = Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any]]

class SimpleTaskScheduler:
    def __init__(self):
        self.task_queue: queue.Queue[Task] = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_worker = threading.Event()
        self.results = [] # To store results or statuses of executed tasks, if needed
        print("SimpleTaskScheduler initialized.")

    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """
        Adds a task (a function and its arguments) to the queue.
        Args:
            func (Callable): The function to be executed.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        """
        task: Task = (func, args, kwargs)
        self.task_queue.put(task)
        print(f"Task '{func.__name__}' added to the queue. Queue size: {self.task_queue.qsize()}")

    def _process_task(self, task: Task) -> None:
        """
        Processes a single task from the queue.
        """
        func, args, kwargs = task
        try:
            print(f"Executing task: {func.__name__} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            print(f"Task {func.__name__} completed. Result: {result}")
            self.results.append({'task': func.__name__, 'status': 'success', 'result': result})
        except Exception as e:
            print(f"Error executing task {func.__name__}: {e}")
            self.results.append({'task': func.__name__, 'status': 'failure', 'error': str(e)})

    def run_next_task(self) -> None:
        """
        Manually triggers the execution of the next task in the queue.
        This runs in the current thread.
        """
        if self.task_queue.empty():
            print("Task queue is empty. No task to run.")
            return
        
        try:
            task = self.task_queue.get_nowait() # Get task without blocking
            self._process_task(task)
            self.task_queue.task_done() # Signal that the task is done
        except queue.Empty:
            print("Task queue is empty (race condition or already processed).")
        except Exception as e:
            print(f"An unexpected error occurred in run_next_task: {e}")

    def run_all_tasks_sequentially(self) -> None:
        """
        Manually triggers the execution of all tasks currently in the queue, one by one.
        This runs in the current thread.
        """
        print(f"Starting to run all {self.task_queue.qsize()} tasks sequentially...")
        while not self.task_queue.empty():
            self.run_next_task()
        print("All tasks in the queue have been processed.")

    # --- Optional: Background Worker --- 
    # The following methods implement a simple background worker to process tasks.
    # This is optional based on requirements (e.g., if tasks are long-running and non-blocking execution is desired).

    def _worker(self) -> None:
        """Background worker function to process tasks from the queue."""
        print("Task worker thread started.")
        while not self._stop_worker.is_set():
            try:
                # Wait for a task with a timeout to allow checking _stop_worker
                task = self.task_queue.get(timeout=1)
                self._process_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                # Queue is empty, continue waiting or check stop signal
                continue
            except Exception as e:
                # Log unexpected errors in the worker itself
                print(f"Unexpected error in worker thread: {e}")
        print("Task worker thread stopped.")

    def start_worker(self) -> None:
        """
        Starts a background thread that continuously processes tasks from the queue.
        """
        if self._worker_thread is not None and self._worker_thread.is_alive():
            print("Worker thread is already running.")
            return
        
        self._stop_worker.clear()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        print("Background task worker started.")

    def stop_worker(self, wait_for_completion: bool = True) -> None:
        """
        Stops the background worker thread.
        Args:
            wait_for_completion (bool): If True, waits for the current task to finish 
                                        and the queue to be empty before stopping.
        """
        if self._worker_thread is None or not self._worker_thread.is_alive():
            print("Worker thread is not running.")
            return

        print("Stopping background task worker...")
        if wait_for_completion:
            print("Waiting for all tasks in queue to complete...")
            self.task_queue.join() # Wait for all tasks to be processed
        
        self._stop_worker.set() # Signal the worker to stop
        self._worker_thread.join(timeout=5) # Wait for the thread to terminate

        if self._worker_thread.is_alive():
            print("Worker thread did not stop in time.")
        else:
            print("Background task worker stopped successfully.")
        self._worker_thread = None

# --- Example Usage --- 

def example_task_1(message: str):
    print(f"Example Task 1 executing with message: {message}")
    time.sleep(1)
    return f"Task 1 said: {message}"

def example_task_2(number1: int, number2: int, operation: str = "add"):
    print(f"Example Task 2 executing: {number1} {operation} {number2}")
    time.sleep(0.5)
    if operation == "add":
        return number1 + number2
    elif operation == "multiply":
        return number1 * number2
    return "Unknown operation"

if __name__ == '__main__':
    scheduler = SimpleTaskScheduler()

    print("\n--- Testing Manual Task Execution ---")
    scheduler.add_task(example_task_1, message="Hello from manual run!")
    scheduler.add_task(example_task_2, number1=5, number2=10, operation="multiply")
    scheduler.add_task(example_task_1, "Another message") # Using positional arg for 'message'
    
    print("\nRunning next task manually:")
    scheduler.run_next_task()
    print(f"Queue size after one manual run: {scheduler.task_queue.qsize()}")

    print("\nRunning all remaining tasks sequentially (manually):")
    scheduler.run_all_tasks_sequentially()
    print(f"Queue size after all manual runs: {scheduler.task_queue.qsize()}")
    print(f"Results from manual execution: {scheduler.results}")
    scheduler.results.clear() # Clear results for next test

    print("\n--- Testing Background Worker Execution ---")
    scheduler.add_task(example_task_1, message="Hello from worker!")
    scheduler.add_task(example_task_2, 7, 3, operation="add")
    scheduler.add_task(example_task_1, message="Worker processing this.")
    scheduler.add_task(example_task_2, number1=4, number2=4, operation="multiply")

    scheduler.start_worker()
    print("Worker started. Tasks will be processed in the background.")
    print("Main thread can do other things here or wait.")
    
    # Wait for a bit to let the worker process tasks, or use stop_worker(wait_for_completion=True)
    # For this demo, let's just wait for queue to empty via task_queue.join()
    # which is implicitly called by stop_worker(wait_for_completion=True)
    
    # Adding more tasks while worker is running
    time.sleep(1) # Simulate some delay or other work
    print("\nAdding more tasks while worker is active...")
    scheduler.add_task(example_task_1, "Late addition task!")

    # Stop the worker and wait for all tasks to complete
    scheduler.stop_worker(wait_for_completion=True)
    
    print(f"\nResults from worker execution: {scheduler.results}")
    print("SimpleTaskScheduler demo finished.")