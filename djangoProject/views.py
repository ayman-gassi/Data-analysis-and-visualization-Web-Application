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

probability_distributions = [
    {
        "title": "Uniform Distribution",
        "definition": "A probability distribution in which all outcomes are equally likely.",
        "description": "Used when every possible outcome has the same chance of occurring, such as rolling a fair die.",
        "howto": "Assign equal probabilities to each outcome.",
        "requirement": "Column must contain distinct values with equal chances of occurring.",
        "data_type": "numeric"
    },
    {
        "title": "Binomial Distribution",
        "definition": "Describes the number of successes in a fixed number of trials.",
        "description": "Useful for binary outcomes like Yes/No.",
        "howto": "Count successes over multiple trials.",
        "requirement": "Column must represent binary outcomes (e.g., Yes/No or 0/1).",
        "data_type": "boolean"
    },
    {
        "title": "Poisson Distribution",
        "definition": "Models the number of events occurring in a fixed interval.",
        "description": "Used for rare event modeling like customer arrivals.",
        "howto": "Specify the average rate of events.",
        "requirement": "Column must represent counts of events.",
        "data_type": "numeric"
    },
    {
        "title": "Exponential Distribution",
        "definition": "Describes the time between events in a Poisson process.",
        "description": "Used to model waiting times, such as time until the next customer arrives.",
        "howto": "Specify the rate at which events occur.",
        "requirement": "Column must represent time intervals between events.",
        "data_type": "numeric"
    },
    {
        "title": "Bernoulli Distribution",
        "definition": "Models a single trial with two possible outcomes.",
        "description": "The simplest distribution, often used as a building block.",
        "howto": "Assign a probability of success.",
        "requirement": "Column must represent binary outcomes (e.g., Yes/No or 0/1).",
        "data_type": "boolean"
    },
    {
        "title": "Normal Distribution",
        "definition": "A continuous distribution symmetric about the mean.",
        "description": "Used for natural phenomena like heights, test scores, etc.",
        "howto": "Specify the mean and standard deviation.",
        "requirement": "Column must represent continuous numerical data.",
        "data_type": "numeric"
    }
]

Analyse_tools = [
        {"name": "Mean", "description": "Calculate the mean value."},
        {"name": "Median", "description": "Calculate the median value."},
        {"name": "Mode", "description": "Calculate the mode value."},
        {"name": "Max", "description": "Find the maximum value."},
        {"name": "Min", "description": "Find the minimum value."},
        {"name": "Sum", "description": "Calculate the sum."},
        {"name": "Covariance", "description": "Calculate the covariance matrix."},
        {"name": "Correlation", "description": "Calculate the correlation matrix."},
        {"name": "Count", "description": "Count the values."}
    ]

