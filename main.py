import argparse
import json
import os
import time
from datetime import datetime, timedelta
from threading import Thread
import platform
import subprocess
import sys


TASKS_FILE = "tasks.json"

def load_tasks():
    """Load tasks from the JSON file."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    """Save tasks to the JSON file."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(name, due_time, priority="medium"):
    """Add a new task."""
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "name": name,
        "due_time": due_time,
        "priority": priority,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task: {name} (Due: {due_time})")

def list_tasks(show_all=False):
    """List all tasks or only pending ones."""
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return
    
    now = datetime.now()
    pending_tasks = [t for t in tasks if not t["completed"]]
    
    if not show_all and not pending_tasks:
        print("No pending tasks.")
        return
    
    task_list = tasks if show_all else pending_tasks
    
    print("\nTask List:")
    print("-" * 50)
    for task in task_list:
        status = "Completed" if task["completed"] else "Pending"
        due_time = datetime.fromisoformat(task["due_time"])
        time_left = due_time - now
        days_left = time_left.days
        hours_left, remainder = divmod(time_left.seconds, 3600)
        minutes_left, _ = divmod(remainder, 60)
        
        print(f"ID: {task['id']}")
        print(f"Name: {task['name']}")
        print(f"Priority: {task['priority']}")
        print(f"Status: {status}")
        print(f"Due: {due_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if not task["completed"]:
            print(f"Time left: {days_left}d {hours_left}h {minutes_left}m")
        print("-" * 50)

def complete_task(task_id):
    """Mark a task as completed."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            save_tasks(tasks)
            print(f"Task {task_id} marked as completed.")
            return
    print(f"Task with ID {task_id} not found.")

def delete_task(task_id):
    """Delete a task."""
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Task {task_id} deleted.")

def notify(title, message):
    """Show a system notification."""
    if platform.system() == "Darwin":  
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
    elif platform.system() == "Linux":
        try:
            subprocess.run(["notify-send", title, message])
        except FileNotFoundError:
            print(f"ALERT: {title} - {message}")
    else:  
        print(f"ALERT: {title} - {message}")

def monitor_tasks():
    """Monitor tasks and trigger alerts when due."""
    while True:
        tasks = load_tasks()
        now = datetime.now()
        
        for task in tasks:
            if not task["completed"]:
                due_time = datetime.fromisoformat(task["due_time"])
                if now >= due_time:
                    notify("Task Due", f"'{task['name']}' is due now!")
        
        time.sleep(60)  

def parse_due_time(due_str):
    """Parse due time string into datetime object."""
    try:
        
        return datetime.strptime(due_str, "%Y-%m-%d %H:%M").isoformat()
    except ValueError:
        pass
    
    try:
        
        if due_str.startswith("in "):
            parts = due_str[3:].split()
            if len(parts) == 2:
                amount = int(parts[0])
                unit = parts[1].rstrip('s')  
                
                if unit == "minute":
                    delta = timedelta(minutes=amount)
                elif unit == "hour":
                    delta = timedelta(hours=amount)
                elif unit == "day":
                    delta = timedelta(days=amount)
                elif unit == "week":
                    delta = timedelta(weeks=amount)
                else:
                    raise ValueError("Unknown time unit")
                
                return (datetime.now() + delta).isoformat()
    except Exception:
        pass
    
    raise ValueError("Invalid due time format. Use 'YYYY-MM-DD HH:MM' or 'in X hours/minutes/days/weeks'")

def print_help():
    """Print help instructions."""
    print("\nTask Reminder CLI - Usage Instructions")
    print("------------------------------------")
    print("1. Add a task:")
    print("   python main.py add \"Task name\" \"due_time\" [--priority low|medium|high]")
    print("   Example: python main.py add \"Buy milk\" \"in 2 hours\" --priority high")
    print("\n2. List tasks:")
    print("   python main.py list [-a|--all]")
    print("   Example: python main.py list --all")
    print("\n3. Complete a task:")
    print("   python main.py complete task_id")
    print("   Example: python main.py complete 1")
    print("\n4. Delete a task:")
    print("   python main.py delete task_id")
    print("   Example: python main.py delete 1")
    print("\n5. Monitor tasks (alerts):")
    print("   python main.py monitor")
    print("\nNote: For relative times, use formats like:")
    print("   \"in 30 minutes\", \"in 2 hours\", \"in 1 day\", \"in 2 weeks\"")

def main():
    """Main CLI interface."""
    if len(sys.argv) == 1:
        print_help()
        return
    
    parser = argparse.ArgumentParser(description="Task Reminder CLI with Alerts", add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add task command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("name", help="Name of the task")
    add_parser.add_argument("due_time", help="Due time (format: 'YYYY-MM-DD HH:MM' or 'in 2 hours')")
    add_parser.add_argument("-p", "--priority", choices=["low", "medium", "high"], 
                          default="medium", help="Task priority")

    # List tasks command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("-a", "--all", action="store_true", 
                           help="Show all tasks (including completed)")

    # Complete task command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument("task_id", type=int, help="ID of the task to complete")

    # Delete task command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="ID of the task to delete")

    # Monitor command 
    subparsers.add_parser("monitor", help="Start monitoring tasks for alerts (runs in background)")

    # Help command
    subparsers.add_parser("help", help="Show usage instructions")

    try:
        args = parser.parse_args()
        
        if args.command == "help":
            print_help()
        elif args.command == "add":
            try:
                due_time = parse_due_time(args.due_time)
                add_task(args.name, due_time, args.priority)
            except ValueError as e:
                print(f"Error: {e}")
        elif args.command == "list":
            list_tasks(args.all)
        elif args.command == "complete":
            complete_task(args.task_id)
        elif args.command == "delete":
            delete_task(args.task_id)
        elif args.command == "monitor":
            print("Starting task monitor. Press Ctrl+C to stop.")
            try:
                monitor_tasks()
            except KeyboardInterrupt:
                print("\nTask monitor stopped.")
    except Exception as e:
        print(f"Error: {e}")
        print_help()

if __name__ == "__main__":
   
    if len(sys.argv) > 1 and sys.argv[1] != "monitor":
        monitor_thread = Thread(target=monitor_tasks, daemon=True)
        monitor_thread.start()
    
    main()
