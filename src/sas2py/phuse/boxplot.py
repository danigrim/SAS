"""
Python implementation of PhUSE box plot generation for clinical data.
Translates the functionality from WPCT-F.07.01.sas.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Union, Any
import os

from ..core.readers import read_sas, handle_sas_missing, convert_sas_dates
from .utils import (
    get_parameter_metadata,
    count_unique_values,
    get_reference_lines,
    get_var_min_max,
    value_format,
    boxplot_block_ranges,
    axis_order
)


def filter_dataset(
    df: pd.DataFrame,
    param_codes: List[str],
    visits: Optional[List[Union[int, str]]] = None,
    population_flag: Optional[str] = None,
    analysis_flag: Optional[str] = None
) -> pd.DataFrame:
    """
    Filter dataset by parameters, visits, and population flags.
    
    Args:
        df: Input dataset
        param_codes: List of parameter codes to include
        visits: List of visit numbers or labels to include
        population_flag: Column name for population flag (e.g., 'SAFFL')
        analysis_flag: Column name for analysis flag (e.g., 'ANL01FL')
        
    Returns:
        Filtered DataFrame
    """
    result = df.copy()
    
    if 'PARAMCD' in result.columns and param_codes:
        result = result[result['PARAMCD'].isin(param_codes)]
    
    if visits and 'AVISITN' in result.columns:
        if all(isinstance(v, (int, float)) for v in visits):
            result = result[result['AVISITN'].isin(visits)]
        elif all(isinstance(v, str) for v in visits) and 'AVISIT' in result.columns:
            result = result[result['AVISIT'].isin(visits)]
    
    if population_flag and population_flag in result.columns:
        result = result[result[population_flag] == 'Y']
    
    if analysis_flag and analysis_flag in result.columns:
        result = result[result[analysis_flag] == 'Y']
    
    return result


def detect_outliers(
    df: pd.DataFrame,
    measure_var: str,
    low_var: Optional[str] = None,
    high_var: Optional[str] = None
) -> pd.DataFrame:
    """
    Detect measurements outside normal range.
    
    Args:
        df: Input dataset
        measure_var: Column name for measured value
        low_var: Column name for lower limit of normal range
        high_var: Column name for upper limit of normal range
        
    Returns:
        DataFrame with outlier flag added
    """
    result = df.copy()
    
    outlier_col = f"{measure_var}_outlier"
    result[outlier_col] = np.nan
    
    if low_var and low_var in result.columns:
        low_mask = (~result[measure_var].isna() & 
                   ~result[low_var].isna() & 
                   (result[measure_var] < result[low_var]))
        result.loc[low_mask, outlier_col] = result.loc[low_mask, measure_var]
    
    if high_var and high_var in result.columns:
        high_mask = (~result[measure_var].isna() & 
                    ~result[high_var].isna() & 
                    (result[measure_var] > result[high_var]))
        result.loc[high_mask, outlier_col] = result.loc[high_mask, measure_var]
    
    return result


def calculate_stats(
    df: pd.DataFrame,
    measure_var: str,
    visit_var: str,
    visit_label_var: str,
    treatment_var: str,
    treatment_label_var: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate summary statistics by visit and treatment.
    
    Args:
        df: Input dataset
        measure_var: Column name for measured value
        visit_var: Column name for visit/timepoint numeric value
        visit_label_var: Column name for visit/timepoint label
        treatment_var: Column name for treatment group
        treatment_label_var: Column name for treatment group label
        
    Returns:
        DataFrame with summary statistics
    """
    groupby_vars = [visit_var, visit_label_var, treatment_var]
    if treatment_label_var:
        groupby_vars.append(treatment_label_var)
    
    stats = df.groupby(groupby_vars)[measure_var].agg(
        n='count',
        mean='mean',
        std='std',
        median='median',
        min='min',
        max='max',
        q1=lambda x: x.quantile(0.25),
        q3=lambda x: x.quantile(0.75)
    ).reset_index()
    
    for stat in ['mean', 'median', 'std']:
        stats[f'{stat}_fmt'] = stats[stat].apply(lambda x: value_format(x, precision=2))
    
    return stats


