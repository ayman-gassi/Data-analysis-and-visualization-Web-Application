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
from django.http import HttpResponse

def about(request):
    return render(request, 'about.html')

def handle_uploaded_file(file):
    try:
        if file.name.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            data = pd.read_excel(file, engine='openpyxl')
        elif file.name.endswith('.xls'):
            data = pd.read_excel(file, engine='xlrd')
        else:
            raise ValueError("Unsupported file type. Please upload a CSV or XLS/XLSX file.")
        return data
    except Exception as e:
        raise ValueError(f"Error processing the file: {str(e)}")

def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                data = handle_uploaded_file(file)
                request.session.flush()
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
            
            elif tool_name == "Covariance":
                try:
                    print(f"Tool Name Received: {tool_name}")
                    numeric_data = data.select_dtypes(include=[np.number])
                    if numeric_data.shape[1] < 2:
                        raise ValueError("Covariance requires at least two numeric columns.")
                    print("Numeric Data for Covariance:\n", numeric_data.head())  # Debug
                    
                    result = numeric_data.cov()
                    print("Covariance Matrix Before HTML Conversion:\n", result)  # Debug

                    result = result.to_html(classes="min-w-full border-collapse border border-gray-300 text-left text-sm bg-white")
                    print("Covariance Matrix HTML:\n", result)  # Debug
                except Exception as e:
                    messages.error(request, f"Error generating covariance matrix: {e}")
                    return redirect('overview')
                
            elif tool_name == "Correlation":
                try:
                    # Check if there are numeric columns in the data
                    numeric_data = data.select_dtypes(include=[np.number])
                    if numeric_data.shape[1] < 2:
                        raise ValueError("Correlation requires at least two numeric columns.")
                    
                    # Compute the correlation matrix
                    result = numeric_data.corr()
                    print("Correlation Matrix:\n", result)  # Debugging output
                    
                    # Convert the matrix to an HTML table with Tailwind CSS classes
                    result = result.to_html(classes="min-w-full border-collapse border border-gray-300 text-left text-sm bg-white")
                except Exception as e:
                    messages.error(request, f"Error generating correlation matrix: {e}")
                    return redirect('overview')


            elif tool_name == "Count":
                if not selected_column or selected_column not in data.columns:
                    messages.error(request, "Invalid or no column selected for Count.")
                    return redirect('overview')
                try:
                    result = int(data[selected_column].count())
                except Exception as e:
                    messages.error(request, f"Error calculating count: {e}")
                    return redirect('overview')

            else:
                messages.error(request, "Invalid tool selected.")
                return redirect('overview')                



            session_results = request.session.get('calculation_results', [])
            
            session_results.append({
                "tool": tool_name,
                "column": selected_column if selected_column else "All Columns",  # Covariance applies to all numeric columns
                "result": result,
            })
            print("Session Results After Append:\n", session_results)  # Debug

            session_results = session_results[::-1]
            request.session['calculation_results'] = session_results
            request.session.modified = True
            #debbug
            print(f"Calculation Result for {tool_name}: {result}")
            #debbug
            print("Session Results:\n", request.session.get('calculation_results', []))


            messages.success(request, f"Result for '{tool_name}' has been calculated and stored.")
            return redirect('overview')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('overview')

def delete_calcul(request):
    if request.method == "POST":
        plot_index = int(request.POST.get("calcul_index"))
        plot_results = request.session.get("calculation_results", [])
        if 0 <= plot_index < len(plot_results):
            del plot_results[plot_index]
            request.session["calculation_results"] = plot_results
    return redirect("overview")  

