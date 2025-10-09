"""
Report generation service for creating comprehensive test reports.

Provides HTML report generation with statistics, charts, and detailed
test result analysis.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..core.config import ConfigurationManager


class ReportGenerator:
    """
    Base class for report generation.
    
    Provides common functionality for generating different types of reports.
    """
    
    def __init__(self, 
                 config_manager: ConfigurationManager,
                 logger: logging.Logger):
        """
        Initialize report generator.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
        self.path_config = config_manager.path_config
    
    def calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics from test results.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary containing calculated statistics
        """
        if not results:
            return {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "status_code_distribution": {},
                "error_distribution": {}
            }
        
        # Basic counts
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Response time statistics
        response_times = [r.get('response_time', 0) for r in results if r.get('response_time') is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Status code distribution
        status_codes = {}
        for result in results:
            status_code = result.get('status_code')
            if status_code:
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
        
        # Error distribution
        errors = {}
        for result in results:
            if not result.get('success', False) and result.get('error_message'):
                error_type = result['error_message'].split(':')[0]  # Get error type
                errors[error_type] = errors.get(error_type, 0) + 1
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "average_response_time": round(avg_response_time, 3),
            "min_response_time": round(min_response_time, 3),
            "max_response_time": round(max_response_time, 3),
            "status_code_distribution": status_codes,
            "error_distribution": errors
        }


class HTMLReportGenerator(ReportGenerator):
    """
    HTML report generator for creating comprehensive test reports.
    
    Generates detailed HTML reports with statistics, charts, and
    individual test result details.
    """
    
    def generate_report(self, 
                       results: List[Dict[str, Any]], 
                       run_id: str,
                       output_folder: Path) -> Path:
        """
        Generate comprehensive HTML test report.
        
        Args:
            results: List of test results
            run_id: Test run identifier
            output_folder: Output folder for the report
            
        Returns:
            Path to generated report file
        """
        try:
            self.logger.info(f"Generating HTML report for run {run_id}")
            
            # Calculate statistics
            stats = self.calculate_statistics(results)
            
            # Generate HTML content
            html_content = self._generate_html_content(results, run_id, stats)
            
            # Save report
            report_file = output_folder / f"test_report_{run_id}.html"
            with open(report_file, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            self.logger.info(f"HTML report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise RuntimeError(f"Failed to generate HTML report: {e}") from e
    
    def _generate_html_content(self, 
                              results: List[Dict[str, Any]], 
                              run_id: str,
                              stats: Dict[str, Any]) -> str:
        """Generate complete HTML content for the report."""
        
        # HTML template with embedded CSS and JavaScript
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Report - Run {run_id}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {self._generate_header(run_id)}
        {self._generate_summary(stats)}
        {self._generate_charts(stats)}
        {self._generate_detailed_results(results)}
    </div>
    <script>
        {self._generate_javascript(stats)}
    </script>
</body>
</html>
"""
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .info { color: #3498db; }
        
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .chart-title {
            font-size: 1.3em;
            margin-bottom: 20px;
            text-align: center;
            color: #333;
        }
        
        .results-table {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .table-header {
            background: #34495e;
            color: white;
            padding: 20px;
            font-size: 1.3em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .status-success {
            color: #27ae60;
            font-weight: bold;
        }
        
        .status-failed {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .response-time {
            font-family: monospace;
        }
        
        .error-message {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .summary {
                grid-template-columns: 1fr;
            }
            
            .charts {
                grid-template-columns: 1fr;
            }
            
            table {
                font-size: 0.9em;
            }
        }
        """
    
    def _generate_header(self, run_id: str) -> str:
        """Generate header section."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <div class="header">
            <h1>API Test Report</h1>
            <p>Run ID: {run_id} | Generated: {timestamp}</p>
        </div>
        """
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """Generate summary statistics section."""
        return f"""
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value info">{stats['total_tests']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value success">{stats['successful_tests']}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-value error">{stats['failed_tests']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'success' if stats['success_rate'] >= 95 else 'warning' if stats['success_rate'] >= 80 else 'error'}">{stats['success_rate']}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value info">{stats['average_response_time']}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
        </div>
        """
    
    def _generate_charts(self, stats: Dict[str, Any]) -> str:
        """Generate charts section."""
        return f"""
        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">Test Results Distribution</div>
                <canvas id="resultsChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Status Code Distribution</div>
                <canvas id="statusChart" width="400" height="200"></canvas>
            </div>
        </div>
        """
    
    def _generate_detailed_results(self, results: List[Dict[str, Any]]) -> str:
        """Generate detailed results table."""
        table_rows = ""
        
        for result in results:
            status_class = "status-success" if result.get('success', False) else "status-failed"
            status_text = "SUCCESS" if result.get('success', False) else "FAILED"
            response_time = f"{result.get('response_time', 0):.3f}s" if result.get('response_time') else "N/A"
            status_code = result.get('status_code', 'N/A')
            error_message = result.get('error_message', '') or ''
            
            table_rows += f"""
            <tr>
                <td>{result.get('file_name', 'Unknown')}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{status_code}</td>
                <td class="response-time">{response_time}</td>
                <td class="error-message" title="{error_message}">{error_message}</td>
            </tr>
            """
        
        return f"""
        <div class="results-table">
            <div class="table-header">Detailed Test Results</div>
            <table>
                <thead>
                    <tr>
                        <th>Test File</th>
                        <th>Status</th>
                        <th>Status Code</th>
                        <th>Response Time</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_javascript(self, stats: Dict[str, Any]) -> str:
        """Generate JavaScript for charts."""
        status_codes = stats.get('status_code_distribution', {})
        status_labels = list(status_codes.keys())
        status_values = list(status_codes.values())
        
        return f"""
        // Results distribution chart
        const resultsCtx = document.getElementById('resultsChart').getContext('2d');
        new Chart(resultsCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Successful', 'Failed'],
                datasets: [{{
                    data: [{stats['successful_tests']}, {stats['failed_tests']}],
                    backgroundColor: ['#27ae60', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Status code distribution chart
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(status_labels)},
                datasets: [{{
                    label: 'Count',
                    data: {json.dumps(status_values)},
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        """


class ReportService:
    """
    High-level service for report generation.
    
    Orchestrates different report generators and provides
    a unified interface for report creation.
    """
    
    def __init__(self, 
                 config_manager: ConfigurationManager,
                 logger: logging.Logger):
        """
        Initialize report service.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
        
        # Initialize report generators
        self.html_generator = HTMLReportGenerator(config_manager, logger)
    
    def generate_html_report(self, 
                           results: List[Dict[str, Any]], 
                           run_id: str,
                           output_folder: Path) -> Path:
        """
        Generate HTML test report.
        
        Args:
            results: List of test results
            run_id: Test run identifier
            output_folder: Output folder for the report
            
        Returns:
            Path to generated report file
        """
        return self.html_generator.generate_report(results, run_id, output_folder)