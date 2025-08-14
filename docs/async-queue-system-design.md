# Asynchronous Queue System Design

## Overview
A robust queue-based processing system that decouples file upload from processing, enabling scalable, distributed document processing with support for multiple queue backends (Kafka, Redis, SQS, etc.).

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   Queue/PubSub   │    │   Processing    │
│   (FastAPI)     │───▶│   Abstraction    │───▶│   Workers       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Notification  │    │   Message        │    │   Result        │
│   Service       │◀───│   Broker         │◀───│   Publisher     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 1.2 Component Interaction Flow

```
Client Upload
     │
     ▼
┌─────────────────┐
│  Upload API     │
│  - Validate     │ 
│  - Store File   │
│  - Enqueue Job  │
└─────────────────┘
     │
     ▼
┌─────────────────┐    ┌─────────────────┐
│  Job Queue      │───▶│  Worker Pool    │
│  - Job Metadata │    │  - Excel Worker │
│  - Priority     │    │  - PDF Worker   │  
│  - Retry Logic  │    │  - AI Worker    │
└─────────────────┘    └─────────────────┘
     │                          │
     ▼                          ▼
┌─────────────────┐    ┌─────────────────┐
│  Status Tracker │    │  Result Store   │
│  - Job Progress │    │  - Output JSON  │
│  - Error States │    │  - Generated    │
│  - Notifications│    │    HTML         │
└─────────────────┘    └─────────────────┘
     │                          │
     ▼                          ▼
┌─────────────────┐    ┌─────────────────┐
│  Client Notify  │    │  Completion     │
│  - Webhooks     │    │  Callback       │
│  - Polling API  │    │  - Store Result │
│  - WebSockets   │    │  - Notify Client│
└─────────────────┘    └─────────────────┘
```

## 2. Core Abstraction Layer

### 2.1 Queue Abstraction Interface
**File**: `converter/queue/queue_interface.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class JobMessage:
    job_id: str
    job_type: str  # "excel_processing", "pdf_processing", "ai_analysis"
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: int = 300
    created_at: float = None
    correlation_id: Optional[str] = None  # For tracking related jobs
    callback_context: Optional[Dict[str, Any]] = None

@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    worker_id: Optional[str] = None
    completed_at: Optional[float] = None

class QueueInterface(ABC):
    """Abstract interface for queue/pubsub implementations"""
    
    @abstractmethod
    async def publish_job(self, message: JobMessage) -> bool:
        """Publish a job to the queue"""
        pass
    
    @abstractmethod
    async def subscribe_jobs(self, job_types: List[str], handler: Callable) -> None:
        """Subscribe to job types with handler"""
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get current status of a job"""
        pass
    
    @abstractmethod
    async def update_job_status(self, job_id: str, status: JobStatus, 
                               result_data: Dict[str, Any] = None) -> bool:
        """Update job status and result"""
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or processing job"""
        pass
    
    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics (pending, processing, completed, etc.)"""
        pass
```

### 2.2 Queue Factory
**File**: `converter/queue/queue_factory.py`

```python
class QueueType(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    KAFKA = "kafka"
    SQS = "sqs"
    PUBSUB = "pubsub"
    RABBITMQ = "rabbitmq"

class QueueFactory:
    """Factory for creating queue implementations"""
    
    @staticmethod
    def create_queue(queue_type: QueueType, config: Dict[str, Any]) -> QueueInterface:
        if queue_type == QueueType.MEMORY:
            return MemoryQueue(config)
        elif queue_type == QueueType.REDIS:
            return RedisQueue(config)
        elif queue_type == QueueType.KAFKA:
            return KafkaQueue(config)
        elif queue_type == QueueType.SQS:
            return SQSQueue(config)
        elif queue_type == QueueType.PUBSUB:
            return PubSubQueue(config)
        elif queue_type == QueueType.RABBITMQ:
            return RabbitMQQueue(config)
        else:
            raise ValueError(f"Unsupported queue type: {queue_type}")
```

## 3. Implementation Examples

### 3.1 Memory Queue (Development/Testing)
**File**: `converter/queue/implementations/memory_queue.py`

