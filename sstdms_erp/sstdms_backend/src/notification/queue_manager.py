# queue_manager.py

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class NotificationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class NotificationTask:
    """Represents a notification task in the queue."""
    id: str
    user_id: int
    notification_type: str
    title: str
    message: str
    data: Dict[str, Any]
    priority: NotificationPriority
    status: NotificationStatus
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.scheduled_at:
            data['scheduled_at'] = self.scheduled_at.isoformat()
        return data

class NotificationQueueManager:
    """Manages notification queues with priority, retry logic, and scheduling."""
    
    def __init__(self, max_workers: int = 5, retry_delay: int = 60):
        self.queues: Dict[NotificationPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in NotificationPriority
        }
        self.scheduled_tasks: List[NotificationTask] = []
        self.processing_tasks: Dict[str, NotificationTask] = {}
        self.completed_tasks: List[NotificationTask] = []
        self.failed_tasks: List[NotificationTask] = []
        
        self.max_workers = max_workers
        self.retry_delay = retry_delay
        self.workers: List[asyncio.Task] = []
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Notification handlers
        self.handlers: Dict[str, Callable] = {}
        
    def register_handler(self, notification_type: str, handler: Callable):
        """Register a handler for a specific notification type."""
        self.handlers[notification_type] = handler
        logger.info(f"Registered handler for notification type: {notification_type}")
    
    async def add_notification(self, 
                             user_id: int,
                             notification_type: str,
                             title: str,
                             message: str,
                             data: Dict[str, Any] = None,
                             priority: NotificationPriority = NotificationPriority.NORMAL,
                             scheduled_at: Optional[datetime] = None) -> str:
        """Add a notification to the queue."""
        
        task = NotificationTask(
            id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            priority=priority,
            status=NotificationStatus.PENDING,
            created_at=datetime.now(),
            scheduled_at=scheduled_at
        )
        
        if scheduled_at and scheduled_at > datetime.now():
            # Schedule for later
            self.scheduled_tasks.append(task)
            logger.info(f"Notification scheduled: {task.id} for {scheduled_at}")
        else:
            # Add to appropriate priority queue
            await self.queues[priority].put(task)
            logger.info(f"Notification queued: {task.id} with priority {priority.name}")
        
        return task.id
    
    async def process_notification(self, task: NotificationTask) -> bool:
        """Process a single notification task."""
        try:
            task.status = NotificationStatus.PROCESSING
            self.processing_tasks[task.id] = task
            
            logger.info(f"Processing notification: {task.id}")
            
            # Get handler for notification type
            handler = self.handlers.get(task.notification_type)
            if not handler:
                raise Exception(f"No handler registered for notification type: {task.notification_type}")
            
            # Execute handler
            result = await handler(task)
            
            if result:
                task.status = NotificationStatus.SENT
                self.completed_tasks.append(task)
                logger.info(f"Notification sent successfully: {task.id}")
                return True
            else:
                raise Exception("Handler returned False")
                
        except Exception as e:
            error_msg = str(e)
            task.last_error = error_msg
            task.retry_count += 1
            
            logger.error(f"Error processing notification {task.id}: {error_msg}")
            
            if task.retry_count < task.max_retries:
                task.status = NotificationStatus.RETRY
                # Schedule retry
                retry_time = datetime.now() + timedelta(seconds=self.retry_delay * task.retry_count)
                task.scheduled_at = retry_time
                self.scheduled_tasks.append(task)
                logger.info(f"Notification {task.id} scheduled for retry at {retry_time}")
            else:
                task.status = NotificationStatus.FAILED
                self.failed_tasks.append(task)
                logger.error(f"Notification {task.id} failed after {task.max_retries} retries")
            
            return False
        
        finally:
            if task.id in self.processing_tasks:
                del self.processing_tasks[task.id]
    
    async def worker(self, worker_id: int):
        """Worker coroutine to process notifications."""
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Check queues in priority order
                task = None
                for priority in sorted(NotificationPriority, key=lambda x: x.value, reverse=True):
                    try:
                        task = self.queues[priority].get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue
                
                if task:
                    await self.process_notification(task)
                    self.queues[task.priority].task_done()
                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def scheduler(self):
        """Scheduler coroutine to handle scheduled notifications."""
        logger.info("Scheduler started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                ready_tasks = []
                
                # Find tasks ready to be processed
                for task in self.scheduled_tasks[:]:
                    if task.scheduled_at and task.scheduled_at <= current_time:
                        ready_tasks.append(task)
                        self.scheduled_tasks.remove(task)
                
                # Add ready tasks to appropriate queues
                for task in ready_tasks:
                    await self.queues[task.priority].put(task)
                    logger.info(f"Scheduled notification moved to queue: {task.id}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(10)
        
        logger.info("Scheduler stopped")
    
    async def start(self):
        """Start the queue manager."""
        if self.is_running:
            logger.warning("Queue manager is already running")
            return
        
        self.is_running = True
        
        # Start workers
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self.worker(i))
            self.workers.append(worker_task)
        
        # Start scheduler
        self.scheduler_task = asyncio.create_task(self.scheduler())
        
        logger.info(f"Queue manager started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the queue manager."""
        if not self.is_running:
            logger.warning("Queue manager is not running")
            return
        
        self.is_running = False
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        # Cancel scheduler
        if self.scheduler_task:
            self.scheduler_task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.workers, self.scheduler_task, return_exceptions=True)
        
        self.workers.clear()
        self.scheduler_task = None
        
        logger.info("Queue manager stopped")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {
            "queues": {},
            "scheduled_tasks": len(self.scheduled_tasks),
            "processing_tasks": len(self.processing_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "is_running": self.is_running,
            "workers": len(self.workers)
        }
        
        for priority, queue in self.queues.items():
            stats["queues"][priority.name] = queue.qsize()
        
        return stats
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task history."""
        all_tasks = (
            list(self.processing_tasks.values()) +
            self.completed_tasks[-limit:] +
            self.failed_tasks[-limit:]
        )
        
        # Sort by creation time
        all_tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return [task.to_dict() for task in all_tasks[:limit]]
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """Manually retry a failed task."""
        failed_task = None
        for task in self.failed_tasks:
            if task.id == task_id:
                failed_task = task
                break
        
        if not failed_task:
            logger.warning(f"Failed task not found: {task_id}")
            return False
        
        # Reset task status and add back to queue
        failed_task.status = NotificationStatus.PENDING
        failed_task.retry_count = 0
        failed_task.last_error = None
        
        await self.queues[failed_task.priority].put(failed_task)
        self.failed_tasks.remove(failed_task)
        
        logger.info(f"Failed task {task_id} added back to queue")
        return True

# Global queue manager instance
notification_queue = NotificationQueueManager()

# Example handlers
async def websocket_notification_handler(task: NotificationTask) -> bool:
    """Example handler for WebSocket notifications."""
    try:
        # This would integrate with your WebSocket server
        logger.info(f"Sending WebSocket notification to user {task.user_id}: {task.title}")
        # await websocket_server.send_notification(task.user_id, task.notification_type, task.title, task.message, task.data)
        return True
    except Exception as e:
        logger.error(f"WebSocket notification failed: {str(e)}")
        return False

async def email_notification_handler(task: NotificationTask) -> bool:
    """Example handler for email notifications."""
    try:
        # This would integrate with your email service
        logger.info(f"Sending email notification to user {task.user_id}: {task.title}")
        # await email_service.send_email(user_email, task.title, task.message)
        return True
    except Exception as e:
        logger.error(f"Email notification failed: {str(e)}")
        return False

# Example usage
if __name__ == "__main__":
    async def main():
        # Register handlers
        notification_queue.register_handler("websocket", websocket_notification_handler)
        notification_queue.register_handler("email", email_notification_handler)
        
        # Start queue manager
        await notification_queue.start()
        
        # Add some test notifications
        await notification_queue.add_notification(
            user_id=1,
            notification_type="websocket",
            title="테스트 알림",
            message="이것은 테스트 알림입니다.",
            priority=NotificationPriority.HIGH
        )
        
        # Schedule a notification for 30 seconds later
        scheduled_time = datetime.now() + timedelta(seconds=30)
        await notification_queue.add_notification(
            user_id=2,
            notification_type="email",
            title="예약된 알림",
            message="이것은 예약된 알림입니다.",
            scheduled_at=scheduled_time
        )
        
        # Let it run for a while
        await asyncio.sleep(60)
        
        # Print stats
        stats = notification_queue.get_queue_stats()
        print(f"Queue stats: {json.dumps(stats, indent=2)}")
        
        # Stop queue manager
        await notification_queue.stop()
    
    asyncio.run(main())

