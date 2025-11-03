#!/usr/bin/env python3
"""
Orchestration script to handle the entire migration process for both PHI and non-PHI collections.
This script coordinates the migration of 200+ collections within a 24-hour timeframe,
tracking progress and ensuring optimal resource utilization.
"""

import json
import os
import sys
import time
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import project modules
from src.utils.config_loader import ConfigLoader

# Setup logging with your specific directory structure and timestamped parent folder
base_log_dir = Path("C:/Users/demesew/logs/mask/PHI")
run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
run_log_dir = base_log_dir / f"mask_parallel_{run_timestamp}"
os.makedirs(run_log_dir, exist_ok=True)

orchestration_log_file = run_log_dir / f"mask_orchestration_{run_timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(orchestration_log_file)
    ]
)
logger = logging.getLogger("orchestration")

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
PHI_COLLECTIONS_PATH = DOCS_DIR / "phi_collections.json"
NO_PHI_COLLECTIONS_PATH = DOCS_DIR / "no-phi_collections.json"
ANALYSIS_OUTPUT_PATH = DOCS_DIR / "collection_analysis.json"
CHECKPOINT_PATH = DOCS_DIR / "migration_checkpoint.json"


def load_collections():
    """
    Load PHI and non-PHI collection lists.
    
    Returns:
        Tuple of (phi_collections, no_phi_collections)
    """
    try:
        with open(PHI_COLLECTIONS_PATH, 'r') as f:
            phi_collections = json.load(f)
        
        with open(NO_PHI_COLLECTIONS_PATH, 'r') as f:
            no_phi_collections = json.load(f)
        
        logger.info(f"Loaded {len(phi_collections)} PHI collections and {len(no_phi_collections)} non-PHI collections")
        return phi_collections, no_phi_collections
    
    except Exception as e:
        logger.error(f"Error loading collection lists: {str(e)}")
        sys.exit(1)


def load_analysis():
    """
    Load collection analysis data.
    
    Returns:
        Analysis data dictionary
    """
    if not os.path.exists(ANALYSIS_OUTPUT_PATH):
        logger.warning(f"Analysis file not found: {ANALYSIS_OUTPUT_PATH}")
        return None
    
    try:
        with open(ANALYSIS_OUTPUT_PATH, 'r') as f:
            analysis = json.load(f)
        
        logger.info(f"Loaded analysis for {analysis['total_collections_analyzed']} collections")
        return analysis
    
    except Exception as e:
        logger.error(f"Error loading analysis data: {str(e)}")
        return None


def load_checkpoint():
    """
    Load migration checkpoint if it exists.
    
    Returns:
        Checkpoint data dictionary or None if no checkpoint exists
    """
    if not os.path.exists(CHECKPOINT_PATH):
        logger.info("No checkpoint found, starting fresh migration")
        return None
    
    try:
        with open(CHECKPOINT_PATH, 'r') as f:
            checkpoint = json.load(f)
        
        logger.info(f"Loaded checkpoint from {checkpoint['timestamp']}")
        return checkpoint
    
    except Exception as e:
        logger.error(f"Error loading checkpoint: {str(e)}")
        return None


def save_checkpoint(completed_collections, failed_collections, current_batch):
    """
    Save migration checkpoint.
    
    Args:
        completed_collections: List of completed collection names
        failed_collections: List of failed collection names
        current_batch: Current batch data
    """
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "completed_collections": completed_collections,
        "failed_collections": failed_collections,
        "current_batch": current_batch
    }
    
    try:
        with open(CHECKPOINT_PATH, 'w') as f:
            json.dump(checkpoint, f, indent=4)
        
        logger.info(f"Checkpoint saved to {CHECKPOINT_PATH}")
    
    except Exception as e:
        logger.error(f"Error saving checkpoint: {str(e)}")


