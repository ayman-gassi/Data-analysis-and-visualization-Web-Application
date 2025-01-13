# Data Cortex - Data Analysis and Visualization Web Application

Data Cortex is a Django-based web application designed to simplify data analysis and visualization for non-technical and technical users alike. With a clean and intuitive interface, users can upload CSV or Excel files, analyze data, and generate insightful visualizations using powerful Python libraries such as **Seaborn**, **Matplotlib**, and **Pandas**.

---

## Features

### Core Functionalities
1. **File Upload**:
   - Supports `.xlsx` (Excel) and `.csv` files for uploading and processing.
   - Seamlessly displays uploaded data in a structured table.

2. **Data Visualization**:
   - Generate a variety of plots, including:
     - **Bivariate KDE Plot**
     - **Histograms**
     - **Bar Plots**
   - Visualizations are powered by **Matplotlib** and **Seaborn** for high-quality and customizable outputs.
   - Options to download or delete generated plots.

3. **Data Manipulation**:
   - Rename columns to better understand datasets.
   - Edit specific elements directly within the interface.
   - Add new columns or manipulate existing ones.

4. **Statistical Analysis**:
   - Perform calculations for key metrics:
     - **Min**, **Max**, **Mean**, **Correlation**, etc.
   - Execute conditional probability and T-tests with **NumPy** and **Pandas**.

5. **Interactive Console**:
   - Enter Python commands directly within the app's console for advanced data manipulation or analysis.
   - Examples:
     ```python
     df['column_name'].mean()
     df.describe()
     ```

---

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Pip (Python package manager)
- Virtualenv (recommended)

### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ayman-gassi/Data-analysis-and-visualization-Web-Application
   cd Data-analysis-and-visualization-Web-Application

2. **Set up a Virtual Environment**:
    ```bash 
    python -m venv env
    source env/bin/activate

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt

4. **Run the Server**:
    ```bash
    python manage.py runserver