def data_analyze(request):
    data_list = request.session.get('data_list')
    
    if not data_list:
        messages.error(request, "No data available to display.")
        return redirect('index')
    data = pd.DataFrame(data_list)
    if data.isna().any().any():
            messages.error(request, "Data contains missing values. Redirecting to overview.")
            return redirect('overview') 
    
    Tools = {
    "Matplotlib": [
        {
            "tool": "Simple Line Plot",
            "description": "A basic line graph to display trends over a range.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Multiple Line Plot",
            "description": "Displays multiple lines (e.g., quadratic and cubic curves) in a single figure.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Simple Scatter Plot",
            "description": "A plot to visualize individual data points with customizable markers and colors.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Scatter Plot with Legends",
            "description": "A scatter plot enhanced with legends and titles for better clarity.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Basic Box Plot",
            "description": "Visualizes data distribution with box-and-whisker diagrams.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Simple Histogram",
            "description": "Displays the frequency distribution of data using customizable bins.",
            "num_variables": 1,
            "data_type": "numeric"
        }
    ],
    "Seaborn": [
        {
            "tool": "Time Series Plot",
            "description": "A line plot for visualizing time series or continuous data.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Customized Line Plot",
            "description": "A line plot with enhanced markers and labels for clarity.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Categorical Scatter Plot",
            "description": "Scatter plots with categories differentiated using color or markers (hue).",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Simple Box Plot",
            "description": "A single box plot for distribution analysis.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Grouped Box Plot",
            "description": "Box plots separated by categorical variables.",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Univariate Histogram",
            "description": "A histogram for one variable with density or probability options.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Grouped Histogram",
            "description": "Histograms with overlays to compare groups (using hue).",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Univariate KDE Plot",
            "description": "A smooth density curve for a single variable.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Bivariate KDE Plot",
            "description": "A density plot for two variables, optionally combined with scatter plots.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Violin Plot",
            "description": "Displays data distribution across categories with a density curve.",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Bar Plot",
            "description": "Aggregated bar charts, typically for means or sums.",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Count Plot",
            "description": "Shows frequency of occurrences in categorical data.",
            "num_variables": 1,
            "data_type": "categorical"
        },
        {
            "tool": "Annotated Heatmap",
            "description": "Rectangular heatmaps with values and a color map.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Pie Chart",
            "description": "A circular chart representing proportions of a dataset.",
            "num_variables": 1,
            "data_type": "categorical"
        }
    ]
}
    
    string_columns = data.select_dtypes(include='object').columns.tolist()
    numeric_columns = data.select_dtypes(include=['number']).columns.tolist()   
    plot_images = request.session.get('plot_results', [])
    return render(request, 'workshop/analyse.html', {
        'current_page': 'data_analyze',
        'tools': Tools,  
        'string_columns': string_columns,
        'numeric_columns': numeric_columns,
        'plot_images': plot_images
        })

def plot_tool(request):
    if request.method == 'POST':
        data_list = request.session.get('data_list')
        if not data_list:
            messages.error(request, "No data available for plotting.")
            return redirect('index')

        data = pd.DataFrame(data_list)
        tool_name = request.POST.get('tool')
        selected_columns = [request.POST.get(f'column_{i+1}') for i in range(2)] 
        
        if not tool_name:
            messages.error(request, "No plot tool selected.")
            return redirect('index')

        try:
            fig, ax = plt.subplots(figsize=(8, 6))

            if tool_name == "Simple Line Plot":
                data[selected_columns[0]].plot(ax=ax)
            elif tool_name == "Multiple Line Plot":
                for col in selected_columns:
                    data[col].plot(ax=ax, label=col)
                ax.legend()
            elif tool_name == "Simple Scatter Plot":
                data.plot.scatter(x=selected_columns[0], y=selected_columns[1], ax=ax)
            elif tool_name == "Scatter Plot with Legends":
                data.plot.scatter(x=selected_columns[0], y=selected_columns[1], ax=ax)
                ax.legend()
                ax.set_title('Scatter Plot with Legends')
            elif tool_name == "Basic Box Plot":
                data[selected_columns[0]].plot.box(ax=ax)
            elif tool_name == "Simple Histogram":
                data[selected_columns[0]].plot.hist(ax=ax)

            elif tool_name == "Time Series Plot":
                sns.lineplot(data=data[selected_columns[0]], ax=ax)
            elif tool_name == "Customized Line Plot":
                sns.lineplot(data=data[selected_columns[0]], ax=ax, markers='o', dashes=False)
            elif tool_name == "Categorical Scatter Plot":
                sns.scatterplot(x=selected_columns[0], y=selected_columns[1], hue=data[selected_columns[0]], ax=ax)
            elif tool_name == "Simple Box Plot":
                sns.boxplot(data=data[selected_columns[0]], ax=ax)
            elif tool_name == "Grouped Box Plot":
                sns.boxplot(x=selected_columns[1], y=selected_columns[0], data=data, ax=ax)
            elif tool_name == "Univariate Histogram":
                sns.histplot(data[selected_columns[0]], ax=ax, kde=True)
            elif tool_name == "Grouped Histogram":
                sns.histplot(data=data, x=selected_columns[0], hue=selected_columns[1], ax=ax, multiple="stack")
            elif tool_name == "Univariate KDE Plot":
                sns.kdeplot(data[selected_columns[0]], ax=ax)
            elif tool_name == "Bivariate KDE Plot":
                sns.kdeplot(data=data, x=selected_columns[0], y=selected_columns[1], ax=ax)
            elif tool_name == "Violin Plot":
                sns.violinplot(x=selected_columns[1], y=selected_columns[0], data=data, ax=ax)
            elif tool_name == "Bar Plot":
                sns.barplot(x=selected_columns[1], y=selected_columns[0], data=data, ax=ax)
            elif tool_name == "Count Plot":
                sns.countplot(x=selected_columns[0], data=data, ax=ax)
            elif tool_name == "Annotated Heatmap":
                sns.heatmap(data.corr(), annot=True, cmap='coolwarm', ax=ax)
            elif tool_name == "Pie Chart":
                data[selected_columns[0]].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            image_base64 = base64.b64encode(image_png).decode('utf-8')

            session_results = request.session.get('plot_results', [])
            session_results.append({
                "tool": tool_name,
                "columns": selected_columns,
                "plot": image_base64,
            })
            session_results = session_results[::-1]
            request.session['plot_results'] = session_results
            request.session.modified = True

            messages.success(request, f"Plot for '{tool_name}' has been generated and stored.")
            return redirect('data_analyze')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('index')