def create_treatment_abbreviations(
    df: pd.DataFrame,
    trt_var: str,
    trt_n_var: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[Union[int, str], str]]:
    """
    Create treatment abbreviations based on PROC FORMAT.
    
    Args:
        df: Input dataset
        trt_var: Column name for treatment
        trt_n_var: Column name for numeric treatment code
        
    Returns:
        Tuple of (DataFrame with abbreviation column, abbreviation mapping)
    """
    result = df.copy()
    
    trt_format = {
        0: 'P',       # Placebo
        54: 'X-high',  # High dose
        81: 'X-low'    # Low dose
    }
    
    abbrev_col = f"{trt_var}_short"
    
    if trt_n_var and trt_n_var in result.columns:
        result[abbrev_col] = result[trt_n_var].map(trt_format)
    else:
        result[abbrev_col] = result[trt_var].map(trt_format)
    
    result[abbrev_col] = result[abbrev_col].fillna(result[trt_var])
    
    formatted_trt_format = {int(k) if isinstance(k, int) else str(k): v for k, v in trt_format.items()}
    return result, formatted_trt_format


def generate_boxplot(
    data_df: pd.DataFrame,
    stats_df: pd.DataFrame,
    param_name: str,
    measure_var: str,
    visit_var: str,
    visit_label_var: str,
    treatment_var: str,
    outlier_var: Optional[str] = None,
    reference_lines: Optional[List[float]] = None,
    y_axis_min: Optional[float] = None,
    y_axis_max: Optional[float] = None,
    output_dir: Optional[str] = None,
    file_format: str = 'html',
    width: int = 800,
    height: int = 600
) -> go.Figure:
    """
    Generate box plot for clinical measurements by visit and treatment.
    
    Args:
        data_df: Input dataset with individual observations
        stats_df: Dataset with summary statistics
        param_name: Parameter name for title
        measure_var: Column name for measured value
        visit_var: Column name for visit/timepoint numeric value
        visit_label_var: Column name for visit/timepoint label
        treatment_var: Column name for treatment group
        outlier_var: Column name for outlier values
        reference_lines: List of reference line values
        y_axis_min: Minimum value for y-axis
        y_axis_max: Maximum value for y-axis
        output_dir: Directory to save output files
        file_format: Output file format ('html', 'png', 'pdf')
        width: Plot width in pixels
        height: Plot height in pixels
        
    Returns:
        Plotly figure object
    """
    visits = data_df[visit_var].unique()
    visit_labels = dict(zip(data_df[visit_var], data_df[visit_label_var]))
    treatments = data_df[treatment_var].unique()
    
    colors = ['rgba(31, 119, 180, 0.7)', 'rgba(255, 127, 14, 0.7)', 'rgba(44, 160, 44, 0.7)']
    color_map = dict(zip(treatments, colors[:len(treatments)]))
    
    fig = go.Figure()
    
    for i, treatment in enumerate(treatments):
        for j, visit in enumerate(visits):
            mask = (data_df[visit_var] == visit) & (data_df[treatment_var] == treatment)
            visit_data = data_df[mask][measure_var].dropna()
            
            if len(visit_data) == 0:
                continue
            
            stat_mask = ((stats_df[visit_var] == visit) & 
                         (stats_df[treatment_var] == treatment))
            if stat_mask.sum() == 0:
                continue
            
            stats_row = stats_df[stat_mask].iloc[0]
            n = stats_row['n']
            
            fig.add_trace(go.Box(
                y=visit_data,
                name=f"{visit_labels[visit]}, {treatment}",
                marker_color=color_map[treatment],
                boxpoints=False,  # Hide all points
                jitter=0,
                pointpos=0,
                hoverinfo='y',
                showlegend=False,
                x0=j + (i * 0.3),  # Offset for treatment within visit
                dx=0.3,  # Width of box
                xaxis='x1'
            ))
            
            if outlier_var:
                outlier_mask = mask & ~data_df[outlier_var].isna()
                outliers = data_df[outlier_mask][outlier_var]
                
                if len(outliers) > 0:
                    fig.add_trace(go.Scatter(
                        x=[j + (i * 0.3)] * len(outliers),  # Same position as box
                        y=outliers,
                        mode='markers',
                        marker=dict(
                            color=color_map[treatment],
                            symbol='circle-open',
                            size=8,
                            line=dict(width=2)
                        ),
                        name=f"Outliers ({treatment})",
                        showlegend=False,
                        hoverinfo='y'
                    ))
            
            fig.add_annotation(
                x=j + (i * 0.3),
                y=stats_row['max'] + (y_axis_max - y_axis_min) * 0.02 if y_axis_min is not None and y_axis_max is not None else stats_row['max'] * 0.02,  # Just above max
                text=f"N={n}",
                showarrow=False,
                font=dict(size=10)
            )
    
    if reference_lines:
        for ref_value in reference_lines:
            fig.add_shape(
                type="line",
                x0=-0.5,
                y0=ref_value,
                x1=len(visits) - 0.5,
                y1=ref_value,
                line=dict(
                    color="red",
                    width=1,
                    dash="dash",
                )
            )
    
    fig.update_layout(
        title=f"Box Plot: {param_name} by Visit and Treatment",
        yaxis_title=param_name,
        xaxis_title="Visit",
        yaxis=dict(
            range=[y_axis_min, y_axis_max]
        ),
        xaxis=dict(
            tickvals=list(range(len(visits))),
            ticktext=[visit_labels[v] for v in visits],
            tickangle=-45
        ),
        boxmode='group',
        width=width,
        height=height,
        template='plotly_white'
    )
    
    for treatment, color in color_map.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=color),
            name=treatment,
            showlegend=True
        ))
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"boxplot_{param_name.replace(' ', '_')}.{file_format}"
        filepath = os.path.join(output_dir, filename)
        
        if file_format == 'html':
            fig.write_html(filepath)
        elif file_format == 'png':
            fig.write_image(filepath)
        elif file_format == 'pdf':
            fig.write_image(filepath)
    
    return fig


