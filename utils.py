"""
Shared utilities for Job Tracker Lambda functions.

NOTE: This file contains AWS-specific utilities (DynamoDB, S3, Secrets Manager)
for Lambda deployments. The current application uses SQLite locally.

These utilities are only used when deploying to AWS Lambda.
For local development, use the SQLite-based app via 'python run.py'.
"""

import json
import boto3
from decimal import Decimal
from datetime import datetime
from typing import Optional, Any
import hashlib


# Initialize clients (lazy loaded)
_dynamodb = None
_s3 = None
_secrets = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb')
    return _dynamodb


def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client('s3')
    return _s3


def get_secrets_client():
    global _secrets
    if _secrets is None:
        _secrets = boto3.client('secretsmanager')
    return _secrets


def get_secret(secret_arn: str) -> dict:
    """Retrieve secret from Secrets Manager."""
    client = get_secrets_client()
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def json_response(status_code: int, body: Any) -> dict:
    """Create API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def generate_job_id(url: str, title: str, company: str) -> str:
    """Generate deterministic job ID from URL + title + company."""
    content = f"{url}:{title}:{company}".lower()
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse ISO format date string."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


class JobStatus:
    """Job application status constants."""
    NEW = 'new'
    INTERESTED = 'interested'
    APPLIED = 'applied'
    INTERVIEWING = 'interviewing'
    REJECTED = 'rejected'
    OFFER = 'offer'
    PASSED = 'passed'  # User chose not to apply
    
    ALL = [NEW, INTERESTED, APPLIED, INTERVIEWING, REJECTED, OFFER, PASSED]


class JobModel:
    """Data model for job listings."""
    
    def __init__(self, table_name: str):
        self.table = get_dynamodb().Table(table_name)
    
    def put_job(self, user_id: str, job_data: dict) -> dict:
        """Create or update a job listing."""
        now = datetime.utcnow().isoformat()
        
        item = {
            'user_id': user_id,
            'job_id': job_data['job_id'],
            'title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', ''),
            'description': job_data.get('description', ''),
            'url': job_data.get('url', ''),
            'source': job_data.get('source', 'unknown'),
            'status': job_data.get('status', JobStatus.NEW),
            'score': job_data.get('score', 0),
            'analysis': job_data.get('analysis', {}),
            'cover_letter': job_data.get('cover_letter', ''),
            'notes': job_data.get('notes', ''),
            'created_at': job_data.get('created_at', now),
            'updated_at': now,
            'email_date': job_data.get('email_date', now),
        }
        
        self.table.put_item(Item=item)
        return item
    
    def get_job(self, user_id: str, job_id: str) -> Optional[dict]:
        """Get a single job by ID."""
        response = self.table.get_item(
            Key={'user_id': user_id, 'job_id': job_id}
        )
        return response.get('Item')
    
    def update_job(self, user_id: str, job_id: str, updates: dict) -> dict:
        """Update specific fields on a job."""
        # Build update expression
        update_parts = []
        expr_names = {}
        expr_values = {':updated_at': datetime.utcnow().isoformat()}
        
        for key, value in updates.items():
            if key not in ['user_id', 'job_id']:  # Don't update keys
                safe_key = f"#{key}"
                expr_names[safe_key] = key
                expr_values[f":{key}"] = value
                update_parts.append(f"{safe_key} = :{key}")
        
        update_parts.append("#updated_at = :updated_at")
        expr_names["#updated_at"] = "updated_at"
        
        response = self.table.update_item(
            Key={'user_id': user_id, 'job_id': job_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW"
        )
        return response.get('Attributes', {})
    
    def query_by_status(self, user_id: str, status: str, limit: int = 50) -> list:
        """Query jobs by status."""
        response = self.table.query(
            IndexName='status-index',
            KeyConditionExpression='user_id = :uid AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':uid': user_id, ':status': status},
            Limit=limit
        )
        return response.get('Items', [])
    
    def query_by_score(self, user_id: str, min_score: int = 0, limit: int = 50) -> list:
        """Query jobs ordered by score (highest first)."""
        response = self.table.query(
            IndexName='score-index',
            KeyConditionExpression='user_id = :uid AND score >= :min_score',
            ExpressionAttributeValues={':uid': user_id, ':min_score': min_score},
            ScanIndexForward=False,  # Descending order
            Limit=limit
        )
        return response.get('Items', [])
    
    def query_recent(self, user_id: str, limit: int = 50) -> list:
        """Query most recent jobs."""
        response = self.table.query(
            IndexName='date-index',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        return response.get('Items', [])
    
    def query_all(self, user_id: str, limit: int = 100) -> list:
        """Query all jobs for a user."""
        response = self.table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=limit
        )
        return response.get('Items', [])
    
    def job_exists(self, user_id: str, job_id: str) -> bool:
        """Check if a job already exists."""
        response = self.table.get_item(
            Key={'user_id': user_id, 'job_id': job_id},
            ProjectionExpression='job_id'
        )
        return 'Item' in response
