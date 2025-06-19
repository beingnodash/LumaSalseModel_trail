# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Luma University Sales & Revenue Analysis Model - a comprehensive financial forecasting tool that simulates and predicts Luma's revenue streams from university partnerships. The project includes both a core Python financial model and an interactive Streamlit web application.

## Key Architecture

### Core Financial Model
- **Location**: `lumasalsemodel_trail/luma_sales_model/financial_model.py`
- **Main Class**: `LumaFinancialModel` - Handles all financial calculations, cohort tracking, and revenue projections
- **Key Features**: Multi-period forecasting, cohort analysis, sensitivity analysis, multiple partnership models (Type1, Type2a/b/c, Type3)

### Streamlit Web Application
- **Entry Point**: `lumasalsemodel_trail/streamlit_app/app.py`
- **Structure**: Multi-page application with navigation between:
  - Main page: Parameter configuration and basic results
  - Visualization page: `pages/visualization.py` - Interactive charts and graphs
  - Sensitivity analysis: `pages/sensitivity.py` - Parameter impact analysis
  - Strategy optimization: `pages/strategy_optimizer.py` - Multi-objective optimization

### Utility Modules
- `streamlit_app/utils/parameter_ui.py` - UI components for parameter input
- `streamlit_app/utils/plot_utils.py` - Plotting and visualization utilities
- `streamlit_app/utils/optimization.py` - Optimization algorithms (grid search, Bayesian, genetic)
- `streamlit_app/utils/localization.py` - Multi-language support utilities

## Common Development Commands

### Environment Setup
```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the Application
```bash
# Start Streamlit web application
poetry run streamlit run lumasalsemodel_trail/streamlit_app/app.py

# Run core model standalone
poetry run python lumasalsemodel_trail/main.py
```

### Development and Testing
```bash
# Run the core model with custom parameters
cd lumasalsemodel_trail && python main.py

# Check model outputs (results saved to outputs/ directory)
ls outputs/
```

## Key Business Models

The financial model supports multiple university partnership types:
- **Type1**: Universities pay fixed access fees, students pay universities directly
- **Type2a/b/c**: Universities pay access fees, Luma gets percentage of student payments (varying splits)
- **Type3**: No access fees, Luma gets all student payments

## Important Configuration

### Parameter Categories
- **Forecasting**: `total_half_years`, `new_clients_per_half_year`
- **Partnership Distribution**: `mode_distribution` (Type1, Type2a/b/c, Type3 percentages)
- **Pricing**: Student feature pricing, membership tiers, university access fees
- **Retention**: University and student renewal rates
- **Conversion**: Student payment conversion rates and usage patterns

### Key Output Metrics
- `Luma_Revenue_Total`: Primary revenue metric
- `Luma_Fixed_Fee_*`: Revenue from university access fees
- `Luma_Student_Share_*`: Revenue from student payment splits
- `Uni_Fund_*`: University fund contributions
- Cohort tracking for universities and students

## Dependencies

The project uses Poetry for dependency management with key packages:
- **Core**: pandas, numpy, matplotlib, seaborn
- **Web App**: streamlit, plotly (for interactive visualizations)
- **Optimization**: scikit-optimize, deap (genetic algorithms)
- **Data Processing**: requests for external data if needed

## File Structure Notes

- Main model logic in `luma_sales_model/financial_model.py:LumaFinancialModel`
- Streamlit app follows multi-page pattern with utils separation
- Results are saved to `outputs/` directory when running standalone
- User documentation in `USER_GUIDE.md` and `streamlit_app/README.md`

## Development Considerations

- The model uses half-year periods as the basic time unit for forecasting
- Cohort tracking is implemented to handle university and student renewals properly
- Parameter validation ensures distribution percentages sum to 1.0
- Sensitivity analysis and optimization features are computationally intensive
- The model is designed to be user-friendly for non-technical business stakeholders