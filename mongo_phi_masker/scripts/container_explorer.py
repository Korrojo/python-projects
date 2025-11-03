#!/usr/bin/env python3
"""
Container Document Structure Explorer

This script examines the actual structure of Container documents in the MongoDB database
and reports on the presence of PHI fields. This helps identify any discrepancies between
the schema definition and the actual data content.
"""

import os
import json
import argparse
import logging
from pymongo import MongoClient
from datetime import datetime

def setup_logging(log_level="INFO", log_file=None, max_bytes=10 * 1024 * 1024, backup_count=5, use_timed_rotating=False):
    """Set up logging configuration with rotation options.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file, if None a default path is generated
        max_bytes (int): Maximum size in bytes before rotating the log file
        backup_count (int): Number of backup files to keep
        use_timed_rotating (bool): If True, use time-based rotation instead of size-based
    """
    # Override settings from environment variables if present
    max_bytes = int(os.environ.get("LOG_MAX_BYTES", max_bytes))
    backup_count = int(os.environ.get("LOG_BACKUP_COUNT", backup_count))
    use_timed_rotating = os.environ.get("LOG_TIMED_ROTATION", str(use_timed_rotating)).lower() == "true"
    
    log_dir = "logs/exploration"
    os.makedirs(log_dir, exist_ok=True)
    
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotation_type = "time" if use_timed_rotating else "size"
        log_file = f"{log_dir}/container_explorer_{timestamp}_{rotation_type}.log"
        
        # Create a symlink to the latest log
        latest_log = f"{log_dir}/container_explorer_latest.log"
        if os.path.exists(latest_log):
            try:
                os.remove(latest_log)
            except:
                pass
        try:
            os.symlink(log_file, latest_log)
        except:
            pass
    
    # Set up logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Use the appropriate handler based on rotation type
    if use_timed_rotating:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when='midnight', interval=1, backupCount=backup_count
        )
    else:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    
    # Convert string log level to numeric if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    root_logger.setLevel(log_level)
    
    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create the module logger
    logger = logging.getLogger(__name__)
    
    # Log initialization message
    rotation_msg = "time-based" if use_timed_rotating else f"size-based ({max_bytes/1024/1024:.1f}MB max)"
    logger.info(f"Logging initialized with level={logging.getLevelName(log_level)}, file={log_file}, rotation={rotation_msg}")
    
    return logger

def get_mongodb_uri(env_prefix):
    """Generate MongoDB URI from environment variables."""
    username = os.environ.get(f"{env_prefix}_USERNAME")
    password = os.environ.get(f"{env_prefix}_PASSWORD")
    host = os.environ.get(f"{env_prefix}_HOST")
    use_srv = os.environ.get(f"{env_prefix}_USE_SRV", "false").lower() == "true"
    
    protocol = "mongodb+srv" if use_srv else "mongodb"
    return f"{protocol}://{username}:{password}@{host}"

def explore_structure(doc, path="", max_depth=5, current_depth=0):
    """Recursively explore document structure."""
    if current_depth >= max_depth:
        return {"__max_depth_reached__": True}
    
    if doc is None:
        return {"__type__": "null"}
    
    result = {}
    
    if isinstance(doc, dict):
        for key, value in doc.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, (dict, list)):
                result[key] = explore_structure(value, current_path, max_depth, current_depth + 1)
            else:
                result[key] = {
                    "__type__": type(value).__name__,
                    "__sample__": str(value)[:50] if value is not None else None
                }
                
    elif isinstance(doc, list):
        if not doc:
            return {"__type__": "empty_array"}
            
        if all(isinstance(item, dict) for item in doc):
            # Sample the first few items if it's a list of documents
            samples = min(3, len(doc))
            result["__array_of_documents__"] = {
                "__length__": len(doc),
                "__samples__": [
                    explore_structure(doc[i], f"{path}[{i}]", max_depth, current_depth + 1)
                    for i in range(samples)
                ]
            }
        else:
            # For arrays of primitives, just show the type and count
            result["__array_of_primitives__"] = {
                "__length__": len(doc),
                "__type__": type(doc[0]).__name__ if doc else "unknown",
                "__samples__": [str(item)[:50] for item in doc[:3]]
            }
    else:
        return {
            "__type__": type(doc).__name__,
            "__value__": str(doc)[:50]
        }
    
    return result

