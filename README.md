# Excel to Gantt Chart

The goal of this little project is develop a python script, using Numpy, Pandas and the [Gantt Library](https://pypi.org/project/python-gantt/) among others; to read an Excel Sheet that contains a common records from any project and build a Gantt Chart. 

Additionally, we develop some functions to filter records and build charts with the data loaded from the Excel file. 

## Some premisses

1. The template from Excel file must be maintained
2. Holidays must be updated in the second tab in Excel file
3. Gantt charts will be saved in ```./gantt``` folder
