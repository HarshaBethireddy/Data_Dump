"""
Ultra-efficient report service with extraordinary features.

Generates interactive HTML reports with charts, analytics, and insights
using minimal, high-performance code with maximum visual impact.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import plotly.graph_objects as go
import plotly.express as px
from jinja2 import Environment, BaseLoader

from api_test_framework.core.config import get_settings
from api_test_framework.core.exceptions import ReportGenerationError
from api_test_framework.core.logging import get_logger
from api_test_framework.models.test_models import TestExecution, ComparisonResult, ReportData


class ReportService:
    """Ultra-efficient report generator with extraordinary features."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("report")
        
        # Ultra-compact HTML template with all features
        self.html_template = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{title}}</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font:14px/1.6 -apple-system,sans-serif;color:#333;background:#f8f9fa}
.container{max-width:1200px;margin:0 auto;padding:20px}.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;border-radius:10px;margin-bottom:30px;text-align:center}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}
.stat-card{background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);text-align:center}
.stat-value{font-size:2em;font-weight:bold;color:#667eea}.stat-label{color:#666;margin-top:5px}
.chart-container{background:white;padding:20px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:30px}
.success{color:#28a745}.warning{color:#ffc107}.error{color:#dc3545}
.table{width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.table th,.table td{padding:12px;text-align:left;border-bottom:1px solid #eee}
.table th{background:#f8f9fa;font-weight:600}.table tr:hover{background:#f8f9fa}
.badge{padding:4px 8px;border-radius:4px;font-size:12px;font-weight:bold}
.badge-success{background:#d4edda;color:#155724}.badge-warning{background:#fff3cd;color:#856404}.badge-error{background:#f8d7da;color:#721c24}
</style></head><body>
<div class="container">
<div class="header"><h1>{{title}}</h1><p>Generated: {{timestamp}}</p></div>

<div class="stats">
<div class="stat-card"><div class="stat-value {{success_class}}">{{total_tests}}</div><div class="stat-label">Total Tests</div></div>
<div class="stat-card"><div class="stat-value success">{{successful_tests}}</div><div class="stat-label">Successful</div></div>
<div class="stat-card"><div class="stat-value {{success_rate_class}}">{{success_rate}}%</div><div class="stat-label">Success Rate</div></div>
<div class="stat-card"><div class="stat-value">{{avg_response_time}}ms</div><div class="stat-label">Avg Response Time</div></div>
</div>

{% if charts %}
<div class="chart-container"><div id="performance-chart"></div></div>
<div class="chart-container"><div id="success-chart"></div></div>
{% if comparison_chart %}<div class="chart-container"><div id="comparison-chart"></div></div>{% endif %}
{% endif %}

<div class="chart-container">
<h3>Test Results</h3>
<table class="table">
<thead><tr><th>Test</th><th>Status</th><th>Response Time</th><th>App ID</th><th>Timestamp</th></tr></thead>
<tbody>
{% for result in test_results %}
<tr><td>{{result.test_name}}</td>
<td><span class="badge badge-{{result.status_class}}">{{result.status}}</span></td>
<td>{{result.response_time}}ms</td><td>{{result.app_id}}</td><td>{{result.timestamp}}</td></tr>
{% endfor %}
</tbody></table></div>

{% if comparisons %}
<div class="chart-container">
<h3>Comparison Results</h3>
<table class="table">
<thead><tr><th>Comparison</th><th>Result</th><th>Similarity</th><th>Differences</th><th>Duration</th></tr></thead>
<tbody>
{% for comp in comparisons %}
<tr><td>{{comp.name}}</td>
<td><span class="badge badge-{{comp.result_class}}">{{comp.result}}</span></td>
<td>{{comp.similarity}}%</td><td>{{comp.differences}}</td><td>{{comp.duration}}ms</td></tr>
{% endfor %}
</tbody></table></div>
{% endif %}

</div>
<script>
{% if charts %}
// Performance Chart
Plotly.newPlot('performance-chart',{{performance_data|safe}},{title:'Response Time Distribution',height:400});
// Success Rate Chart  
Plotly.newPlot('success-chart',{{success_data|safe}},{title:'Success Rate Over Time',height:400});
{% if comparison_chart %}
// Comparison Chart
Plotly.newPlot('comparison-chart',{{comparison_data|safe}},{title:'Comparison Results',height:400});
{% endif %}
{% endif %}
</script></body></html>
        """
    
    async def generate_comprehensive_report(
        self,
        executions: List[TestExecution],
        comparisons: Optional[List[ComparisonResult]] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """Generate comprehensive report with all extraordinary features."""
        
        # Create report data
        report_data = ReportData(
            report_title="API Test Framework - Comprehensive Report",
            report_type="comprehensive",
            test_executions=executions,
            comparison_results=comparisons or []
        )
        
        # Generate all formats
        output_dir = output_path or self.settings.paths.reports_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate HTML report with charts
        html_path = await self._generate_html_report(report_data, output_dir, timestamp)
        
        # Generate JSON report
        await self._generate_json_report(report_data, output_dir, timestamp)
        
        # Generate Excel report
        await self._generate_excel_report(report_data, output_dir, timestamp)
        
        self.logger.info(f"Generated comprehensive report: {html_path}")
        return html_path
    
    async def _generate_html_report(
        self,
        report_data: ReportData,
        output_dir: Path,
        timestamp: str
    ) -> Path:
        """Generate interactive HTML report with charts."""
        
        # Calculate statistics
        stats = self._calculate_statistics(report_data)
        
        # Generate charts
        charts = self._generate_charts(report_data)
        
        # Prepare template data
        template_data = {
            "title": report_data.report_title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": stats["total_tests"],
            "successful_tests": stats["successful_tests"],
            "success_rate": f"{stats['success_rate']:.1f}",
            "avg_response_time": f"{stats['avg_response_time']:.1f}",
            "success_class": "success" if stats["success_rate"] >= 95 else "warning" if stats["success_rate"] >= 80 else "error",
            "success_rate_class": "success" if stats["success_rate"] >= 95 else "warning" if stats["success_rate"] >= 80 else "error",
            "charts": True,
            "performance_data": json.dumps(charts["performance"]),
            "success_data": json.dumps(charts["success_rate"]),
            "comparison_chart": bool(report_data.comparison_results),
            "comparison_data": json.dumps(charts.get("comparison", [])),
            "test_results": self._format_test_results(report_data),
            "comparisons": self._format_comparisons(report_data.comparison_results)
        }
        
        # Render template
        env = Environment(loader=BaseLoader())
        template = env.from_string(self.html_template)
        html_content = template.render(**template_data)
        
        # Save HTML file
        html_path = output_dir / f"report_{timestamp}.html"
        async with aiofiles.open(html_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)
        
        return html_path
    
    def _calculate_statistics(self, report_data: ReportData) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        total_tests = sum(len(exec.test_results) for exec in report_data.test_executions)
        successful_tests = sum(
            sum(1 for r in exec.test_results if r.is_successful())
            for exec in report_data.test_executions
        )
        
        # Response times
        response_times = []
        for exec in report_data.test_executions:
            for result in exec.test_results:
                if result.response_time_ms:
                    response_times.append(result.response_time_ms)
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
        }
    
    def _generate_charts(self, report_data: ReportData) -> Dict[str, Any]:
        """Generate interactive charts with Plotly."""
        charts = {}
        
        # Performance distribution chart
        response_times = []
        for exec in report_data.test_executions:
            for result in exec.test_results:
                if result.response_time_ms:
                    response_times.append(result.response_time_ms)
        
        if response_times:
            fig = go.Figure(data=[go.Histogram(x=response_times, nbinsx=20)])
            fig.update_layout(xaxis_title="Response Time (ms)", yaxis_title="Count")
            charts["performance"] = fig.to_dict()
        
        # Success rate over time
        success_data = []
        for exec in report_data.test_executions:
            success_data.append({
                "execution": exec.execution_name,
                "success_rate": exec.get_success_rate(),
                "timestamp": exec.start_time.isoformat() if exec.start_time else ""
            })
        
        if success_data:
            fig = go.Figure(data=[
                go.Scatter(
                    x=[d["execution"] for d in success_data],
                    y=[d["success_rate"] for d in success_data],
                    mode='lines+markers'
                )
            ])
            fig.update_layout(xaxis_title="Execution", yaxis_title="Success Rate (%)")
            charts["success_rate"] = fig.to_dict()
        
        # Comparison results chart
        if report_data.comparison_results:
            similarities = [c.get_similarity_percentage() for c in report_data.comparison_results]
            names = [c.comparison_name for c in report_data.comparison_results]
            
            fig = go.Figure(data=[go.Bar(x=names, y=similarities)])
            fig.update_layout(xaxis_title="Comparison", yaxis_title="Similarity (%)")
            charts["comparison"] = fig.to_dict()
        
        return charts
    
    def _format_test_results(self, report_data: ReportData) -> List[Dict[str, Any]]:
        """Format test results for display."""
        results = []
        for exec in report_data.test_executions:
            for result in exec.test_results:
                results.append({
                    "test_name": result.test_name,
                    "status": result.status.value,
                    "status_class": "success" if result.is_successful() else "error",
                    "response_time": f"{result.response_time_ms:.1f}" if result.response_time_ms else "N/A",
                    "app_id": str(result.app_id),
                    "timestamp": result.start_time.strftime("%H:%M:%S") if result.start_time else "N/A"
                })
        return results[:100]  # Limit for performance
    
    def _format_comparisons(self, comparisons: List[ComparisonResult]) -> List[Dict[str, Any]]:
        """Format comparison results for display."""
        return [
            {
                "name": comp.comparison_name,
                "result": "Equal" if comp.are_equal else "Different",
                "result_class": "success" if comp.are_equal else "warning",
                "similarity": f"{comp.get_similarity_percentage():.1f}",
                "differences": len(comp.differences),
                "duration": f"{comp.comparison_duration_ms:.1f}" if comp.comparison_duration_ms else "N/A"
            }
            for comp in comparisons
        ]
    
    async def _generate_json_report(
        self,
        report_data: ReportData,
        output_dir: Path,
        timestamp: str
    ) -> Path:
        """Generate JSON report."""
        json_path = output_dir / f"report_{timestamp}.json"
        
        async with aiofiles.open(json_path, 'w') as f:
            await f.write(report_data.to_json())
        
        return json_path
    
    async def _generate_excel_report(
        self,
        report_data: ReportData,
        output_dir: Path,
        timestamp: str
    ) -> Path:
        """Generate Excel report with multiple sheets."""
        try:
            import pandas as pd
            from openpyxl.styles import PatternFill, Font
            
            excel_path = output_dir / f"report_{timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    "Metric": ["Total Tests", "Successful Tests", "Success Rate", "Avg Response Time"],
                    "Value": [
                        report_data.summary_stats.get("total_tests", 0),
                        report_data.summary_stats.get("successful_tests", 0),
                        f"{report_data.summary_stats.get('overall_success_rate', 0):.1f}%",
                        f"{report_data.summary_stats.get('average_response_time_ms', 0):.1f}ms"
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
                
                # Test results sheet
                test_data = []
                for exec in report_data.test_executions:
                    for result in exec.test_results:
                        test_data.append({
                            "Execution": exec.execution_name,
                            "Test Name": result.test_name,
                            "Status": result.status.value,
                            "App ID": str(result.app_id),
                            "Response Time (ms)": result.response_time_ms,
                            "Success": result.is_successful(),
                            "Start Time": result.start_time
                        })
                
                if test_data:
                    pd.DataFrame(test_data).to_excel(writer, sheet_name="Test Results", index=False)
                
                # Comparison results sheet
                if report_data.comparison_results:
                    comp_data = []
                    for comp in report_data.comparison_results:
                        comp_data.append({
                            "Comparison Name": comp.comparison_name,
                            "Are Equal": comp.are_equal,
                            "Similarity %": comp.get_similarity_percentage(),
                            "Total Differences": len(comp.differences),
                            "Duration (ms)": comp.comparison_duration_ms
                        })
                    
                    pd.DataFrame(comp_data).to_excel(writer, sheet_name="Comparisons", index=False)
            
            return excel_path
            
        except ImportError:
            self.logger.warning("pandas/openpyxl not available, skipping Excel report")
            return None
    
    async def generate_quick_summary(self, execution: TestExecution) -> str:
        """Generate ultra-quick text summary."""
        stats = {
            "total": len(execution.test_results),
            "success": sum(1 for r in execution.test_results if r.is_successful()),
            "avg_time": sum(r.response_time_ms or 0 for r in execution.test_results) / len(execution.test_results) if execution.test_results else 0
        }
        
        return f"""
🚀 Test Execution Summary: {execution.execution_name}
📊 Results: {stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}% success)
⏱️  Avg Response: {stats['avg_time']:.1f}ms
🎯 Status: {execution.status.value}
        """.strip()