def process_boxplot_parameters(
    df: pd.DataFrame,
    parameters: List[str],
    measure_var: str,
    visit_var: str,
    visit_label_var: str,
    treatment_var: str,
    low_var: Optional[str] = None,
    high_var: Optional[str] = None,
    population_flag: Optional[str] = None,
    analysis_flag: Optional[str] = None,
    reference_lines_type: str = 'UNIFORM',
    output_dir: Optional[str] = None,
    max_boxes_per_page: int = 20,
    file_format: str = 'html'
) -> List[go.Figure]:
    """
    Process multiple parameters to generate box plots.
    Implements the main functionality of the %boxplot_each_param_tp macro.
    
    Args:
        df: Input dataset
        parameters: List of parameter codes to process
        measure_var: Column name for measured value
        visit_var: Column name for visit/timepoint numeric value
        visit_label_var: Column name for visit/timepoint label
        treatment_var: Column name for treatment group
        low_var: Column name for lower limit of normal range
        high_var: Column name for upper limit of normal range
        population_flag: Column name for population flag (e.g., 'SAFFL')
        analysis_flag: Column name for analysis flag (e.g., 'ANL01FL')
        reference_lines_type: Type of reference lines ('NONE', 'UNIFORM', 'NARROW', 'ALL')
        output_dir: Directory to save output files
        max_boxes_per_page: Maximum number of boxes per page
        file_format: Output file format ('html', 'png', 'pdf')
        
    Returns:
        List of Plotly figure objects
    """
    figures = []
    
    df_with_abbrev, _ = create_treatment_abbreviations(
        df, treatment_var, 'TRTPN' if 'TRTPN' in df.columns else None
    )
    
    param_metadata = get_parameter_metadata(df, 'PARAMCD', 'PARAM')
    
    for param in parameters:
        param_data = filter_dataset(
            df_with_abbrev, 
            [param],
            population_flag=population_flag,
            analysis_flag=analysis_flag
        )
        
        if len(param_data) == 0:
            continue
        
        param_name = param_metadata.get(param, param)
        
        param_data = detect_outliers(
            param_data,
            measure_var,
            low_var,
            high_var
        )
        
        stats = calculate_stats(
            param_data,
            measure_var,
            visit_var,
            visit_label_var,
            treatment_var
        )
        
        ref_lines = get_reference_lines(
            param_data,
            measure_var,
            ref_type=reference_lines_type,
            low_col=low_var,
            high_col=high_var
        )
        
        y_min, y_max = get_var_min_max(param_data, measure_var, padding=0.1)
        
        visits = sorted(param_data[visit_var].unique())
        page_ranges = boxplot_block_ranges(param_data, visit_var, max_boxes_per_page)
        
        for page_idx, (start_idx, end_idx) in enumerate(page_ranges):
            page_visits = visits[start_idx:end_idx+1]
            page_data = param_data[param_data[visit_var].isin(page_visits)]
            
            if len(page_data) == 0:
                continue
            
            fig = generate_boxplot(
                page_data,
                stats[stats[visit_var].isin(page_visits)],
                param_name,
                measure_var,
                visit_var,
                visit_label_var,
                treatment_var,
                outlier_var=f"{measure_var}_outlier",
                reference_lines=ref_lines,
                y_axis_min=y_min,
                y_axis_max=y_max,
                output_dir=output_dir,
                file_format=file_format,
                width=800,
                height=600
            )
            
            if output_dir and len(page_ranges) > 1:
                filename = f"boxplot_{param.replace(' ', '_')}_page{page_idx+1}.{file_format}"
                filepath = os.path.join(output_dir, filename)
                
                if file_format == 'html':
                    fig.write_html(filepath)
                elif file_format == 'png':
                    fig.write_image(filepath)
                elif file_format == 'pdf':
                    fig.write_image(filepath)
            
            figures.append(fig)
    
    return figures