def migrate_no_phi_collections(no_phi_collections, config_path, env_path, batch_size=100):
    """
    Migrate collections without PHI data.
    
    Args:
        no_phi_collections: List of collection names without PHI
        config_path: Path to configuration file
        env_path: Path to environment file
        batch_size: Batch size for document migration
        
    Returns:
        Tuple of (success_count, failed_collections)
    """
    logger.info(f"Starting migration of {len(no_phi_collections)} no-PHI collections")
    
    script_path = PROJECT_ROOT / "scripts" / "migrate_no_phi_collections.py"
    collections_arg = ",".join(no_phi_collections)
    
    # Use python3 explicitly
    command = [
        "python3", 
        str(script_path),
        "--config", config_path,
        "--env", env_path,
        "--batch-size", str(batch_size),
        "--collections", collections_arg
    ]
    
    logger.info(f"Running command: {' '.join(command)}")
    
    success_count = 0
    failed_collections = []
    
    try:
        # Run the migration script as a subprocess
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Successfully migrated {len(no_phi_collections)} no-PHI collections.")
            # Assuming the script outputs failed collections if any, otherwise all succeeded
            # For simplicity now, assume all succeeded if return code is 0
            # A more robust approach would parse stdout/stderr or use a status file
            success_count = len(no_phi_collections) 
        else:
            logger.error(f"Error migrating no-PHI collections. Return code: {process.returncode}")
            logger.error(f"Stderr:\n{stderr}")
            logger.error(f"Stdout:\n{stdout}")
            # Assume all failed if the script exits non-zero
            failed_collections = list(no_phi_collections)
            
    except Exception as e:
        logger.error(f"Failed to execute migration script for no-PHI collections: {str(e)}")
        failed_collections = list(no_phi_collections)

    return success_count, failed_collections


def migrate_phi_collection_batch(batch, config_path, env_path, use_in_situ=True, run_log_dir=None):
    """
    Migrate a batch of PHI collections with masking.
    
    Args:
        batch: List of collection names with PHI
        config_path: Path to configuration file
        env_path: Path to environment file
        use_in_situ: Whether to use in-situ masking (default: True)
        run_log_dir: Directory for this run's logs
        
    Returns:
        Tuple of (success_list, failed_list)
    """
    logger.info(f"Starting migration of {len(batch)} PHI collections")
    masking_mode = "in-situ" if use_in_situ else "source-to-destination"
    logger.info(f"Using {masking_mode} masking mode")
    success_list = []
    failed_list = []

    masking_script_path = PROJECT_ROOT / "masking.py"
    
    # Include Dask parameters for parallel processing
    worker_count = 16  # Set to optimal value based on system resources
    threads_per_worker = 2  # Set to optimal value based on collection characteristics
    
    # Use the provided run log directory or create a new one
    if run_log_dir is None:
        base_log_dir = Path("C:/Users/demesew/logs/mask/PHI")
        run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_log_dir = base_log_dir / f"mask_parallel_{run_timestamp}"
        os.makedirs(run_log_dir, exist_ok=True)
    
    # Get the timestamp from the run directory name
    run_timestamp = run_log_dir.name.split('_')[-1]  # Extract timestamp from directory name
    daily_log_file = run_log_dir / f"mask_parallel_{run_timestamp}.log"
    
    logger.info(f"Multi-collection processing will be logged to: {daily_log_file}")

    for collection_name in batch:
        # Add a clear section divider for this collection in the log
        collection_header = f"\n{'=' * 80}\n== COLLECTION: {collection_name} | STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==\n{'=' * 80}\n"
        
        with open(daily_log_file, 'a') as log_file:
            log_file.write(collection_header)
            log_file.flush()
        
        logger.info(f"Processing PHI collection: {collection_name} ({masking_mode} mode)")
        
        # Use python3 explicitly with Dask parameters and optional in-situ masking
        command = [
            "python3",
            str(masking_script_path),
            "--collection", collection_name,
            "--config", config_path,
            "--env", env_path,
            "--use-dask",
            "--worker-count", str(worker_count),
            "--threads-per-worker", str(threads_per_worker)
        ]
        
        # Add in-situ flag if enabled
        if use_in_situ:
            command.append("--in-situ")
        
        # Log the full command being run
        cmd_str = ' '.join(command)
        logger.info(f"Running command: {cmd_str}")
        
        try:
            # Run the command and append output to the daily log file
            with open(daily_log_file, 'a') as log_file:
                # Set environment variable for the run log directory
                env = dict(os.environ, 
                          DASK_CONFIG="./dask_masker_config.yaml",
                          PHI_RUN_LOG_DIR=str(run_log_dir))
                
                process = subprocess.Popen(
                    command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout for chronological output
                    text=True,
                    bufsize=1,  # Line buffered for real-time output
                    env=env
                )
                
                # Stream and log output in real-time
                for line in process.stdout:
                    # Add collection name prefix to each line for better readability
                    formatted_line = f"[{collection_name}] {line}"
                    log_file.write(formatted_line)
                    log_file.flush()
                    
                    # Also log important lines to the main orchestration log
                    if any(important in line for important in ["ERROR", "Batch performance:", "documents processed", "worker", "scheduler", "Processing complete"]):
                        logger.info(f"{collection_name} | {line.strip()}")
                
                # Wait for process to complete
                return_code = process.wait()
                
                # Add completion status to the log
                completion_status = "SUCCESS" if return_code == 0 else f"FAILED (code: {return_code})"
                completion_footer = f"\n{'-' * 80}\n-- COLLECTION: {collection_name} | {completion_status} | COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --\n{'-' * 80}\n"
                log_file.write(completion_footer)
                log_file.flush()
                
                if return_code == 0:
                    logger.info(f"Successfully processed PHI collection: {collection_name}")
                    success_list.append(collection_name)
                else:
                    logger.error(f"Error processing PHI collection: {collection_name}. Return code: {return_code}")
                    failed_list.append(collection_name)
        except Exception as e:
            logger.error(f"Failed to execute masking script for {collection_name}: {str(e)}")
            failed_list.append(collection_name)

    return success_list, failed_list