Plots_tools = {
    "Matplotlib": [
        {
            "tool": "Line Plot",
            "description": "Displays trends over time or continuous data.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Scatter Plot",
            "description": "Shows the relationship between two numeric variables.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Histogram",
            "description": "Displays the frequency distribution of a numeric variable.",
            "num_variables": 1,
            "data_type": "numeric"
        },
        {
            "tool": "Box Plot",
            "description": "Summarizes data distribution using quartiles.",
            "num_variables": 1,
            "data_type": "numeric"
        }
    ],
    "Seaborn": [
        {
            "tool": "Heatmap",
            "description": "Displays correlations between numeric variables.",
            "num_variables": 2,
            "data_type": "numeric"
        },
        {
            "tool": "Bar Plot",
            "description": "Compares categorical data with numeric aggregates (e.g., mean).",
            "num_variables": 2,
            "data_type": "numeric and categorical"
        },
        {
            "tool": "Count Plot",
            "description": "Shows the frequency of categories.",
            "num_variables": 1,
            "data_type": "categorical"
        },
        {
            "tool": "KDE Plot",
            "description": "Displays a smooth density curve for numeric data.",
            "num_variables": 1,
            "data_type": "numeric"
        }
    ]
}

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
    column_names = data.select_dtypes(include=['number']).columns.tolist() 
   
    tools_requiring_columns = ["Mean", "Median", "Mode", "Max", "Min", "Sum"]
    tools_requiring_two_columns = ["Covariance", "Correlation"]


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
        'tools': Analyse_tools,
        'tools_requiring_columns': tools_requiring_columns,
        'tools_requiring_two_columns': tools_requiring_two_columns,
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
        selected_second_column = request.POST.get('secondColumn') 

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

            elif tool_name in ["Covariance", "Correlation"]:
                if not selected_column or not selected_second_column:
                    messages.error(request, "Two columns must be selected for this calculation.")
                    return redirect('overview')
                
                if selected_column not in data.columns or selected_second_column not in data.columns:
                    messages.error(request, "Invalid columns selected.")
                    return redirect('overview')

                column_x = data[selected_column]
                column_y = data[selected_second_column]
                
                if tool_name == "Covariance":
                   result = round(column_x.cov(column_y), 2)
                elif tool_name == "Correlation":
                   result = round(column_x.corr(column_y), 2) 

            elif tool_name == "Count":
                result = data[data.columns[0]].count()

            else:
                messages.error(request, "Invalid tool selected.")
                return redirect('overview')

            session_results = request.session.get('calculation_results', [])
            session_results.append({
                "tool": tool_name,
                "columns": f"{selected_column} & {selected_second_column}" if tool_name in ["Covariance", "Correlation"] else selected_column,
                "result": float(result) if isinstance(result, (np.float64, np.float32)) else
                        int(result) if isinstance(result, (np.int64, np.int32)) else result,
            })
            session_results = session_results[::-1]
            request.session['calculation_results'] = session_results
            request.session.modified = True

            messages.success(request, f"Result for '{tool_name}' has been calculated and stored: {result:.4f}")
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
    
    string_columns = data.select_dtypes(include='object').columns.tolist()
    numeric_columns = data.select_dtypes(include=['number']).columns.tolist()   
    plot_images = request.session.get('plot_results', [])
    return render(request, 'workshop/analyse.html', {
        'current_page': 'data_analyze',
        'tools': Plots_tools,  
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
        selected_columns = [request.POST.get(f'column_{i+1}') for i in range(2) if request.POST.get(f'column_{i+1}')]

        if not tool_name:
            messages.error(request, "No plot tool selected.")
            return redirect('index')

        try:
            sns.set_palette("Set2")
            plt.style.use('ggplot')
            fig, ax = plt.subplots(figsize=(8, 6))

            # Generate plots based on the selected tool
            if tool_name == "Line Plot":
                data[selected_columns[0]].plot(ax=ax, color='blue', linestyle='-', linewidth=2)
                ax.set_title("Line Plot")
                ax.set_xlabel("Index")
                ax.set_ylabel(selected_columns[0])
            elif tool_name == "Scatter Plot":
                data.plot.scatter(x=selected_columns[0], y=selected_columns[1], ax=ax, color='purple')
                ax.set_title("Scatter Plot")
            elif tool_name == "Histogram":
                data[selected_columns[0]].plot.hist(ax=ax, color='orange', edgecolor='black', bins=10)
                ax.set_title("Histogram")
                ax.set_xlabel(selected_columns[0])
                ax.set_ylabel("Frequency")
            elif tool_name == "Box Plot":
                data[selected_columns[0]].plot.box(ax=ax, patch_artist=True, boxprops=dict(facecolor='cyan'))
                ax.set_title("Box Plot")
            elif tool_name == "Heatmap":
                heatmap_data = data.pivot_table(index=selected_columns[0], columns=selected_columns[1], aggfunc='size', fill_value=0)
                sns.heatmap(heatmap_data, annot=True, cmap='coolwarm', ax=ax)
                ax.set_title("Heatmap")
            elif tool_name == "Bar Plot":
                sns.barplot(x=selected_columns[0], y=selected_columns[1], data=data, palette="bright", ax=ax)
                ax.set_title("Bar Plot")
            elif tool_name == "Count Plot":
                sns.countplot(x=selected_columns[0], data=data, palette="deep", ax=ax)
                ax.set_title("Count Plot")
            elif tool_name == "KDE Plot":
                sns.kdeplot(data[selected_columns[0]], ax=ax, color='purple', fill=True)
                ax.set_title("KDE Plot")
                ax.set_xlabel(selected_columns[0])
                ax.set_ylabel("Density")

            # Save the plot as an image
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

def probability(request):
    return render(request, 'workshop/proba.html', {"distributions": probability_distributions , "current_page": "probability"})

def probability_detail(request, title):
    data_list = request.session.get('data_list')
    if not data_list:
        messages.error(request, "No data available for plotting.")
        return redirect('index')
    
    distribution = next((item for item in probability_distributions if item["title"] == title), None)
    if not distribution:
        return redirect('probability')
    
    data = pd.DataFrame(data_list) 
    # string_columns = data.select_dtypes(include='object').columns.tolist() or []
    # numeric_columns = data.select_dtypes(include=['number']).columns.tolist() or []
    # boolean_columns = data.select_dtypes(include='bool').columns.tolist() or []
    
    # if distribution["data_type"] == "numeric":
    #     valid_columns = numeric_columns
    # elif distribution["data_type"] == "string":
    #     valid_columns = string_columns
    # elif distribution["data_type"] == "boolean":
    #     valid_columns = boolean_columns
    # else:
    #     valid_columns = []

    # if not valid_columns:
    #     print(request, f"No valid {distribution['data_type']} columns found for {title}.")


    return render(
        request,
        'workshop/proba_detail.html',
        {
            "distribution": distribution,
            "data_columns": data.columns.tolist() or [],
            "valid_columns": distribution["data_type"],
            "probability": request.session.get(f"{title}_result"),
            "current_page": "probability",
            "graph": request.session.get(f"{title}_graph")
        }
    )

def apply_distribution(request, title):
    data_list = request.session.get('data_list')
    if not data_list:
        messages.error(request, "No data available for plotting.")
        return redirect('index')
    
    distribution = next((item for item in probability_distributions if item["title"] == title), None)
    if not distribution:
        messages.error(request, "Invalid distribution selected.")
        return redirect('probability')
    
    data = pd.DataFrame(data_list)
    column_name = request.POST.get('column')
    column_args1 = float(request.POST.get('column_args1', 1)) 
    column_args2 = float(request.POST.get('column_args2', 0.5))
    if not column_name or not column_args1 or not column_args2:
        messages.error(request, "Something not selected selected.")
        return redirect('probability_detail', title=title ,current_page="probability")
    
    try:
        result = None
        simulated = None
        details = None

        if distribution["title"] == "Uniform Distribution":
                result = 0
                simulated = data[column_name]
                plot_type = "bar"
        elif distribution["title"] == "Binomial Distribution":
            simulated = np.random.binomial(column_args1, column_args2, size=len(data[column_name]))
            result = float(simulated.mean())
            plot_type = "bar"
        elif distribution["title"] == "Poisson Distribution":
            lambda_value = data[column_name].mean()
            details = "lambda = " + str(lambda_value)
            simulated = np.random.poisson(lambda_value, size=len(data[column_name]))
            result = float(simulated.mean())
            plot_type = "histogram"
        elif distribution["title"] == "Exponential Distribution":
            lambda_value = 1 / data[column_name].mean()
            details = f"lambda = {lambda_value:.2f}"
            simulated = np.random.exponential(lambda_value, size=len(data[column_name]))
            result = float(simulated.mean())
            plot_type = "density"
        elif distribution["title"] == "Bernoulli Distribution":
            simulated = np.random.binomial(column_args1,column_args2, size=len(data[column_name]))
            result = float(simulated.mean())
            print(result)
            plot_type = "bar"
        elif distribution["title"] == "Normal Distribution":
            mean = data[column_name].mean()
            std_dev = data[column_name].std()
            simulated = np.random.normal(mean, std_dev, size=len(data[column_name]))
            details = "Mean  = {:.2f}, Standard Deviation (σ) = {:.2f}".format(mean, std_dev)
            result = 0
            plot_type = "density"
        else:
            messages.error(request, "Invalid distribution logic.")
            return redirect('probability_detail', title=title)
        
        session_key = f"{title}_result"
        request.session[session_key] = result

        plt.figure(figsize=(8, 4))
        plt.rcParams['axes.facecolor'] = 'white'  
        plt.rcParams['figure.facecolor'] = 'white'  
        if plot_type == "bar":
            unique, counts = np.unique(simulated, return_counts=True)
            plt.title(f'{title}')
            plt.bar(unique, counts, alpha=0.7, color='white', edgecolor='white')
            plt.xlabel('Value')
        elif plot_type == "histogram":
            plt.hist(simulated, bins=10, alpha=0.7, color='white', edgecolor='white')
            plt.title(f'{title}  - {details}')
            plt.xlabel('Value')
            plt.ylabel('Frequency')
        elif plot_type == "density":
            density, bins, _ = plt.hist(simulated, bins=10, density=True, alpha=0.7, color='white', edgecolor='white')
            plt.title(f'{title} - {details}')
            plt.plot(bins[:-1], density, linestyle='--', color='red')
            plt.xlabel('Value')
            plt.ylabel('Density')
        
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        image_base64 = base64.b64encode(image_png).decode('utf-8')
        session_key2 = f"{title}_graph"
        request.session[session_key2] = image_base64

        # Success message
        messages.success(request, f"Computed result for '{title}': {result:.4f}")
        return redirect('probability_detail', title=title)
    except Exception as e:
        # Error handling
        session_key = f"{title}_result"
        request.session[session_key] = "Error while computing the result."
        session_key2 = f"{title}_graph"
        request.session[session_key2] = None
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('probability_detail', title=title ,current_page="probability")

def logout(request):
    request.session.flush()
    messages.success(request, "You have successfully logged out.")
    return redirect('index')