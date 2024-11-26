import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadFileForm
import matplotlib.pyplot as plt
import numpy as np
from django.core.paginator import Paginator
from io import BytesIO
import urllib, base64
import seaborn as sns



def handle_uploaded_file(file):
    if file.name.endswith('.csv'):
        data = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        data = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or XLS/XLSX file.")
    return data

def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                data = handle_uploaded_file(file)
                request.session['data_list'] = data.to_dict(orient='records')
                return redirect('overview') 
            except ValueError as e:
                form.add_error('file', str(e))
            except Exception as e:
                form.add_error(None, "An unexpected error occurred.")
    else:
        form = UploadFileForm()
    return render(request, 'index.html', {'form': form})

def categorize_dtype(dtype):
    if pd.api.types.is_numeric_dtype(dtype):
        return "number"
    elif pd.api.types.is_string_dtype(dtype):
        return "string"
    elif pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    else:
        return "other"

def overview(request):
    data_list = request.session.get('data_list')
    if not data_list:
        messages.error(request, "No data available to display.")
        return redirect('index')
    
    data = pd.DataFrame(data_list)
    columns_with_nan = [
        {
            "column_name": col,
            "column_type": categorize_dtype(data[col].dtype)
        }
        for col in data.columns[data.isna().any()]
    ]
    column_names = data.columns.tolist()
    tools = [
        {"name": "Mean", "description": "Calculate the mean value."},
        {"name": "Median", "description": "Calculate the median value."},
        {"name": "Mode", "description": "Calculate the mode value."},
        {"name": "Max", "description": "Find the maximum value."},
        {"name": "Min", "description": "Find the minimum value."},
        {"name": "Sum", "description": "Calculate the sum."},
        {"name": "Count", "description": "Count the values."},
        {"name": "Covariance", "description": "Calculate the covariance matrix."},
        {"name": "Correlation", "description": "Calculate the correlation matrix."},
    ]
    tools_requiring_columns = ["Mean", "Median", "Mode", "Max", "Min", "Sum", "Count"]


    if request.method == 'POST':
        replacement_value = request.POST.get('replacement_value')
        column_to_replace = request.POST.get('column')
        if not replacement_value or not column_to_replace:
            messages.error(request, "Both column and replacement value are required.")
            return redirect('overview')
        column_data = next((col for col in columns_with_nan if col["column_name"] == column_to_replace), None)
        if not column_data:
            messages.error(request, "Invalid column selected.")
            return redirect('overview')
        try:
            if column_data["column_type"] == "number":
                replacement_value = float(replacement_value)
            elif column_data["column_type"] == "boolean":
                replacement_value = replacement_value.lower() == 'true'
        except ValueError:
            messages.error(request, "Invalid replacement value for the selected column type.")
            return redirect('overview')
        data[column_to_replace].fillna(replacement_value, inplace=True)
        request.session['data_list'] = data.to_dict('records')
        messages.success(request, f"NaN values in '{column_to_replace}' replaced with '{replacement_value}'.")
        return redirect('overview')
    
    paginator = Paginator(data_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    results = request.session.get('calculation_results', [])
    print(results)
    return render(request, 'workshop/overview.html', {
        'page_obj': page_obj,
        'current_page': 'overview',
        'columns_with_nan': columns_with_nan,
        'tools': tools,
        'tools_requiring_columns': tools_requiring_columns,
        'column_names': column_names,
        'results': results 
    })

def calculate_tool(request):
    if request.method == 'POST':
        data_list = request.session.get('data_list')
        if not data_list:
            messages.error(request, "No data available for calculation.")
            return redirect('overview')
        
        data = pd.DataFrame(data_list)
        tool_name = request.POST.get('tool')
        selected_column = request.POST.get('column')

        if not tool_name:
            messages.error(request, "No tool selected.")
            return redirect('overview')

        try:
            if tool_name in ["Mean", "Median", "Mode", "Max", "Min", "Sum"]:
                if not selected_column or selected_column not in data.columns:
                    messages.error(request, "Invalid or no column selected.")
                    return redirect('overview')
                column_data = data[selected_column]
                if tool_name == "Mean":
                    result = column_data.mean()
                elif tool_name == "Median":
                    result = column_data.median()
                elif tool_name == "Mode":
                    result = column_data.mode().iloc[0]
                elif tool_name == "Max":
                    result = column_data.max()
                elif tool_name == "Min":
                    result = column_data.min()
                elif tool_name == "Sum":
                    result = column_data.sum()
               
            else:
                if tool_name == "Covariance":
                    result = data.cov().to_dict()
                elif tool_name == "Correlation":
                    result = data.corr().to_dict()
                elif tool_name == "Count":
                    result = column_data.count()
                else:
                    messages.error(request, "Invalid tool selected.")
                    return redirect('overview')

            session_results = request.session.get('calculation_results', [])
            session_results.append({
                "tool": tool_name,
                "column": selected_column if selected_column else "All Columns",
                "result": float(result) if isinstance(result, (np.float64, np.float32)) else 
                        int(result) if isinstance(result, (np.int64, np.int32)) else result,
            })
            request.session['calculation_results'] = session_results
            request.session.modified = True

            messages.success(request, f"Result for '{tool_name}' has been calculated and stored.")
            return redirect('overview')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('overview')



def data_analyze(request):
    data_list = request.session.get('data_list')
    
    if not data_list:
        messages.error(request, "No data available to display.")
        return redirect('index')
    
    data = pd.DataFrame(data_list)

    plot_images = []

    for col in data.select_dtypes(include=['float64', 'int64']).columns:
        fig, ax = plt.subplots()
        sns.histplot(data[col], kde=True, ax=ax)
        ax.set_title(f"Histogram of {col}")
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode("utf-8")
        plot_images.append(f"data:image/png;base64,{plot_data}")
        plt.close(fig)

    numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
    for i in range(len(numeric_columns)):
        for j in range(i + 1, len(numeric_columns)):
            fig, ax = plt.subplots()
            sns.scatterplot(x=data[numeric_columns[i]], y=data[numeric_columns[j]], ax=ax)
            ax.set_title(f"Scatter Plot: {numeric_columns[i]} vs {numeric_columns[j]}")
            buffer = BytesIO()
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.read()).decode("utf-8")
            plot_images.append(f"data:image/png;base64,{plot_data}")
            plt.close(fig)

    for col in data.select_dtypes(include=['float64', 'int64']).columns:
        fig, ax = plt.subplots()
        sns.boxplot(x=data[col], ax=ax)
        ax.set_title(f"Box Plot of {col}")
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode("utf-8")
        plot_images.append(f"data:image/png;base64,{plot_data}")
        plt.close(fig)

    fig, ax = plt.subplots()
    corr_matrix = data.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
    ax.set_title("Correlation Heatmap")
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.read()).decode("utf-8")
    plot_images.append(f"data:image/png;base64,{plot_data}")
    plt.close(fig)

    return render(request, 'workshop/analyse.html', {
        'current_page': 'data_analyze',
        'plot_images': plot_images  
    })



def console(request):
    data_list = request.session.get('data_list')
    if not data_list:
        messages.error(request, "No data available to display.")
        return redirect('index')
    data = pd.DataFrame(data_list)
    result = None

    if request.method == "POST":
        command = request.POST.get('command')

        try:
            if command:
           
                result = eval(command, {"df": data})

                if isinstance(result, pd.DataFrame):
                    result = result.to_html(classes="table table-striped")
                elif isinstance(result, pd.Series):
                    result = result.to_frame().to_html(classes="table table-striped")
                elif isinstance(result, pd.DataFrame):
                    result = result.to_html()
        except Exception as e:
            messages.error(request, f"Error executing command: {str(e)}")
            result = f"Error: {str(e)}"

    return render(request, 'console.html', {
        'current_page': 'console',
        'result': result,
    })


def logout(request):
    request.session.flush()
    messages.success(request, "You have successfully logged out.")
    return redirect('index')