```python
import asyncio
import uuid
from collections import defaultdict, deque
from typing import Dict, List, Callable
import time

class MemoryQueue(QueueInterface):
    """In-memory queue implementation for development and testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.queues: Dict[str, deque] = defaultdict(deque)
        self.job_status: Dict[str, JobResult] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.processing_jobs: Dict[str, JobMessage] = {}
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "pending_jobs": 0
        }
    
    async def publish_job(self, message: JobMessage) -> bool:
        message.created_at = time.time()
        if not message.job_id:
            message.job_id = str(uuid.uuid4())
            
        # Add to appropriate queue based on priority
        queue_key = f"{message.job_type}_{message.priority.value}"
        self.queues[queue_key].append(message)
        
        # Update status
        self.job_status[message.job_id] = JobResult(
            job_id=message.job_id,
            status=JobStatus.QUEUED
        )
        
        self._stats["total_jobs"] += 1
        self._stats["pending_jobs"] += 1
        
        # Notify subscribers
        await self._notify_subscribers(message.job_type, message)
        return True
    
    async def subscribe_jobs(self, job_types: List[str], handler: Callable) -> None:
        for job_type in job_types:
            self.subscribers[job_type].append(handler)
            
        # Process existing jobs
        asyncio.create_task(self._process_queue(job_types, handler))
    
    async def _process_queue(self, job_types: List[str], handler: Callable):
        """Background task to process queued jobs"""
        while True:
            for job_type in job_types:
                # Check all priority levels
                for priority in JobPriority:
                    queue_key = f"{job_type}_{priority.value}"
                    if self.queues[queue_key]:
                        message = self.queues[queue_key].popleft()
                        self._stats["pending_jobs"] -= 1
                        
                        # Mark as processing
                        self.processing_jobs[message.job_id] = message
                        await self.update_job_status(message.job_id, JobStatus.PROCESSING)
                        
                        # Process the job
                        asyncio.create_task(self._handle_job(message, handler))
                        break
            
            await asyncio.sleep(0.1)  # Prevent tight loop
    
    async def _handle_job(self, message: JobMessage, handler: Callable):
        """Handle individual job processing"""
        try:
            result = await handler(message)
            await self.update_job_status(
                message.job_id, 
                JobStatus.COMPLETED, 
                result
            )
            self._stats["completed_jobs"] += 1
        except Exception as e:
            await self.update_job_status(
                message.job_id, 
                JobStatus.FAILED, 
                {"error": str(e)}
            )
            self._stats["failed_jobs"] += 1
        finally:
            self.processing_jobs.pop(message.job_id, None)
```

### 3.2 Redis Queue Implementation  
**File**: `converter/queue/implementations/redis_queue.py`

```python
import redis.asyncio as redis
import json
import uuid
from typing import Dict, List, Callable

class RedisQueue(QueueInterface):
    """Redis-based queue implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis = redis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            password=config.get("password"),
            db=config.get("db", 0)
        )
        self.key_prefix = config.get("key_prefix", "docproc")
    
    async def publish_job(self, message: JobMessage) -> bool:
        if not message.job_id:
            message.job_id = str(uuid.uuid4())
            
        # Store job data
        job_key = f"{self.key_prefix}:job:{message.job_id}"
        await self.redis.hset(job_key, mapping={
            "data": json.dumps(message.__dict__, default=str),
            "status": JobStatus.QUEUED.value,
            "created_at": time.time()
        })
        
        # Add to priority queue
        queue_key = f"{self.key_prefix}:queue:{message.job_type}"
        priority_score = message.priority.value * 1000 + time.time()
        await self.redis.zadd(queue_key, {message.job_id: priority_score})
        
        # Publish notification
        await self.redis.publish(f"{self.key_prefix}:notify:{message.job_type}", message.job_id)
        return True
    
    async def subscribe_jobs(self, job_types: List[str], handler: Callable) -> None:
        pubsub = self.redis.pubsub()
        
        # Subscribe to job notifications
        for job_type in job_types:
            await pubsub.subscribe(f"{self.key_prefix}:notify:{job_type}")
        
        # Start processing
        asyncio.create_task(self._redis_worker(pubsub, job_types, handler))
    
    async def get_job_status(self, job_id: str) -> Optional[JobResult]:
        job_key = f"{self.key_prefix}:job:{job_id}"
        job_data = await self.redis.hgetall(job_key)
        
        if not job_data:
            return None
            
        return JobResult(
            job_id=job_id,
            status=JobStatus(job_data[b"status"].decode()),
            result_data=json.loads(job_data.get(b"result", b"{}").decode()),
            error_message=job_data.get(b"error"),
            processing_time=float(job_data.get(b"processing_time", 0)),
            completed_at=float(job_data.get(b"completed_at", 0))
        )
```

