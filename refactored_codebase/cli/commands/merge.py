"""
Merge command implementation for merging CSV files to Excel.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from refactored_codebase.config.settings import Settings
from refactored_codebase.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def execute_merge_command(
    settings: Settings,
    csv_folder: str,
    output_file: Optional[str] = None,
    include_summary: bool = False
) -> None:
    """
    Execute the merge command.
    
    Args:
        settings: Framework settings
        csv_folder: Folder containing CSV files to merge
        output_file: Output Excel file name
        include_summary: Whether to include summary sheet
    """
    logger.info(f"Starting CSV merge - folder: {csv_folder}")
    
    csv_path = Path(csv_folder)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV folder not found: {csv_path}")
    
    # Find CSV files
    csv_files = list(csv_path.glob("*.csv"))
    
    if not csv_files:
        console.print(f"⚠️ No CSV files found in {csv_path}", style="yellow")
        return
    
    # Determine output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"merged_results_{timestamp}.xlsx"
    
    output_path = settings.paths.merged_dir / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n📊 Starting CSV Merge", style="bold blue")
    console.print(f"CSV folder: {csv_path}")
    console.print(f"Found {len(csv_files)} CSV files")
    console.print(f"Output file: {output_path}")
    console.print(f"Include summary: {include_summary}")
    
    # Process CSV files
    dataframes = {}
    file_info = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Processing CSV files...", total=len(csv_files))
        
        for csv_file in csv_files:
            try:
                # Read CSV file
                df = pd.read_csv(csv_file)
                
                # Clean sheet name (Excel sheet names have restrictions)
                sheet_name = _clean_sheet_name(csv_file.stem)
                
                # Ensure unique sheet name
                original_name = sheet_name
                counter = 1
                while sheet_name in dataframes:
                    sheet_name = f"{original_name}_{counter}"
                    counter += 1
                
                dataframes[sheet_name] = df
                
                file_info.append({
                    "csv_file": csv_file.name,
                    "sheet_name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_kb": csv_file.stat().st_size / 1024
                })
                
                progress.update(task, advance=1)
                
            except Exception as e:
                logger.error(f"Failed to process {csv_file.name}: {e}")
                console.print(f"❌ Error processing {csv_file.name}: {e}", style="red")
                progress.update(task, advance=1)
    
    if not dataframes:
        console.print("❌ No valid CSV files could be processed", style="red")
        return
    
    # Create Excel file
    console.print(f"\n📝 Creating Excel file with {len(dataframes)} sheets...")
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write data sheets
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Create summary sheet if requested
            if include_summary:
                _create_summary_sheet(writer, file_info, dataframes)
        
        console.print(f"✅ Excel file created successfully!", style="bold green")
        console.print(f"Output: {output_path}")
        
        # Display summary
        _display_merge_summary(file_info, output_path)
        
    except Exception as e:
        logger.error(f"Failed to create Excel file: {e}")
        console.print(f"❌ Failed to create Excel file: {e}", style="red")
        raise


def _clean_sheet_name(name: str) -> str:
    """Clean sheet name for Excel compatibility."""
    # Excel sheet name restrictions
    invalid_chars = ['\\', '/', '*', '[', ']', ':', '?']
    
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Limit length to 31 characters
    if len(name) > 31:
        name = name[:28] + "..."
    
    return name


def _create_summary_sheet(writer, file_info: list, dataframes: dict) -> None:
    """Create summary sheet with file information."""
    summary_data = []
    
    for info in file_info:
        summary_data.append({
            "CSV File": info["csv_file"],
            "Excel Sheet": info["sheet_name"],
            "Rows": info["rows"],
            "Columns": info["columns"],
            "Size (KB)": round(info["size_kb"], 2)
        })
    
    # Add totals row
    total_rows = sum(info["rows"] for info in file_info)
    total_size = sum(info["size_kb"] for info in file_info)
    
    summary_data.append({
        "CSV File": "TOTAL",
        "Excel Sheet": f"{len(file_info)} sheets",
        "Rows": total_rows,
        "Columns": "-",
        "Size (KB)": round(total_size, 2)
    })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    
    # Format summary sheet
    worksheet = writer.sheets["Summary"]
    
    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Bold header row
    for cell in worksheet[1]:
        cell.font = cell.font.copy(bold=True)
    
    # Bold totals row
    last_row = len(summary_data)
    for cell in worksheet[last_row + 1]:
        cell.font = cell.font.copy(bold=True)


def _display_merge_summary(file_info: list, output_path: Path) -> None:
    """Display merge summary table."""
    table = Table(title="Merge Summary")
    table.add_column("CSV File", style="cyan")
    table.add_column("Excel Sheet", style="green")
    table.add_column("Rows", style="yellow")
    table.add_column("Columns", style="yellow")
    table.add_column("Size (KB)", style="magenta")
    
    total_rows = 0
    total_size = 0
    
    for info in file_info:
        table.add_row(
            info["csv_file"],
            info["sheet_name"],
            str(info["rows"]),
            str(info["columns"]),
            f"{info['size_kb']:.1f}"
        )
        total_rows += info["rows"]
        total_size += info["size_kb"]
    
    # Add totals row
    table.add_row(
        "TOTAL",
        f"{len(file_info)} sheets",
        str(total_rows),
        "-",
        f"{total_size:.1f}",
        style="bold"
    )
    
    console.print(table)
    
    # File information
    console.print(f"\n📄 Output File Information:")
    console.print(f"  Path: {output_path}")
    console.print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
    console.print(f"  Sheets: {len(file_info)}")
    console.print(f"  Total Rows: {total_rows:,}")