def generate_optimized_batches(phi_collections, analysis_data=None, target_batch_time=60):
    """
    Generate optimized batches for PHI collection processing.
    If analysis data is available, use it to balance batches by processing time.
    
    Args:
        phi_collections: List of PHI collection names
        analysis_data: Collection analysis data (optional)
        target_batch_time: Target processing time per batch in minutes
        
    Returns:
        List of batches (each batch is a list of collection names)
    """
    if not analysis_data or "collection_details" not in analysis_data:
        # If no analysis data, create simple batches of 10 collections each
        logger.info("No analysis data available, creating simple batches")
        return [phi_collections[i:i+10] for i in range(0, len(phi_collections), 10)]
    
    # Use analysis data to create balanced batches
    logger.info("Creating optimized batches based on analysis data")
    
    # Get processing time estimates
    collection_times = []
    for collection in phi_collections:
        if collection in analysis_data["collection_details"]:
            est_time = analysis_data["collection_details"][collection].get("estimated_processing_time_mins", 10)
            collection_times.append((collection, est_time))
        else:
            # Default to 10 minutes if no estimate available
            collection_times.append((collection, 10))
    
    # Sort by processing time (descending)
    collection_times.sort(key=lambda x: x[1], reverse=True)
    
    # Create batches
    batches = []
    current_batch = []
    current_batch_time = 0
    
    for coll_name, est_time in collection_times:
        # If adding this collection would exceed target time and batch isn't empty,
        # finalize current batch and start a new one
        if current_batch_time + est_time > target_batch_time and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_batch_time = 0
        
        current_batch.append(coll_name)
        current_batch_time += est_time
    
    # Add the last batch if not empty
    if current_batch:
        batches.append(current_batch)
    
    logger.info(f"Created {len(batches)} optimized batches")
    return batches