def download_plot(request):
    if request.method == "POST":
        plot_index = int(request.POST.get("plot_index"))
        plot_results = request.session.get("plot_results", [])
        if 0 <= plot_index < len(plot_results):
            plot_data = plot_results[plot_index]
            plot_base64 = plot_data.get("plot")
            if not plot_base64:
                return HttpResponse("Plot data not found.", status=404)
            plot_image_data = base64.b64decode(plot_base64)
            buffer = BytesIO(plot_image_data)
            response = HttpResponse(buffer, content_type="image/png")
            response["Content-Disposition"] = f"attachment; filename=cortex_plot_{plot_index}.png"
            return response
        else:
            return HttpResponse("Invalid plot index.", status=400)

    return HttpResponse("Invalid request method.", status=405)

def delete_plot(request):
    if request.method == "POST":
        plot_index = int(request.POST.get("plot_index"))
        plot_results = request.session.get("plot_results", [])
        if 0 <= plot_index < len(plot_results):
            del plot_results[plot_index]
            request.session["plot_results"] = plot_results
    return redirect("data_analyze")  

def console(request):
    data_list = request.session.get('data_list')
    if not data_list:
        messages.error(request, "No data available to display.")
        return redirect('index')
    data = pd.DataFrame(data_list)
    if data.isna().any().any():
            messages.error(request, "Data contains missing values. Redirecting to overview.")
            return redirect('overview') 
    
    result = None

    if request.method == "POST":
        command = request.POST.get('command')

        try:
            if command:
           
                result = eval(command, {"df": data})
                if isinstance(result, pd.DataFrame):
                    result = result.head(10)
                    result = result.to_html(
                        classes="table-auto",
                        index=False,
                        escape=False
                    )
                    result = result.replace('<table', '<table class="border-collapse border border-gray-300 text-left w-full"')
                    result = result.replace('<th', '<th class="px-4 py-2 bg-green-500 text-white text-left"')
                    result = result.replace('<td', '<td class="border border-gray-300 px-4 py-2 text-gray-700"')
                elif isinstance(result, pd.Series):
                    result = result.to_frame()
                    result = result.head(10)
                    result = result.to_html(
                        classes="table-auto",
                        index=False,
                        escape=False
                    )
                    result = result.replace('<table', '<table class="border-collapse border border-gray-300 text-left w-full"')
                    result = result.replace('<th', '<th class="px-4 py-2 bg-green-500 text-white text-left"')
                    result = result.replace('<td', '<td class="border border-gray-300 px-4 py-2 text-gray-700"')
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