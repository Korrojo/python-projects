import argparse
import glob
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def load_metrics_data(metrics_dir):
    """Load metrics data from CSV files.

    Args:
        metrics_dir: Directory containing metrics files

    Returns:
        Dictionary of DataFrames with metrics data
    """
    data = {}

    # Load batch stats
    batch_stats_files = glob.glob(os.path.join(metrics_dir, "batch_stats", "*.csv"))
    if batch_stats_files:
        batch_stats = []
        for file in batch_stats_files:
            try:
                df = pd.read_csv(file)
                batch_stats.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")

        if batch_stats:
            data["batch_stats"] = pd.concat(batch_stats)

    # Load system stats
    system_stats_files = glob.glob(os.path.join(metrics_dir, "system_stats", "*.csv"))
    if system_stats_files:
        system_stats = []
        for file in system_stats_files:
            try:
                df = pd.read_csv(file)
                system_stats.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")

        if system_stats:
            data["system_stats"] = pd.concat(system_stats)

    return data


def plot_throughput(batch_stats, output_dir):
    """Plot document processing throughput.

    Args:
        batch_stats: DataFrame with batch statistics
        output_dir: Directory to save plots
    """
    if "throughput" not in batch_stats.columns:
        print("Throughput data not available")
        return

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=batch_stats, x="timestamp", y="throughput")
    plt.title("Document Processing Throughput")
    plt.xlabel("Time")
    plt.ylabel("Documents per Second")
    plt.grid(True)

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "throughput.png"))
    plt.close()


def plot_resource_usage(system_stats, output_dir):
    """Plot system resource usage.

    Args:
        system_stats: DataFrame with system statistics
        output_dir: Directory to save plots
    """
    # Plot CPU usage
    if "cpu_percent" in system_stats.columns:
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=system_stats, x="timestamp", y="cpu_percent")
        plt.title("CPU Usage")
        plt.xlabel("Time")
        plt.ylabel("CPU Usage (%)")
        plt.grid(True)

        # Save plot
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, "cpu_usage.png"))
        plt.close()

    # Plot memory usage
    if "memory_percent" in system_stats.columns:
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=system_stats, x="timestamp", y="memory_percent")
        plt.title("Memory Usage")
        plt.xlabel("Time")
        plt.ylabel("Memory Usage (%)")
        plt.grid(True)

        # Save plot
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, "memory_usage.png"))
        plt.close()


def plot_batch_size_vs_throughput(batch_stats, output_dir):
    """Plot batch size vs throughput.

    Args:
        batch_stats: DataFrame with batch statistics
        output_dir: Directory to save plots
    """
    if "batch_size" not in batch_stats.columns or "throughput" not in batch_stats.columns:
        print("Batch size or throughput data not available")
        return

    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=batch_stats, x="batch_size", y="throughput")
    plt.title("Batch Size vs Throughput")
    plt.xlabel("Batch Size")
    plt.ylabel("Documents per Second")
    plt.grid(True)

    # Add trend line
    sns.regplot(data=batch_stats, x="batch_size", y="throughput", scatter=False, color="red")

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "batch_size_vs_throughput.png"))
    plt.close()


def plot_worker_count_vs_throughput(batch_stats, output_dir):
    """Plot worker count vs throughput.

    Args:
        batch_stats: DataFrame with batch statistics
        output_dir: Directory to save plots
    """
    if "worker_count" not in batch_stats.columns or "throughput" not in batch_stats.columns:
        print("Worker count or throughput data not available")
        return

    plt.figure(figsize=(12, 6))
    sns.boxplot(data=batch_stats, x="worker_count", y="throughput")
    plt.title("Worker Count vs Throughput")
    plt.xlabel("Worker Count")
    plt.ylabel("Documents per Second")
    plt.grid(True)

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "worker_count_vs_throughput.png"))
    plt.close()


