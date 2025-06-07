import os
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from threading import Thread
import queue
import time


class GrafanaCloudLogger:
    """
    Logger that sends structured logs to Grafana Cloud Loki
    """
    
    def __init__(self):
        self.loki_url = os.getenv("GRAFANA_LOKI_URL")  # e.g., https://logs-prod-us-central1.grafana.net/loki/api/v1/push
        self.loki_username = os.getenv("GRAFANA_LOKI_USERNAME")  # Your Grafana Cloud username
        self.loki_password = os.getenv("GRAFANA_LOKI_PASSWORD")  # Your Grafana Cloud API key
        
        self.enabled = all([self.loki_url, self.loki_username, self.loki_password])
        
        if self.enabled:
            # Create a queue for batching logs
            self.log_queue = queue.Queue()
            self.batch_size = int(os.getenv("LOKI_BATCH_SIZE", "10"))
            self.flush_interval = int(os.getenv("LOKI_FLUSH_INTERVAL", "5"))  # seconds
            
            # Start background thread to send logs
            self.sender_thread = Thread(target=self._log_sender, daemon=True)
            self.sender_thread.start()
            
            print("Grafana Cloud Logger initialized successfully")
        else:
            print("Grafana Cloud Logger disabled - missing configuration")
    
    def send_log(self, level: str, message: str, labels: Dict[str, str], timestamp: datetime = None):
        """
        Send a log entry to Grafana Cloud Loki
        """
        if not self.enabled:
            return
            
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Convert timestamp to nanoseconds (Loki requirement)
        timestamp_ns = str(int(timestamp.timestamp() * 1_000_000_000))
        
        # Prepare log entry
        log_entry = {
            "timestamp": timestamp_ns,
            "line": json.dumps({
                "level": level,
                "message": message,
                **labels
            })
        }
        
        # Add to queue
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # If queue is full, skip this log entry
            pass
    
    def _log_sender(self):
        """
        Background thread that batches and sends logs to Loki
        """
        batch = []
        last_flush = time.time()
        
        while True:
            try:
                # Get log entry with timeout
                try:
                    log_entry = self.log_queue.get(timeout=1.0)
                    batch.append(log_entry)
                except queue.Empty:
                    log_entry = None
                
                # Check if we should flush the batch
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and time.time() - last_flush >= self.flush_interval)
                )
                
                if should_flush and batch:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()
                    
            except Exception as e:
                print(f"Error in log sender thread: {e}")
                time.sleep(1)
    
    def _send_batch(self, batch: List[Dict]):
        """
        Send a batch of logs to Loki
        """
        try:
            if not batch:
                return
                
            # Prepare Loki payload
            streams = []
            
            # Group logs by labels
            streams_dict = {}
            for entry in batch:
                try:
                    # Extract labels from the log line
                    log_data = json.loads(entry["line"])
                    
                    # Create labels for Loki (ensure all values are strings)
                    labels = {
                        "app": "padeltour",
                        "level": str(log_data.get("level", "info")).lower(),
                        "logger": str(log_data.get("logger", "unknown")),
                        "environment": str(os.getenv("ENVIRONMENT", "production"))
                    }
                    
                    # Add optional labels (sanitize values for Loki)
                    if "event_type" in log_data:
                        labels["event_type"] = str(log_data["event_type"]).replace(" ", "_").replace("/", "_")
                    
                    if "endpoint" in log_data:
                        # Clean endpoint for use as label (remove query params, etc.)
                        endpoint = str(log_data["endpoint"]).split('?')[0]
                        # Replace problematic characters for Loki labels
                        endpoint = endpoint.replace("/", "_").replace("-", "_")
                        labels["endpoint"] = endpoint
                    
                    # Create a hashable key from labels for grouping
                    label_key = tuple(sorted(labels.items()))
                    
                    if label_key not in streams_dict:
                        streams_dict[label_key] = []
                    
                    streams_dict[label_key].append([entry["timestamp"], entry["line"]])
                    
                except Exception as log_error:
                    print(f"Error processing log entry: {log_error}, entry: {entry}")
                    continue
            
            # Convert to Loki format
            streams = [
                {
                    "stream": dict(label_key),  # Convert tuple back to dict
                    "values": values
                }
                for label_key, values in streams_dict.items()
            ]
            
            payload = {"streams": streams}
            
            # Debug: Print payload structure (only in development)
            if os.getenv("DEBUG_GRAFANA") == "true":
                print(f"Sending {len(streams)} streams to Grafana")
                for i, stream in enumerate(streams[:2]):  # Only show first 2 streams
                    print(f"Stream {i}: {stream['stream']}")
            
            # Send to Loki
            response = requests.post(
                self.loki_url,
                auth=(self.loki_username, self.loki_password),
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 204:
                # Success
                if os.getenv("DEBUG_GRAFANA") == "true":
                    print(f"Successfully sent {len(batch)} logs to Grafana")
            else:
                print(f"Failed to send logs to Grafana: {response.status_code} - {response.text}")
                # Print the payload for debugging
                print(f"Payload that failed: {json.dumps(payload, indent=2)[:500]}...")
                
        except Exception as e:
            print(f"Error sending logs to Grafana: {e}")
            # Print more context for debugging
            print(f"Batch size: {len(batch) if batch else 0}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(f"Traceback: {traceback.format_exc()}")


# Global instance
grafana_logger = GrafanaCloudLogger()


class GrafanaHandler(logging.Handler):
    """
    Custom logging handler that sends logs to Grafana Cloud
    """
    
    def __init__(self):
        super().__init__()
        self.grafana_logger = grafana_logger
    
    def emit(self, record):
        """
        Emit a log record to Grafana Cloud
        """
        if not self.grafana_logger.enabled:
            return
        
        try:
            # Format the record
            message = self.format(record)
            
            # Extract labels from the record
            labels = {
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": str(record.lineno)
            }
            
            # Add extra fields if they exist
            if hasattr(record, 'request_id'):
                labels['request_id'] = str(record.request_id)
            
            if hasattr(record, 'user_id'):
                labels['user_id'] = str(record.user_id)
                
            if hasattr(record, 'event_type'):
                labels['event_type'] = str(record.event_type)
                
            if hasattr(record, 'endpoint'):
                labels['endpoint'] = str(record.endpoint)
            
            # Send to Grafana
            self.grafana_logger.send_log(
                level=record.levelname,
                message=message,
                labels=labels,
                timestamp=datetime.fromtimestamp(record.created)
            )
            
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error sending log to Grafana: {e}")


def setup_grafana_logging():
    """
    Add Grafana handler to the root logger
    """
    if grafana_logger.enabled:
        grafana_handler = GrafanaHandler()
        grafana_handler.setLevel(logging.INFO)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(grafana_handler)
        
        print("Grafana Cloud logging enabled")
    else:
        print("Grafana Cloud logging disabled - set environment variables to enable") 