def main():
    parser = argparse.ArgumentParser(description="Orchestrate the complete migration process")
    parser.add_argument('--config', default='config/config_rules/config.json', help='Path to configuration file')
    parser.add_argument('--env', default='.env.prod', help='Path to environment file')
    parser.add_argument('--skip-no-phi', action='store_true', help='Skip migration of no-PHI collections')
    parser.add_argument('--skip-phi', action='store_true', help='Skip migration of PHI collections')
    parser.add_argument('--skip-processed', action='store_true', help='Skip collections already processed in previous runs')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for document migration')
    parser.add_argument('--target-batch-time', type=int, default=60, help='Target processing time per batch in minutes')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--no-in-situ', action='store_true', help='Disable in-situ masking (use source->destination mode)')
    args = parser.parse_args()
    
    # Start time for tracking total migration time
    start_time = datetime.now()
    logger.info(f"Starting migration orchestration at {start_time}")
    
    # Log masking mode
    masking_mode = "source-to-destination" if args.no_in_situ else "in-situ"
    logger.info(f"PHI masking mode: {masking_mode}")
    if not args.no_in_situ:
        logger.info("Using in-situ masking for faster processing (modifies source collections directly)")
    else:
        logger.info("Using source-to-destination masking (copies data to destination collections)")
    
    # Load environment variables
    if os.path.exists(args.env):
        load_dotenv(args.env, override=True)
        logger.info(f"Loaded environment from {args.env}")
    else:
        logger.warning(f"Environment file {args.env} not found")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(args.config, args.env)
        config = config_loader.load_config()
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        sys.exit(1)
    
    # Load collection lists
    phi_collections, no_phi_collections = load_collections()
    
    # Load analysis data if available
    analysis_data = load_analysis()
    
    # Load checkpoint regardless of resume flag to get completed/failed lists
    checkpoint = load_checkpoint()
    
    # Track progress - initialize from checkpoint if it exists
    completed_collections = []
    failed_collections = []
    current_batch_info = None # Initialize current batch info
    
    if checkpoint:
        completed_collections = checkpoint.get("completed_collections", [])
        failed_collections = checkpoint.get("failed_collections", [])
        current_batch_info = checkpoint.get("current_batch", None) # Get batch info
        logger.info(f"Loaded checkpoint: {len(completed_collections)} completed, {len(failed_collections)} failed")
        if current_batch_info and current_batch_info.get("batch_index") is not None:
             logger.info(f"Checkpoint indicates potential resume point at batch index {current_batch_info.get('batch_index')}")
    else:
        logger.info("No checkpoint file found or it's empty.")

    # === Temporarily Skipping Non-PHI Migration ===
    logger.info("Skipping non-PHI collection migration as requested to focus on PHI.")
    # if not args.skip_no_phi:
    #     # Filter out already completed collections
    #     pending_no_phi = [c for c in no_phi_collections if c not in completed_collections and c not in failed_collections]
    #     
    #     if pending_no_phi:
    #         logger.info(f"Migrating {len(pending_no_phi)} pending no-PHI collections")
    #         success_count, new_failed = migrate_no_phi_collections(
    #             pending_no_phi, 
    #             args.config, 
    #             args.env,
    #             batch_size=args.batch_size
    #         )
    #         
    #         # Update progress based on results
    #         # Assume migrate_no_phi_collections returns lists of successfully processed and newly failed collections
    #         # For simplicity, let's assume it returns a list of newly_failed collections
    #         # And successful ones are those in pending_no_phi not in new_failed
    #         
    #         newly_completed = [c for c in pending_no_phi if c not in new_failed]
    #         completed_collections.extend(newly_completed)
    #         failed_collections.extend(new_failed)
    #         
    #         # Save checkpoint after processing non-PHI
    #         save_checkpoint(completed_collections, failed_collections, None) # Clear batch info after non-PHI step
    #     else:
    #         logger.info("No pending no-PHI collections to migrate based on checkpoint")
    # else:
    #     logger.info("Skipping no-PHI collections as requested")
    # === End of Skipped Non-PHI Section ===

    # Process PHI collections (unless skipped)
    if not args.skip_phi:
        # --- Original logic for skipping specific high-complexity collections ---
        # Skip these collections that have already been processed in previous runs (Manual list, could be removed if checkpoint handles all)
        # already_processed_manual = ["Container", "Patients", "SyncAcknowledgment"] # Example, can be managed purely by checkpoint now
        # logger.info(f"Manually skipping previously processed high-complexity collections: {', '.join(already_processed_manual)}")
        
        # Mark previously processed collections as completed (This might be redundant if checkpoint is loaded correctly)
        # for coll in already_processed_manual:
        #    if coll not in completed_collections and coll not in failed_collections:
        #        completed_collections.append(coll)
        #        logger.info(f"Marked {coll} as completed (previously processed manual list)")
        # --- End of original logic ---

        # Filter PHI collections based *only* on the loaded checkpoint's completed/failed lists
        pending_phi = [c for c in phi_collections 
                      if c not in completed_collections 
                      and c not in failed_collections]
        
        if pending_phi:
            # Check if resuming PHI batch processing
            start_batch_index = 0
            remaining_batches_from_checkpoint = []
            if args.resume and current_batch_info:
                 start_batch_index = current_batch_info.get("batch_index", 0)
                 remaining_batches_from_checkpoint = current_batch_info.get("remaining_batches", [])
                 logger.info(f"Attempting to resume PHI migration from batch index {start_batch_index}")
            else:
                 logger.info(f"Starting PHI migration for {len(pending_phi)} pending collections.")


            # Optimize and create batches only for pending PHI collections
            batches = generate_optimized_batches(
                pending_phi, 
                analysis_data, 
                target_batch_time=args.target_batch_time
            )
            
            if not batches:
                 logger.warning("No batches created for pending PHI collections.")
                 sys.exit(0) # Exit gracefully if no batches

            # If resuming, use the remaining batches from the checkpoint if available
            if args.resume and remaining_batches_from_checkpoint:
                 logger.info(f"Using {len(remaining_batches_from_checkpoint)} remaining batches from checkpoint.")
                 batches_to_process = remaining_batches_from_checkpoint
            else:
                # Otherwise, process batches starting from the calculated start index
                batches_to_process = batches[start_batch_index:]
                logger.info(f"Processing {len(batches_to_process)} batches starting from index {start_batch_index}.")

            total_phi_batches = len(batches_to_process)
            
            # Process PHI collections in batches
            for i, batch in enumerate(batches_to_process):
                current_batch_index_overall = start_batch_index + i
                logger.info(f"Processing PHI batch {current_batch_index_overall + 1}/{len(batches)} (Batch {i+1} of {total_phi_batches} in this run)")
                
                # Save checkpoint *before* starting the batch, including remaining batches
                remaining_batches_for_checkpoint = batches[current_batch_index_overall + 1:]
                batch_checkpoint_info = {
                    "batch_index": current_batch_index_overall,
                    "remaining_batches": remaining_batches_for_checkpoint
                }
                save_checkpoint(completed_collections, failed_collections, batch_checkpoint_info)

                success_list, fail_list = migrate_phi_collection_batch(
                    batch, 
                    args.config, 
                    args.env,
                    use_in_situ=not args.no_in_situ,  # Use in-situ unless explicitly disabled
                    run_log_dir=run_log_dir  # Pass the run log directory
                )
                
                # Update progress
                completed_collections.extend(success_list)
                failed_collections.extend(fail_list)
                
                # Save checkpoint *after* completing the batch, clearing remaining batches for this index
                save_checkpoint(completed_collections, failed_collections, None) # Clear batch info after successful batch completion

            logger.info("PHI collection migration completed.")
            
        else:
            logger.info("No pending PHI collections to migrate based on checkpoint.")
    else:
        logger.info("Skipping PHI collections as requested")
    
    # Calculate final statistics
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print summary
    logger.info(f"\nMigration Summary:")
    logger.info(f"Started at:  {start_time}")
    logger.info(f"Finished at: {end_time}")
    logger.info(f"Total duration: {duration}")
    logger.info(f"Collections successfully migrated: {len(completed_collections)}")
    logger.info(f"Collections failed: {len(failed_collections)}")
    
    if len(failed_collections) > 0:
        logger.info(f"Failed collections: {', '.join(failed_collections)}")
    
    # Final completion status
    total_collections = len(phi_collections) + len(no_phi_collections)
    if len(completed_collections) == total_collections:
        logger.info("Migration completed successfully!")
    else:
        completion_percentage = len(completed_collections) / total_collections * 100
        logger.info(f"Migration partially completed: {completion_percentage:.1f}%")


if __name__ == "__main__":
    main()
