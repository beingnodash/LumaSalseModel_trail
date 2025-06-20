# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Luma University Sales & Revenue Analysis Model - a comprehensive financial forecasting tool that simulates and predicts Luma's revenue streams from university partnerships. The project includes both a core Python financial model and an interactive Streamlit web application.

## Key Architecture

### Core Financial Models
The project has evolved to include three financial model versions:
- **Primary Model**: `lumasalsemodel_trail/luma_sales_model/simplified_financial_model.py`
  - **Main Class**: `LumaSimplifiedFinancialModel` - Current production model
  - **Features**: 7-category parameter structure, unified B/C mode revenue sharing, optimized revenue accounting
- **Enhanced Model**: `lumasalsemodel_trail/luma_sales_model/enhanced_financial_model.py`
  - Advanced features with additional complexity
- **Legacy Model**: `lumasalsemodel_trail/luma_sales_model/financial_model.py`
  - Original implementation maintained for reference

### Streamlit Web Application
- **Entry Point**: `lumasalsemodel_trail/streamlit_app/app.py`
- **Architecture**: Single-page application with tabbed interface:
  - Parameter Configuration: 7-category parameter setup
  - Model Execution: Run financial model and view results
  - Result Analysis: Interactive visualizations and charts
  - Deep Insights: AI-driven business insights and recommendations

### Specialized Pages
- **Enhanced Sensitivity Analysis**: `pages/enhanced_sensitivity.py`
  - Single parameter, multi-parameter, and importance ranking analysis
- **Enhanced Strategy Optimizer**: `pages/enhanced_strategy_optimizer.py`
  - Multi-algorithm optimization with realistic constraints
- **User Guide**: `pages/user_guide.py` - Interactive documentation

### Core Utility Modules
- `utils/simplified_parameter_ui.py` - Main parameter configuration system (7 categories)
- `utils/enhanced_plot_utils.py` - Advanced visualization tools with Plotly
- `utils/enhanced_optimization.py` - Optimization algorithms with realistic constraints
- `utils/enhanced_sensitivity_analysis.py` - Advanced sensitivity analysis tools
- `utils/localization.py` - Multi-language support utilities

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
# Run tests using pytest
poetry run pytest

# Run specific test files
poetry run pytest tests/test_realistic_constraints.py
poetry run pytest lumasalsemodel_trail/test_simplified_model.py
poetry run pytest lumasalsemodel_trail/test_enhanced_sensitivity.py

# Run the core model with custom parameters
cd lumasalsemodel_trail && python main.py

# Check model outputs (results saved to outputs/ directory)
ls outputs/

# Run constraint validation tests
python run_constraint_tests.py
```

## Key Business Models

The simplified financial model supports three partnership modes:
- **Mode A**: Universities pay fixed access fees, students use all features for free
- **Mode B**: Universities pay access fees, students pay tiered fees (Luma gets revenue share)  
- **Mode C**: Universities pay no fees, students pay tiered fees (Luma gets all student payments)

## Important Configuration

### Parameter Categories (7-Category Structure)
- **Basic Parameters**: `total_half_years` (forecasting periods)
- **Pricing Parameters**: Student pricing (`price_per_use`, membership tiers), university pricing by mode
- **Market Scale**: `new_clients_per_half_year`, `avg_students_per_uni`
- **Market Distribution**: Mode A/B/C ratios, student conversion rates
- **Student Segmentation**: Pay-per-use vs subscription distributions
- **Renewal Rates**: University and student retention rates
- **Revenue Sharing**: Unified sharing ratios for modes B/C

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

- **Main model**: `luma_sales_model/simplified_financial_model.py:LumaSimplifiedFinancialModel`
- **Streamlit app**: Single-page with tabs, specialized analysis pages in `pages/`
- **Utility separation**: Core utilities in `utils/` with enhanced features
- **Results**: Saved to `outputs/` directory when running standalone
- **Documentation**: 
  - `streamlit_app/README.md` - Comprehensive technical documentation
  - `streamlit_app/USER_GUIDE.md` - User-facing guide
  - `docs/` directory - Development notes and architecture documentation
- **Testing**: Test files distributed across root and `lumasalsemodel_trail/` directories
- **Archived code**: Historical implementations in `archived/` directory

## Development Considerations

- **Time Units**: The model uses half-year periods as the basic time unit for forecasting
- **Parameter Validation**: Strict validation ensures distribution percentages sum to 1.0
- **Model Evolution**: Project has evolved from complex Type1/2a/2b/2c/3 structure to simplified Mode A/B/C
- **Performance**: Enhanced sensitivity analysis and optimization features are computationally intensive
- **Architecture**: Multi-version approach with simplified, enhanced, and legacy models
- **Constraints**: Realistic constraint handling prevents extreme parameter values in optimization
- **User Focus**: Designed to be accessible for non-technical business stakeholders
- **Testing**: Comprehensive test suite including constraint validation and model verification