"""
Multi-format report generation service with HTML, JSON, and Excel output.

This service provides:
- HTML reports with interactive visualizations
- JSON reports for programmatic access
- Excel reports with formatted data
- Statistical analysis and charts
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
from jinja2 import Template

from apitesting.config.settings import get_config
from apitesting.core.constants import (
    HTML_REPORT_NAME,
    JSON_REPORT_NAME,
    EXCEL_REPORT_NAME,
    ERROR_KEYWORDS,
    REPORT_PRIMARY_COLOR,
    REPORT_SUCCESS_COLOR,
    REPORT_ERROR_COLOR,
    REPORT_WARNING_COLOR
)
from apitesting.core.exceptions import ReportGenerationError
from apitesting.core.models import (
    RequestResult,
    BatchRequestResult,
    TestStatistics,
    StatusCodeDistribution,
    TestReport,
    ExecutionStatus
)
from apitesting.utils.file_handler import FileHandler, JSONHandler, ExcelHandler
from apitesting.utils.logger import get_logger, PerformanceLogger


class StatisticsCalculator:
    """
    Calculates test execution statistics and metrics.
    """
    
    @staticmethod
    def calculate_statistics(results: List[RequestResult]) -> TestStatistics:
        """
        Calculate comprehensive statistics from test results.
        
        Args:
            results: List of request results
            
        Returns:
            TestStatistics with calculated metrics
        """
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Calculate success rate
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        # Response time statistics
        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        max_response_time = max(response_times) if response_times else 0.0
        min_response_time = min(response_times) if response_times else 0.0
        total_execution_time = sum(response_times)
        
        # Status code distribution
        status_code_counts: Dict[int, int] = {}
        for result in results:
            if result.status_code:
                status_code_counts[result.status_code] = status_code_counts.get(result.status_code, 0) + 1
        
        status_code_distribution = [
            StatusCodeDistribution(
                status_code=code,
                count=count,
                percentage=(count / total_tests * 100) if total_tests > 0 else 0.0
            )
            for code, count in sorted(status_code_counts.items())
        ]
        
        # Count errors in responses
        error_count = sum(
            1 for r in results
            if r.error_message or any(keyword in r.response_text for keyword in ERROR_KEYWORDS)
        )
        
        return TestStatistics(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            total_execution_time=total_execution_time,
            status_code_distribution=status_code_distribution,
            error_count=error_count
        )


class HTMLReportGenerator:
    """
    Generates interactive HTML reports with visualizations.
    """
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Report - Run {{ run_id }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, {{ primary_color }} 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header-info {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-left: 5px solid {{ primary_color }};
            padding-left: 15px;
            font-weight: 600;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, {{ primary_color }} 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card.success {
            background: linear-gradient(135deg, {{ success_color }} 0%, #45a049 100%);
        }
        
        .stat-card.error {
            background: linear-gradient(135deg, {{ error_color }} 0%, #da190b 100%);
        }
        
        .stat-card.warning {
            background: linear-gradient(135deg, {{ warning_color }} 0%, #f57c00 100%);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        
        th {
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
            padding: 15px;
            text-align: left;
            border-bottom: 2px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .status-success {
            color: {{ success_color }};
            font-weight: bold;
        }
        
        .status-error {
            color: {{ error_color }};
            font-weight: bold;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-success {
            background: {{ success_color }};
            color: white;
        }
        
        .badge-error {
            background: {{ error_color }};
            color: white;
        }
        
        .response-preview {
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #666;
        }
        
        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .progress-bar {
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, {{ success_color }}, #45a049);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 1s ease;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Test Report</h1>
            <div class="header-info">
                <strong>Run ID:</strong> {{ run_id }} | 
                <strong>Generated:</strong> {{ timestamp }} |
                <strong>Duration:</strong> {{ duration }}
            </div>
        </div>
        
        <div class="content">
            <!-- Summary Statistics -->
            <div class="section">
                <h2 class="section-title">📊 Test Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.total_tests }}</div>
                        <div class="stat-label">Total Tests</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-value">{{ stats.successful_tests }}</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat-card error">
                        <div class="stat-value">{{ stats.failed_tests }}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-value">{{ "%.1f"|format(stats.success_rate) }}%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ "%.2f"|format(stats.avg_response_time) }}s</div>
                        <div class="stat-label">Avg Response Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.error_count }}</div>
                        <div class="stat-label">Errors Detected</div>
                    </div>
                </div>
                
                <!-- Success Rate Progress Bar -->
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ stats.success_rate }}%">
                        {{ "%.1f"|format(stats.success_rate) }}% Success Rate
                    </div>
                </div>
            </div>
            
            <!-- Status Code Distribution -->
            <div class="section">
                <h2 class="section-title">📈 Status Code Distribution</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Status Code</th>
                            <th>Count</th>
                            <th>Percentage</th>
                            <th>Category</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for dist in stats.status_code_distribution %}
                        <tr>
                            <td class="{% if 200 <= dist.status_code < 300 %}status-success{% else %}status-error{% endif %}">
                                {{ dist.status_code }}
                            </td>
                            <td>{{ dist.count }}</td>
                            <td>{{ "%.1f"|format(dist.percentage) }}%</td>
                            <td>
                                <span class="badge {% if 200 <= dist.status_code < 300 %}badge-success{% else %}badge-error{% endif %}">
                                    {% if 200 <= dist.status_code < 300 %}Success
                                    {% elif 400 <= dist.status_code < 500 %}Client Error
                                    {% elif 500 <= dist.status_code < 600 %}Server Error
                                    {% else %}Other{% endif %}
                                </span>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Detailed Results -->
            <div class="section">
                <h2 class="section-title">📋 Detailed Test Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test File</th>
                            <th>Status Code</th>
                            <th>Response Time</th>
                            <th>Result</th>
                            <th>Response Preview</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in results %}
                        <tr>
                            <td>{{ result.file_name }}</td>
                            <td class="{% if result.success %}status-success{% else %}status-error{% endif %}">
                                {{ result.status_code if result.status_code else 'N/A' }}
                            </td>
                            <td>{{ "%.2f"|format(result.response_time) }}s</td>
                            <td>
                                <span class="badge {% if result.success %}badge-success{% else %}badge-error{% endif %}">
                                    {% if result.success %}✓ Success{% else %}✗ Failed{% endif %}
                                </span>
                            </td>
                            <td class="response-preview" title="{{ result.response_preview }}">
                                {{ result.response_preview }}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Error Analysis -->
            {% if error_results %}
            <div class="section">
                <h2 class="section-title">⚠️ Error Analysis</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test File</th>
                            <th>Status Code</th>
                            <th>Error Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in error_results %}
                        <tr>
                            <td>{{ result.file_name }}</td>
                            <td class="status-error">{{ result.status_code if result.status_code else 'N/A' }}</td>
                            <td>{{ result.error_details }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="section">
                <h2 class="section-title">✅ No Errors Detected</h2>
                <p style="text-align: center; font-size: 1.2em; color: {{ success_color }};">
                    All tests completed without errors! 🎉
                </p>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            Generated by API Testing Framework | {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize HTML report generator.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
    
    def generate_html_report(
        self,
        report: TestReport,
        output_file: Path
    ) -> Path:
        """
        Generate HTML report.
        
        Args:
            report: Test report data
            output_file: Output file path
            
        Returns:
            Path to generated HTML file
            
        Raises:
            ReportGenerationError: If generation fails
        """
        try:
            # Prepare template data
            template_data = {
                'run_id': report.run_id,
                'timestamp': report.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': self._format_duration(report.duration),
                'stats': report.statistics,
                'results': self._prepare_results_for_html(report.results),
                'error_results': self._prepare_error_results(report.results),
                'primary_color': REPORT_PRIMARY_COLOR,
                'success_color': REPORT_SUCCESS_COLOR,
                'error_color': REPORT_ERROR_COLOR,
                'warning_color': REPORT_WARNING_COLOR
            }
            
            # Render template
            template = Template(self.HTML_TEMPLATE)
            html_content = template.render(**template_data)
            
            # Write to file
            FileHandler.write_text_file(output_file, html_content)
            
            self.logger.info(f"HTML report generated: {output_file}")
            return output_file
            
        except Exception as e:
            raise ReportGenerationError(
                "Failed to generate HTML report",
                report_type="HTML",
                output_path=str(output_file),
                original_error=e
            )
    
    def _prepare_results_for_html(self, results: List[RequestResult]) -> List[Dict[str, Any]]:
        """Prepare results for HTML template."""
        prepared = []
        for result in results:
            preview = result.error_message if result.error_message else result.response_text
            if len(preview) > self.config.reports.preview_length:
                preview = preview[:self.config.reports.preview_length] + '...'
            
            prepared.append({
                'file_name': Path(result.file_path).name,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'success': result.success,
                'response_preview': preview
            })
        return prepared
    
    def _prepare_error_results(self, results: List[RequestResult]) -> List[Dict[str, Any]]:
        """Prepare error results for HTML template."""
        error_results = []
        for result in results:
            if not result.success or result.error_message:
                error_details = result.error_message or result.response_text[:200] + '...'
                error_results.append({
                    'file_name': Path(result.file_path).name,
                    'status_code': result.status_code,
                    'error_details': error_details
                })
        return error_results
    
    def _format_duration(self, duration: float) -> str:
        """Format duration in human-readable format."""
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class ReportService:
    """
    Main service for generating test reports in multiple formats.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize report service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
        self.stats_calculator = StatisticsCalculator()
        self.html_generator = HTMLReportGenerator(self.logger)
    
    def generate_reports(
        self,
        results: List[RequestResult],
        run_id: str,
        output_folder: Path,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Path]:
        """
        Generate reports in all configured formats.
        
        Args:
            results: List of request results
            run_id: Unique run identifier
            output_folder: Output folder for reports
            start_time: Test start time
            end_time: Test end time
            
        Returns:
            Dictionary mapping format names to file paths
            
        Raises:
            ReportGenerationError: If report generation fails
        """
        try:
            with PerformanceLogger(self.logger, "Generate Test Reports"):
                # Ensure output folder exists
                FileHandler.ensure_directory(output_folder)
                
                # Calculate statistics
                statistics = self.stats_calculator.calculate_statistics(results)
                
                # Determine execution status
                if statistics.failed_tests == 0:
                    status = ExecutionStatus.SUCCESS
                elif statistics.successful_tests == 0:
                    status = ExecutionStatus.FAILED
                else:
                    status = ExecutionStatus.PARTIAL
                
                # Create test report
                test_report = TestReport(
                    run_id=run_id,
                    execution_status=status,
                    statistics=statistics,
                    results=results,
                    start_time=start_time,
                    end_time=end_time,
                    configuration=self.config.to_dict()
                )
                
                generated_reports = {}
                
                # Generate HTML report
                if self.config.reports.html_enabled:
                    html_file = output_folder / HTML_REPORT_NAME
                    self.html_generator.generate_html_report(test_report, html_file)
                    generated_reports['html'] = html_file
                
                # Generate JSON report
                if self.config.reports.json_enabled:
                    json_file = output_folder / JSON_REPORT_NAME
                    self._generate_json_report(test_report, json_file)
                    generated_reports['json'] = json_file
                
                # Generate Excel report
                if self.config.reports.excel_enabled:
                    excel_file = output_folder / EXCEL_REPORT_NAME
                    self._generate_excel_report(test_report, excel_file)
                    generated_reports['excel'] = excel_file
                
                self.logger.info(
                    f"Generated {len(generated_reports)} report(s): {', '.join(generated_reports.keys())}"
                )
                
                return generated_reports
                
        except Exception as e:
            if isinstance(e, ReportGenerationError):
                raise
            raise ReportGenerationError(
                "Failed to generate reports",
                report_type="multiple",
                output_path=str(output_folder),
                original_error=e
            )
    
    def _generate_json_report(self, report: TestReport, output_file: Path) -> None:
        """Generate JSON report."""
        try:
            report_dict = report.model_dump(mode='json')
            JSONHandler.write_json(output_file, report_dict, indent=2)
            self.logger.info(f"JSON report generated: {output_file}")
        except Exception as e:
            raise ReportGenerationError(
                "Failed to generate JSON report",
                report_type="JSON",
                output_path=str(output_file),
                original_error=e
            )
    
    def _generate_excel_report(self, report: TestReport, output_file: Path) -> None:
        """Generate Excel report with multiple sheets."""
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': [
                        'Run ID',
                        'Execution Status',
                        'Total Tests',
                        'Successful Tests',
                        'Failed Tests',
                        'Success Rate (%)',
                        'Avg Response Time (s)',
                        'Max Response Time (s)',
                        'Min Response Time (s)',
                        'Total Execution Time (s)',
                        'Errors Detected',
                        'Start Time',
                        'End Time',
                        'Duration (s)'
                    ],
                    'Value': [
                        report.run_id,
                        report.execution_status,
                        report.statistics.total_tests,
                        report.statistics.successful_tests,
                        report.statistics.failed_tests,
                        f"{report.statistics.success_rate:.2f}",
                        f"{report.statistics.avg_response_time:.2f}",
                        f"{report.statistics.max_response_time:.2f}",
                        f"{report.statistics.min_response_time:.2f}",
                        f"{report.statistics.total_execution_time:.2f}",
                        report.statistics.error_count,
                        report.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        report.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        f"{report.duration:.2f}"
                    ]
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed results sheet
                results_data = []
                for result in report.results:
                    results_data.append({
                        'File Name': Path(result.file_path).name,
                        'Status Code': result.status_code if result.status_code else 'N/A',
                        'Success': 'Yes' if result.success else 'No',
                        'Response Time (s)': f"{result.response_time:.2f}",
                        'Timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'Error Message': result.error_message or ''
                    })
                df_results = pd.DataFrame(results_data)
                df_results.to_excel(writer, sheet_name='Detailed Results', index=False)
                
                # Status code distribution sheet
                status_data = []
                for dist in report.statistics.status_code_distribution:
                    status_data.append({
                        'Status Code': dist.status_code,
                        'Count': dist.count,
                        'Percentage': f"{dist.percentage:.2f}"
                    })
                df_status = pd.DataFrame(status_data)
                df_status.to_excel(writer, sheet_name='Status Codes', index=False)
            
            self.logger.info(f"Excel report generated: {output_file}")
            
        except Exception as e:
            raise ReportGenerationError(
                "Failed to generate Excel report",
                report_type="Excel",
                output_path=str(output_file),
                original_error=e
            )