def get_nested_value(document, path):
    """Get a value from a nested document using dot notation and array indexing."""
    if not document:
        return None
    
    # Handle special array iteration path syntax ([] indicates any array element)
    if '[]' in path:
        base_path, rest_path = path.split('[]', 1)
        if rest_path.startswith('.'):
            rest_path = rest_path[1:]  # Remove leading dot if present
        
        base_value = get_nested_value(document, base_path)
        
        if not isinstance(base_value, list):
            return None
        
        # Process all elements in the array
        results = []
        for item in base_value:
            value = get_nested_value(item, rest_path)
            if value is not None:
                results.append(value)
        
        return results
    
    # Regular path handling
    parts = path.split('.')
    current = document
    
    for part in parts:
        # Handle array indexing (e.g., "Encounter[0]")
        if '[' in part and part.endswith(']'):
            array_name, idx_str = part.split('[')
            idx = int(idx_str[:-1])  # Remove closing bracket and convert to int
            
            if not isinstance(current, dict) or array_name not in current:
                return None
            
            array_value = current[array_name]
            if not isinstance(array_value, list) or idx >= len(array_value):
                return None
            
            current = array_value[idx]
        else:
            # Regular dict access
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
    
    return current

def count_phi_fields(doc, phi_fields):
    """Count occurrences of PHI fields in the document."""
    counts = {field: 0 for field in phi_fields}
    doc_presence = {field: False for field in phi_fields}
    
    # Process fields with array iteration notation (e.g., Encounter[].PatientFirstName)
    for field in phi_fields:
        if '[]' in field:
            base_path, rest_path = field.split('[]', 1)
            if rest_path.startswith('.'):
                rest_path = rest_path[1:]  # Remove leading dot if present
            
            base_value = get_nested_value(doc, base_path)
            
            if isinstance(base_value, list):
                for i, item in enumerate(base_value):
                    if isinstance(item, dict):
                        # Get the value using the remaining path
                        value = get_nested_value(item, rest_path)
                        if value is not None:
                            counts[field] += 1
                            doc_presence[field] = True
        else:
            # Regular fields without array notation
            value = get_nested_value(doc, field)
            if value is not None:
                counts[field] += 1
                doc_presence[field] = True
    
    return counts, doc_presence