def generate_performance_report(metrics_data, output_dir):
    """Generate performance report.

    Args:
        metrics_data: Dictionary containing metrics DataFrames
        output_dir: Directory to save the report
    """
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "performance_report.html")

    # Initialize HTML report
    report_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MongoPHIMasker Performance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #3498db; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .metric-value {{ font-weight: bold; }}
            .chart-container {{ margin: 20px 0; }}
            .chart-container img {{ max-width: 100%; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>MongoPHIMasker Performance Report</h1>
        <p>Generated on: {date}</p>
    """.format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Add performance summary
    report_html += "<h2>Performance Summary</h2>"

    if "batch_stats" in metrics_data:
        batch_stats = metrics_data["batch_stats"]

        # Calculate summary statistics
        total_docs = batch_stats["docs_processed"].sum() if "docs_processed" in batch_stats.columns else 0
        avg_throughput = batch_stats["throughput"].mean() if "throughput" in batch_stats.columns else 0
        max_throughput = batch_stats["throughput"].max() if "throughput" in batch_stats.columns else 0

        # Create summary table
        report_html += f"""
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Documents Processed</td>
                <td class="metric-value">{total_docs}</td>
            </tr>
            <tr>
                <td>Average Throughput</td>
                <td class="metric-value">{avg_throughput:.2f} docs/sec</td>
            </tr>
            <tr>
                <td>Maximum Throughput</td>
                <td class="metric-value">{max_throughput:.2f} docs/sec</td>
            </tr>
        </table>
        """

    # Add system resource usage summary
    if "system_stats" in metrics_data:
        system_stats = metrics_data["system_stats"]

        # Calculate summary statistics
        avg_cpu = system_stats["cpu_percent"].mean() if "cpu_percent" in system_stats.columns else 0
        max_cpu = system_stats["cpu_percent"].max() if "cpu_percent" in system_stats.columns else 0
        avg_memory = system_stats["memory_percent"].mean() if "memory_percent" in system_stats.columns else 0
        max_memory = system_stats["memory_percent"].max() if "memory_percent" in system_stats.columns else 0

        # Create summary table
        report_html += f"""
        <h2>Resource Usage Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Average</th>
                <th>Maximum</th>
            </tr>
            <tr>
                <td>CPU Usage</td>
                <td class="metric-value">{avg_cpu:.2f}%</td>
                <td class="metric-value">{max_cpu:.2f}%</td>
            </tr>
            <tr>
                <td>Memory Usage</td>
                <td class="metric-value">{avg_memory:.2f}%</td>
                <td class="metric-value">{max_memory:.2f}%</td>
            </tr>
        </table>
        """

    # Add batch size analysis
    if "batch_stats" in metrics_data and "batch_size" in metrics_data["batch_stats"].columns:
        report_html += """
        <h2>Batch Size Analysis</h2>
        <div class="chart-container">
            <img src="batch_size_vs_throughput.png" alt="Batch Size vs Throughput">
        </div>
        """

        # Calculate optimal batch size
        batch_stats = metrics_data["batch_stats"]
        if "batch_size" in batch_stats.columns and "throughput" in batch_stats.columns:
            # Group by batch size and calculate average throughput
            batch_throughput = batch_stats.groupby("batch_size")["throughput"].mean().reset_index()
            optimal_batch_size = batch_throughput.loc[batch_throughput["throughput"].idxmax(), "batch_size"]

            report_html += f"""
            <p><strong>Optimal Batch Size:</strong> {optimal_batch_size} documents</p>
            """

    # Add worker count analysis
    if "batch_stats" in metrics_data and "worker_count" in metrics_data["batch_stats"].columns:
        report_html += """
        <h2>Worker Count Analysis</h2>
        <div class="chart-container">
            <img src="worker_count_vs_throughput.png" alt="Worker Count vs Throughput">
        </div>
        """

        # Calculate optimal worker count
        batch_stats = metrics_data["batch_stats"]
        if "worker_count" in batch_stats.columns and "throughput" in batch_stats.columns:
            # Group by worker count and calculate average throughput
            worker_throughput = batch_stats.groupby("worker_count")["throughput"].mean().reset_index()
            optimal_worker_count = worker_throughput.loc[worker_throughput["throughput"].idxmax(), "worker_count"]

            report_html += f"""
            <p><strong>Optimal Worker Count:</strong> {optimal_worker_count} workers</p>
            """

    # Add throughput analysis
    report_html += """
    <h2>Throughput Analysis</h2>
    <div class="chart-container">
        <img src="throughput.png" alt="Document Processing Throughput">
    </div>
    """

    # Add resource usage analysis
    report_html += """
    <h2>Resource Usage Analysis</h2>
    <div class="chart-container">
        <img src="cpu_usage.png" alt="CPU Usage">
    </div>
    <div class="chart-container">
        <img src="memory_usage.png" alt="Memory Usage">
    </div>
    """

    # Add recommendations
    report_html += """
    <h2>Performance Recommendations</h2>
    <ul>
    """

    # Add batch size recommendation
    if "batch_stats" in metrics_data and "batch_size" in metrics_data["batch_stats"].columns:
        batch_stats = metrics_data["batch_stats"]
        if "batch_size" in batch_stats.columns and "throughput" in batch_stats.columns:
            # Group by batch size and calculate average throughput
            batch_throughput = batch_stats.groupby("batch_size")["throughput"].mean().reset_index()
            optimal_batch_size = batch_throughput.loc[batch_throughput["throughput"].idxmax(), "batch_size"]

            report_html += f"""
            <li><strong>Batch Size:</strong> Use a batch size of {optimal_batch_size} documents for optimal throughput.</li>
            """

    # Add worker count recommendation
    if "batch_stats" in metrics_data and "worker_count" in metrics_data["batch_stats"].columns:
        batch_stats = metrics_data["batch_stats"]
        if "worker_count" in batch_stats.columns and "throughput" in batch_stats.columns:
            # Group by worker count and calculate average throughput
            worker_throughput = batch_stats.groupby("worker_count")["throughput"].mean().reset_index()
            optimal_worker_count = worker_throughput.loc[worker_throughput["throughput"].idxmax(), "worker_count"]

            report_html += f"""
            <li><strong>Worker Count:</strong> Use {optimal_worker_count} workers for optimal throughput.</li>
            """

    # Add resource usage recommendation
    if "system_stats" in metrics_data:
        system_stats = metrics_data["system_stats"]
        if "cpu_percent" in system_stats.columns:
            avg_cpu = system_stats["cpu_percent"].mean()
            max_cpu = system_stats["cpu_percent"].max()

            if max_cpu > 90:
                report_html += f"""
                <li><strong>CPU Usage:</strong> CPU usage peaked at {max_cpu:.2f}%, which may indicate resource constraints. Consider using a machine with more CPU cores or adjusting the worker count.</li>
                """
            elif avg_cpu < 50:
                report_html += f"""
                <li><strong>CPU Usage:</strong> Average CPU usage was only {avg_cpu:.2f}%, which suggests that the system is not fully utilizing available resources. Consider increasing the batch size or worker count.</li>
                """

        if "memory_percent" in system_stats.columns:
            avg_memory = system_stats["memory_percent"].mean()
            max_memory = system_stats["memory_percent"].max()

            if max_memory > 90:
                report_html += f"""
                <li><strong>Memory Usage:</strong> Memory usage peaked at {max_memory:.2f}%, which may indicate memory constraints. Consider using a machine with more memory or adjusting the batch size.</li>
                """

    report_html += """
    </ul>
    """

    # Close HTML document
    report_html += """
    </body>
    </html>
    """

    # Write report to file
    with open(report_path, "w") as f:
        f.write(report_html)

    print(f"Performance report generated: {report_path}")

    return report_path


def create_example_data(output_dir, num_samples=100):
    """Create example metrics data for testing.

    Args:
        output_dir: Directory to save example data
        num_samples: Number of data points to generate
    """
    # Create directories
    batch_stats_dir = os.path.join(output_dir, "batch_stats")
    system_stats_dir = os.path.join(output_dir, "system_stats")
    os.makedirs(batch_stats_dir, exist_ok=True)
    os.makedirs(system_stats_dir, exist_ok=True)

    # Generate timestamps
    timestamps = pd.date_range(start="2023-01-01", periods=num_samples, freq="1min")

    # Generate batch stats
    batch_sizes = np.random.choice([100, 500, 1000, 2000, 5000], num_samples)
    worker_counts = np.random.choice([2, 4, 8, 16], num_samples)
    # Throughput model: higher with larger batch sizes, but with diminishing returns
    throughput = 100 + 0.1 * batch_sizes * np.sqrt(worker_counts) + np.random.normal(0, 50, num_samples)
    throughput = np.maximum(10, throughput)  # Ensure positive throughput

    batch_stats = pd.DataFrame(
        {
            "timestamp": timestamps,
            "batch_size": batch_sizes,
            "worker_count": worker_counts,
            "docs_processed": batch_sizes,
            "docs_with_errors": np.random.randint(0, 10, num_samples),
            "throughput": throughput,
            "elapsed_seconds": batch_sizes / throughput,
        }
    )

    batch_stats_file = os.path.join(batch_stats_dir, "batch_stats.csv")
    batch_stats.to_csv(batch_stats_file, index=False)
    print(f"Example batch stats created: {batch_stats_file}")

    # Generate system stats
    # CPU usage model: higher with more workers and throughput
    cpu_percent = 20 + 0.01 * throughput + 2 * np.sqrt(worker_counts) + np.random.normal(0, 5, num_samples)
    cpu_percent = np.clip(cpu_percent, 5, 100)  # Bound between 5-100%

    # Memory usage model: increases with batch size
    memory_percent = 30 + 0.005 * batch_sizes + np.random.normal(0, 3, num_samples)
    memory_percent = np.clip(memory_percent, 10, 100)  # Bound between 10-100%

    system_stats = pd.DataFrame(
        {
            "timestamp": timestamps,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_read_bytes": np.random.randint(1000, 10000, num_samples),
            "disk_write_bytes": np.random.randint(1000, 10000, num_samples),
        }
    )

    system_stats_file = os.path.join(system_stats_dir, "system_stats.csv")
    system_stats.to_csv(system_stats_file, index=False)
    print(f"Example system stats created: {system_stats_file}")

    return {"batch_stats": batch_stats, "system_stats": system_stats}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize performance metrics for MongoPHIMasker")
    parser.add_argument("--metrics-dir", default="metrics", help="Directory containing metrics data")
    parser.add_argument(
        "--output-dir", default="reports/performance", help="Directory to save visualizations and report"
    )
    parser.add_argument("--create-example", action="store_true", help="Create example metrics data for testing")
    parser.add_argument("--example-samples", type=int, default=100, help="Number of samples to create for example data")

    args = parser.parse_args()

    # Create example data if requested
    if args.create_example:
        metrics_data = create_example_data(args.metrics_dir, args.example_samples)
    else:
        # Load metrics data
        metrics_data = load_metrics_data(args.metrics_dir)

    if not metrics_data:
        print("No metrics data found")
        exit(1)

    print("Generating visualizations...")

    # Create visualizations
    if "batch_stats" in metrics_data:
        plot_throughput(metrics_data["batch_stats"], args.output_dir)
        plot_batch_size_vs_throughput(metrics_data["batch_stats"], args.output_dir)
        plot_worker_count_vs_throughput(metrics_data["batch_stats"], args.output_dir)

    if "system_stats" in metrics_data:
        plot_resource_usage(metrics_data["system_stats"], args.output_dir)

    # Generate performance report
    report_path = generate_performance_report(metrics_data, args.output_dir)

    print(f"Visualizations and report saved to: {args.output_dir}")
    print(f"Open {report_path} in a web browser to view the performance report")
