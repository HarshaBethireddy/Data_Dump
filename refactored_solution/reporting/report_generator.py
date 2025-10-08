"""
Enhanced report generation with better formatting and analysis.
"""
import os
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

from ..api_client.http_client import RequestResult
from ..utils.logger import framework_logger


class HTMLReportGenerator:
    """Generates comprehensive HTML reports for test results."""
    
    def __init__(self, report_folder: str):
        self.report_folder = report_folder
        self.logger = framework_logger.get_logger()
    
    def generate_report(self, results: List[RequestResult], run_id: int) -> str:
        """Generate a comprehensive HTML report."""
        try:
            report_file = os.path.join(self.report_folder, "test_report.html")
            
            # Calculate statistics
            stats = self._calculate_statistics(results)
            
            # Generate HTML content
            html_content = self._generate_html_content(results, stats, run_id)
            
            # Write to file
            with open(report_file, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            self.logger.info(f"HTML report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    def _calculate_statistics(self, results: List[RequestResult]) -> Dict[str, Any]:
        """Calculate test execution statistics."""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Response time statistics
        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Status code distribution
        status_codes = {}
        for result in results:
            if result.status_code:
                status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        
        # Error analysis
        error_responses = []
        for result in results:
            if not result.success or self._has_error_in_response(result.response_text):
                error_responses.append(result)
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'status_codes': status_codes,
            'error_responses': error_responses
        }
    
    def _has_error_in_response(self, response_text: str) -> bool:
        """Check if response contains error indicators."""
        if not response_text:
            return False
        
        error_indicators = ['ERROR', 'Error', 'error', 'FAIL', 'fail', 'exception', 'Exception']
        return any(indicator in response_text for indicator in error_indicators)
    
    def _generate_html_content(self, results: List[RequestResult], stats: Dict[str, Any], run_id: int) -> str:
        """Generate the complete HTML content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Report - Run {run_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .success {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); }}
        .error {{ background: linear-gradient(135deg, #f44336 0%, #da190b 100%); }}
        .warning {{ background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-success {{ color: #4CAF50; font-weight: bold; }}
        .status-error {{ color: #f44336; font-weight: bold; }}
        .response-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .expandable {{
            cursor: pointer;
            color: #1976d2;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>API Test Report</h1>
            <p><strong>Run ID:</strong> {run_id} | <strong>Generated:</strong> {timestamp}</p>
        </div>
        
        <div class="section">
            <h2 class="section-title">Test Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{stats['total_tests']}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{stats['successful_tests']}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat-card error">
                    <div class="stat-value">{stats['failed_tests']}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-value">{stats['success_rate']:.1f}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['avg_response_time']:.2f}s</div>
                    <div class="stat-label">Avg Response Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(stats['error_responses'])}</div>
                    <div class="stat-label">Error Responses</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Status Code Distribution</h2>
            <table>
                <thead>
                    <tr>
                        <th>Status Code</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add status code distribution
        for status_code, count in sorted(stats['status_codes'].items()):
            percentage = (count / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
            status_class = "status-success" if 200 <= status_code < 300 else "status-error"
            html += f"""
                    <tr>
                        <td class="{status_class}">{status_code}</td>
                        <td>{count}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">Detailed Test Results</h2>
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
"""
        
        # Add detailed results
        for result in results:
            filename = os.path.basename(result.file_path)
            status_display = result.status_code if result.status_code else "N/A"
            status_class = "status-success" if result.success else "status-error"
            result_text = "✓ Success" if result.success else "✗ Failed"
            
            # Prepare response preview
            if result.error_message:
                response_preview = result.error_message
            elif result.response_text:
                response_preview = result.response_text[:100] + "..." if len(result.response_text) > 100 else result.response_text
            else:
                response_preview = "No response"
            
            # Escape HTML characters
            response_preview = response_preview.replace('<', '&lt;').replace('>', '&gt;')
            
            html += f"""
                    <tr>
                        <td>{filename}</td>
                        <td class="{status_class}">{status_display}</td>
                        <td>{result.response_time:.2f}s</td>
                        <td class="{status_class}">{result_text}</td>
                        <td class="response-cell" title="{response_preview}">{response_preview}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">Error Analysis</h2>
"""
        
        if stats['error_responses']:
            html += """
            <table>
                <thead>
                    <tr>
                        <th>Test File</th>
                        <th>Status Code</th>
                        <th>Error Details</th>
                    </tr>
                </thead>
                <tbody>
"""
            for error_result in stats['error_responses']:
                filename = os.path.basename(error_result.file_path)
                status_display = error_result.status_code if error_result.status_code else "N/A"
                error_details = error_result.error_message or error_result.response_text[:200] + "..."
                error_details = error_details.replace('<', '&lt;').replace('>', '&gt;')
                
                html += f"""
                        <tr>
                            <td>{filename}</td>
                            <td class="status-error">{status_display}</td>
                            <td>{error_details}</td>
                        </tr>
"""
            html += """
                </tbody>
            </table>
"""
        else:
            html += "<p>No errors detected in responses! 🎉</p>"
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        return html