def analyze_container_structure(sample_size=10, logger=None):
    """Analyze the structure of Container documents."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Connect to MongoDB
    source_uri = get_mongodb_uri("MONGO_SOURCE")
    source_client = MongoClient(source_uri)
    source_db = source_client[os.environ.get("MONGO_SOURCE_DB")]
    source_coll = source_db[os.environ.get("MONGO_SOURCE_COLL")]
    
    logger.info(f"Connected to {os.environ.get('MONGO_SOURCE_DB')}.{os.environ.get('MONGO_SOURCE_COLL')}")
    logger.info(f"Analyzing {sample_size} random documents")
    
    # Get sample documents
    pipeline = [{"$sample": {"size": sample_size}}]
    sample_docs = list(source_coll.aggregate(pipeline, allowDiskUse=True))
    
    logger.info(f"Retrieved {len(sample_docs)} documents for analysis")
    
    # Define the PHI fields we're looking for - using array notation for Encounter
    phi_fields = [
        "Encounter[].PatientFirstName",
        "Encounter[].PatientMiddleName",
        "Encounter[].PatientLastName",
        "Encounter[].UserName",
        "Encounter[].CaseNote.Notes",
        "Encounter[].HPI.HPINote",
        "Encounter[].CareSnapshot.Goals",
        "Encounter[].Reason",
        "Encounter[].PhoneCall.Activities[].VisitAddress",
        "Encounter[].PhoneCall.Activities[].PhoneNumber",
        "Encounter[].AssessmentAndPlan.ProblemList[].Comments",
        "Encounter[].AssessmentAndPlan.ProblemList[].FinalNotes",
        "Encounter[].Dat[].OtherReason",
        "Encounter[].Document.Documents[].Path"
    ]
    
    # Analyze first document in detail
    if sample_docs:
        logger.info("Analyzing document structure...")
        structure = explore_structure(sample_docs[0])
        
        # Save structure to file
        output_dir = "logs/exploration"
        os.makedirs(output_dir, exist_ok=True)
        structure_file = f"{output_dir}/container_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(structure_file, "w") as f:
            json.dump(structure, f, indent=2)
            
        logger.info(f"Document structure saved to {structure_file}")
    
    # Count PHI fields across all sample documents
    logger.info("Counting PHI field occurrences...")
    phi_counts = {field: 0 for field in phi_fields}
    doc_counts = {field: 0 for field in phi_fields}
    
    for doc in sample_docs:
        # Count PHI fields in this document
        doc_phi_counts, doc_presence = count_phi_fields(doc, phi_fields)
        
        # Update total counts
        for field, count in doc_phi_counts.items():
            phi_counts[field] += count
            if doc_presence[field]:
                doc_counts[field] += 1
    
    # Generate report
    logger.info("\nPHI Field Occurrence Report:")
    logger.info(f"{'Field':<50} {'Documents':<10} {'Occurrences':<12}")
    logger.info("-" * 75)
    
    for field in phi_fields:
        logger.info(
            f"{field:<50} {doc_counts[field]:<10} {phi_counts[field]:<12}"
        )
    
    # Generate summary
    total_docs = len(sample_docs)
    summary = {
        "sample_size": total_docs,
        "phi_fields": {
            field: {
                "documents": doc_counts[field],
                "document_percentage": round(doc_counts[field] / total_docs * 100, 1) if total_docs > 0 else 0,
                "occurrences": phi_counts[field],
                "average_per_document": round(phi_counts[field] / total_docs, 2) if total_docs > 0 else 0
            }
            for field in phi_fields
        }
    }
    
    # Save summary to file
    summary_file = f"{output_dir}/container_phi_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"\nPHI field summary saved to {summary_file}")
    
    # Clean up
    source_client.close()
    
    return summary

def main():
    """Main entry point for container explorer script."""
    parser = argparse.ArgumentParser(description='Explore Container collection structure')
    parser.add_argument('--sample-size', type=int, default=10, help='Number of documents to sample for exploration')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set logging level')
    parser.add_argument('--output-file', help='Path to save exploration results JSON')
    parser.add_argument('--log-file', type=str, help='Custom log file path')
    parser.add_argument('--log-max-bytes', type=int, default=10 * 1024 * 1024, help='Maximum log file size before rotation (default: 10MB)')
    parser.add_argument('--log-backup-count', type=int, default=5, help='Number of backup log files to keep (default: 5)')
    parser.add_argument('--log-timed-rotation', action='store_true', help='Use time-based rotation instead of size-based')
    
    args = parser.parse_args()
    
    # Setup enhanced logging
    logger = setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        max_bytes=args.log_max_bytes,
        backup_count=args.log_backup_count,
        use_timed_rotating=args.log_timed_rotation
    )
    
    # Load appropriate .env file
    env_file = f".env.{args.env}"
    if not os.path.isfile(env_file):
        logger.error(f"Environment file {env_file} not found")
        return 1
    
    from dotenv import load_dotenv
    load_dotenv(env_file)
    logger.info(f"Loaded environment from {env_file}")
    
    # Run analysis
    analyze_container_structure(sample_size=args.sample_size, logger=logger)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