def generate_phuse_boxplots(
    input_file: str,
    output_dir: str,
    parameters: List[str],
    visits: Optional[List[Union[int, str]]] = None,
    measure_var: str = 'AVAL',
    low_var: str = 'A1LO',
    high_var: str = 'A1HI',
    visit_var: str = 'AVISITN',
    visit_label_var: str = 'AVISIT',
    treatment_var: str = 'TRTP',
    population_flag: str = 'SAFFL',
    analysis_flag: str = 'ANL01FL',
    reference_lines_type: str = 'UNIFORM',
    max_boxes_per_page: int = 20,
    file_format: str = 'html'
) -> List[go.Figure]:
    """
    Main function to generate PhUSE-compliant box plots for clinical measurements.
    
    Args:
        input_file: Path to input SAS dataset
        output_dir: Directory to save output files
        parameters: List of parameter codes to process
        visits: List of visit numbers to include
        measure_var: Column name for measured value
        low_var: Column name for lower limit of normal range
        high_var: Column name for upper limit of normal range
        visit_var: Column name for visit/timepoint numeric value
        visit_label_var: Column name for visit/timepoint label
        treatment_var: Column name for treatment group
        population_flag: Column name for population flag
        analysis_flag: Column name for analysis flag
        reference_lines_type: Type of reference lines
        max_boxes_per_page: Maximum number of boxes per page
        file_format: Output file format ('html', 'png', 'pdf')
        
    Returns:
        List of Plotly figure objects
    """
    df, meta = read_sas(input_file)
    
    df = handle_sas_missing(df)
    
    if 'ATPTN' not in df.columns and 'ATPT' not in df.columns:
        df['ATPTN'] = 1
        df['ATPT'] = 'TimePoint unknown'
    
    if visits:
        df = filter_dataset(df, parameters, visits)
    
    figures = process_boxplot_parameters(
        df,
        parameters,
        measure_var,
        visit_var,
        visit_label_var,
        treatment_var,
        low_var,
        high_var,
        population_flag,
        analysis_flag,
        reference_lines_type,
        output_dir,
        max_boxes_per_page,
        file_format
    )
    
    return figures