### 3.3 Kafka Queue Implementation
**File**: `converter/queue/implementations/kafka_queue.py`

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import asyncio

class KafkaQueue(QueueInterface):
    """Kafka-based queue implementation for high-throughput scenarios"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bootstrap_servers = config.get("bootstrap_servers", "localhost:9092")
        self.producer = None
        self.consumer = None
        self.topic_prefix = config.get("topic_prefix", "docproc")
        
    async def _ensure_producer(self):
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            await self.producer.start()
    
    async def publish_job(self, message: JobMessage) -> bool:
        await self._ensure_producer()
        
        if not message.job_id:
            message.job_id = str(uuid.uuid4())
        
        topic = f"{self.topic_prefix}.{message.job_type}"
        
        # Use priority as partition key for ordered processing within priority
        partition_key = f"priority_{message.priority.value}".encode('utf-8')
        
        await self.producer.send(
            topic,
            value=message.__dict__,
            key=partition_key
        )
        
        return True
    
    async def subscribe_jobs(self, job_types: List[str], handler: Callable) -> None:
        topics = [f"{self.topic_prefix}.{job_type}" for job_type in job_types]
        
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.config.get("consumer_group", "docproc_workers"),
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        asyncio.create_task(self._kafka_worker(handler))
    
    async def _kafka_worker(self, handler: Callable):
        """Kafka message consumer worker"""
        try:
            async for message in self.consumer:
                job_message = JobMessage(**message.value)
                try:
                    result = await handler(job_message)
                    # Optionally publish result to results topic
                    await self._publish_result(job_message.job_id, result)
                except Exception as e:
                    await self._publish_error(job_message.job_id, str(e))
        finally:
            await self.consumer.stop()
```

## 4. Job Processing System

### 4.1 Job Manager
**File**: `converter/queue/job_manager.py`

```python
class JobManager:
    """Manages job lifecycle and worker coordination"""
    
    def __init__(self, queue: QueueInterface, config: Dict[str, Any]):
        self.queue = queue
        self.config = config
        self.workers: Dict[str, WorkerPool] = {}
        self.job_handlers: Dict[str, Callable] = {}
        self.notification_service = NotificationService(config)
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a job handler for specific job type"""
        self.job_handlers[job_type] = handler
    
    async def start_workers(self):
        """Start worker pools for each job type"""
        for job_type, handler in self.job_handlers.items():
            worker_pool = WorkerPool(
                job_type=job_type,
                handler=handler,
                queue=self.queue,
                pool_size=self.config.get(f"{job_type}_workers", 2)
            )
            self.workers[job_type] = worker_pool
            await worker_pool.start()
    
    async def submit_job(self, 
                        job_type: str, 
                        payload: Dict[str, Any],
                        priority: JobPriority = JobPriority.NORMAL,
                        callback_context: Dict[str, Any] = None) -> str:
        """Submit a new job for processing"""
        
        job_message = JobMessage(
            job_id=str(uuid.uuid4()),
            job_type=job_type,
            payload=payload,
            priority=priority,
            callback_context=callback_context
        )
        
        success = await self.queue.publish_job(job_message)
        if success:
            return job_message.job_id
        else:
            raise Exception("Failed to submit job to queue")
    
    async def get_job_result(self, job_id: str) -> Optional[JobResult]:
        """Get job result with optional polling"""
        return await self.queue.get_job_status(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if possible"""
        return await self.queue.cancel_job(job_id)
```

### 4.2 Worker Pool
**File**: `converter/queue/worker_pool.py`

```python
class WorkerPool:
    """Manages a pool of workers for a specific job type"""
    
    def __init__(self, job_type: str, handler: Callable, queue: QueueInterface, pool_size: int):
        self.job_type = job_type
        self.handler = handler
        self.queue = queue
        self.pool_size = pool_size
        self.workers: List[Worker] = []
        self.running = False
    
    async def start(self):
        """Start all workers in the pool"""
        self.running = True
        
        for i in range(self.pool_size):
            worker = Worker(
                worker_id=f"{self.job_type}_worker_{i}",
                handler=self.handler,
                queue=self.queue
            )
            self.workers.append(worker)
            asyncio.create_task(worker.start())
        
        # Subscribe to jobs
        await self.queue.subscribe_jobs([self.job_type], self._route_to_worker)
    
    async def _route_to_worker(self, job_message: JobMessage):
        """Route job to available worker"""
        # Find available worker
        for worker in self.workers:
            if not worker.is_busy():
                await worker.process_job(job_message)
                return
        
        # All workers busy - this will be retried by queue
        # Could implement overflow logic here
        pass
    
    async def stop(self):
        """Stop all workers gracefully"""
        self.running = False
        for worker in self.workers:
            await worker.stop()
```

### 4.3 Individual Worker
**File**: `converter/queue/worker.py`

```python
class Worker:
    """Individual worker that processes jobs"""
    
    def __init__(self, worker_id: str, handler: Callable, queue: QueueInterface):
        self.worker_id = worker_id
        self.handler = handler
        self.queue = queue
        self.current_job: Optional[JobMessage] = None
        self.running = False
    
    def is_busy(self) -> bool:
        return self.current_job is not None
    
    async def start(self):
        """Start the worker"""
        self.running = True
        # Worker lifecycle managed by pool
    
    async def process_job(self, job_message: JobMessage):
        """Process a single job"""
        if self.current_job:
            raise Exception("Worker is already processing a job")
        
        self.current_job = job_message
        start_time = time.time()
        
        try:
            # Update job status to processing
            await self.queue.update_job_status(
                job_message.job_id, 
                JobStatus.PROCESSING
            )
            
            # Execute the job
            result = await self.handler(job_message)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update job status to completed
            await self.queue.update_job_status(
                job_message.job_id,
                JobStatus.COMPLETED,
                {
                    "result": result,
                    "processing_time": processing_time,
                    "worker_id": self.worker_id
                }
            )
            
        except Exception as e:
            # Handle job failure
            await self.queue.update_job_status(
                job_message.job_id,
                JobStatus.FAILED,
                {
                    "error": str(e),
                    "worker_id": self.worker_id,
                    "processing_time": time.time() - start_time
                }
            )
            
        finally:
            self.current_job = None
    
    async def stop(self):
        """Stop the worker gracefully"""
        self.running = False
        # Wait for current job to complete if any
        while self.current_job:
            await asyncio.sleep(0.1)
```

## 5. Integration with Existing System

### 5.1 FastAPI Integration
**File**: `fastapi_service/routers/async_processing.py`

```python
from converter.queue.job_manager import JobManager
from converter.queue.queue_factory import QueueFactory, QueueType

# Initialize queue system
queue_config = {
    "type": os.getenv("QUEUE_TYPE", "memory"),
    "redis_host": os.getenv("REDIS_HOST", "localhost"),
    "redis_port": int(os.getenv("REDIS_PORT", 6379)),
}

queue = QueueFactory.create_queue(
    QueueType(queue_config["type"]), 
    queue_config
)

job_manager = JobManager(queue, queue_config)

# Register handlers
job_manager.register_handler("excel_processing", excel_processing_handler)
job_manager.register_handler("pdf_processing", pdf_processing_handler)
job_manager.register_handler("ai_analysis", ai_analysis_handler)

@router.post("/upload-async")
async def upload_file_async(
    file: UploadFile = File(...),
    priority: str = "normal",
    callback_url: Optional[str] = None
):
    """Upload file for asynchronous processing"""
    
    # Store file temporarily
    file_path = await store_uploaded_file(file)
    
    # Determine job type
    job_type = "pdf_processing" if file.filename.endswith('.pdf') else "excel_processing"
    
    # Submit job
    job_id = await job_manager.submit_job(
        job_type=job_type,
        payload={
            "file_path": file_path,
            "filename": file.filename,
            "file_size": file.size
        },
        priority=JobPriority[priority.upper()],
        callback_context={
            "callback_url": callback_url,
            "user_id": get_current_user_id(),
            "upload_timestamp": time.time()
        }
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "File queued for processing",
        "polling_url": f"/api/job/{job_id}/status"
    }

@router.get("/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get job processing status"""
    result = await job_manager.get_job_result(job_id)
    
    if not result:
        raise HTTPException(404, "Job not found")
    
    return {
        "job_id": job_id,
        "status": result.status.value,
        "result": result.result_data,
        "error": result.error_message,
        "processing_time": result.processing_time,
        "completed_at": result.completed_at
    }

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job"""
    success = await job_manager.cancel_job(job_id)
    
    if success:
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(400, "Job could not be cancelled")

@router.get("/queue/stats")
async def get_queue_stats():
    """Get queue statistics"""
    return await queue.get_queue_stats()
```

### 5.2 Job Handlers
**File**: `converter/queue/handlers/excel_handler.py`

```python
async def excel_processing_handler(job_message: JobMessage) -> Dict[str, Any]:
    """Handle Excel file processing"""
    
    file_path = job_message.payload["file_path"]
    filename = job_message.payload["filename"]
    
    try:
        # Use existing Excel processing logic
        from converter.compact_excel_processor import CompactExcelProcessor
        
        processor = CompactExcelProcessor()
        result = processor.process_file(file_path)
        
        # Store results
        storage = get_storage_service()
        result_key = f"async_results/{job_message.job_id}/processed.json"
        storage.put_json(result_key, result)
        
        # Generate HTML
        from converter.html_generator import HTMLGenerator
        html_generator = HTMLGenerator()
        html_content = html_generator.generate_complete_html(
            {"full": result}, 
            job_message.payload
        )
        
        html_key = f"async_results/{job_message.job_id}/display.html"
        storage.put_bytes(html_key, html_content.encode('utf-8'))
        
        return {
            "status": "completed",
            "result_key": result_key,
            "html_key": html_key,
            "filename": filename,
            "tables_count": len(result.get("workbook", {}).get("sheets", [])),
            "file_size": job_message.payload.get("file_size", 0)
        }
        
    except Exception as e:
        # Clean up on error
        cleanup_temp_files(file_path)
        raise e
    finally:
        # Always clean up temp file
        cleanup_temp_files(file_path)
```

## 6. Notification System

### 6.1 Notification Service
**File**: `converter/queue/notification_service.py`

```python
class NotificationService:
    """Handles job completion notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_client = httpx.AsyncClient()
        self.websocket_manager = WebSocketManager()
    
    async def notify_job_completion(self, job_result: JobResult, callback_context: Dict[str, Any]):
        """Send notifications for job completion"""
        
        notifications = []
        
        # Webhook notification
        if callback_context.get("callback_url"):
            notifications.append(
                self._send_webhook(job_result, callback_context["callback_url"])
            )
        
        # WebSocket notification
        if callback_context.get("user_id"):
            notifications.append(
                self._send_websocket(job_result, callback_context["user_id"])
            )
        
        # Email notification (if configured)
        if callback_context.get("email") and self.config.get("email_enabled"):
            notifications.append(
                self._send_email(job_result, callback_context["email"])
            )
        
        # Send all notifications concurrently
        await asyncio.gather(*notifications, return_exceptions=True)
    
    async def _send_webhook(self, job_result: JobResult, callback_url: str):
        """Send webhook notification"""
        try:
            payload = {
                "job_id": job_result.job_id,
                "status": job_result.status.value,
                "result": job_result.result_data,
                "error": job_result.error_message,
                "completed_at": job_result.completed_at
            }
            
            response = await self.webhook_client.post(
                callback_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
        except Exception as e:
            # Log webhook failure but don't raise
            logger.error(f"Webhook notification failed: {e}")
    
    async def _send_websocket(self, job_result: JobResult, user_id: str):
        """Send WebSocket notification"""
        await self.websocket_manager.send_to_user(user_id, {
            "type": "job_completion",
            "job_id": job_result.job_id,
            "status": job_result.status.value,
            "result": job_result.result_data
        })
```

## 7. Configuration & Deployment

### 7.1 Configuration
**File**: `converter/queue/config.py`

```python
@dataclass
class QueueConfig:
    # Queue Backend
    queue_type: str = "memory"  # memory, redis, kafka, sqs
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_prefix: str = "docproc"
    kafka_consumer_group: str = "docproc_workers"
    
    # AWS SQS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    sqs_queue_prefix: str = "docproc"
    
    # Worker Configuration
    excel_workers: int = 2
    pdf_workers: int = 2
    ai_workers: int = 1
    max_job_timeout: int = 3600  # 1 hour
    max_retries: int = 3
    
    # Notification Configuration
    webhook_timeout: int = 30
    websocket_enabled: bool = True
    email_enabled: bool = False
    
    @classmethod
    def from_env(cls) -> 'QueueConfig':
        return cls(
            queue_type=os.getenv("QUEUE_TYPE", "memory"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            redis_password=os.getenv("REDIS_PASSWORD"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            excel_workers=int(os.getenv("EXCEL_WORKERS", 2)),
            pdf_workers=int(os.getenv("PDF_WORKERS", 2)),
            ai_workers=int(os.getenv("AI_WORKERS", 1)),
        )
```

### 7.2 Docker Compose Example
**File**: `docker-compose.queue.yml`

```yaml
version: '3.8'

services:
  web:
    build: .
    environment:
      - QUEUE_TYPE=redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - EXCEL_WORKERS=3
      - PDF_WORKERS=2
    depends_on:
      - redis
    volumes:
      - ./storage:/app/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  worker-excel:
    build: .
    command: python -m converter.queue.workers.excel_worker
    environment:
      - QUEUE_TYPE=redis
      - REDIS_HOST=redis
      - WORKER_TYPE=excel
    depends_on:
      - redis
    volumes:
      - ./storage:/app/storage
    deploy:
      replicas: 2

  worker-pdf:
    build: .
    command: python -m converter.queue.workers.pdf_worker
    environment:
      - QUEUE_TYPE=redis
      - REDIS_HOST=redis
      - WORKER_TYPE=pdf
    depends_on:
      - redis
    volumes:
      - ./storage:/app/storage
    deploy:
      replicas: 2

volumes:
  redis_data:
```

## 8. Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. Queue abstraction interface
2. Memory queue implementation
3. Basic job manager
4. Simple worker pool

### Phase 2: Redis Implementation (Week 2)
1. Redis queue implementation
2. Job persistence and status tracking
3. Notification system
4. Error handling and retries

### Phase 3: FastAPI Integration (Week 3)
1. Async upload endpoints
2. Job status endpoints
3. WebSocket notifications
4. Queue statistics dashboard

### Phase 4: Advanced Features (Week 4)
1. Additional queue backends (Kafka, SQS)
2. Job prioritization and scheduling
3. Worker auto-scaling
4. Monitoring and alerting

## 9. Success Metrics

### 9.1 Performance Metrics
- **Throughput**: Jobs processed per minute
- **Latency**: Time from upload to queue to processing start
- **Reliability**: Job success rate and retry effectiveness
- **Scalability**: Linear scaling with additional workers

### 9.2 Operational Metrics
- **Queue Depth**: Number of pending jobs
- **Worker Utilization**: Percentage of time workers are busy
- **Error Rate**: Percentage of failed jobs
- **Response Time**: API response times for job submission and status

This design provides a robust, scalable foundation for asynchronous document processing that can adapt to various queue backends and deployment scenarios while maintaining high reliability and performance.
