"""
Gantt Class to build Gantt Charts


"""

import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import gantt
import datetime
import random

__author__ = 'Pablo Veinberg'
__version__ = '1.0'

class GanttChart :

    pie_size = (8, 8)
    barh_size = (16, 8)
    colors = ['yellow', 'lime', 'red', 'orange', 'green', 'gray', 'aqua']

    def __init__(self, filename, main_project_name) -> None:
        
        # Day in Brazil (Latin América) format
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')

        self.filename = filename
        self.main_project_name = main_project_name
        pass    
    
    # Load tasks records and holidays
    def load_data_and_holidays(self):
        self.data = pd.read_excel(self.filename, sheet_name='Project')
        self.data_holidays = pd.read_excel(self.filename, sheet_name='Holidays')
        self.holidays = list(self.data_holidays.Day)
        
    # Get records with date (start_date | forecast | accomplished) equal or after current date
    def records_with_date_after_today_by(self, _field):
        return self.data.loc[(self.data[_field] >= self.today)].copy()

    # Get records with date (start_date | forecast | accomplished) equal or before current date
    def records_with_date_before_today_by(self, _field):
        return self.data.loc[(self.data[_field] < self.today)].copy()

    # Delayed records
    def delayed_records(self):
        field = 'forecast'
        return self.data.loc[(self.data[field] < self.today) & (self.data['pct_progress'] < 100)].copy()

    # Records with 'accomplished' date not 'NaT' and 'pct_progress = 100
    def accomplished_records(self):
        return self.data.loc[(self.data['accomplished'].notna()) & (self.data['pct_progress'] == 100)].copy()

    # Records whose 'pct_progress' isn't zero (not started), but isn't 100 (not accomplished)
    def records_in_progress(self):
        return self.data.loc[(self.data['pct_progress'] > 0) \
                             & (self.data['pct_progress'] < 100) \
                             & (self.data['accomplished'] <= self.today)].copy()

    # Inconsistents records
    def inconsistens_records(self):
        return self.data.loc[(self.data['start_date'] > self.data['forecast'])].copy()

    # Get a filename using a source name and datetime 
    def get_chart_filename(self, _name):
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        _name = _name.lower().replace(' ', '_').replace('.', '_')
        return f'{_name}_{now}.svg'

    # Get a tasks list (Gantt objects)
    def get_tasks(self, _data, _color):
        tasks = []
        codes = []
        
        start_date = pd.Timestamp(datetime.datetime.today())
        end_date = pd.Timestamp(datetime.datetime.today())

        try:
            for item in _data.iterrows():
                codes.append(item[1]['id'])
                tasks.append(gantt.Task( \
                    name=item[1]['task'], \
                    fullname=f"{item[1]['id']} - {item[1]['task']}", \
                    start=pd.Timestamp(item[1]['start_date']), \
                    duration=item[1]['days'], \
                    percent_done=item[1]['pct_progress'], \
                    color=_color, \
                    resources=[gantt.Resource(item[1]['external_owner'])] ))


                start_date = pd.Timestamp(item[1]['start_date']) if pd.Timestamp(item[1]['start_date']) < start_date \
                    else start_date
                end_date = pd.Timestamp(item[1]['accomplished']) if pd.Timestamp(item[1]['accomplished']) > end_date \
                    else end_date
                
        except KeyError:
            raise Exception('An keyerror type occurs')
        finally:
            print(f"Tasks to {item[1]['source']} processed ok")
            
        result = self.process_dependencies(list(zip(codes, tasks)))
        return start_date, end_date, result

    # Process all dependencies (depends_of) from a tasks set
    def process_dependencies(self, _tasks:list):
        result = []
        for task_id, task_obj in _tasks:
            # get dependencies (objects lists)
            task_obj.depends_of = self.get_dependencies(task_id, _tasks)
            result.append((task_id, task_obj))
            
        return result

    # Get an object (gantt) list with tasks that depends of current task (by 'id')
    def get_dependencies(self, _id, _tasks):
        try:
            dependencies = str(self.data.loc[self.data['id'] == _id].values[0][1]).split(';')
            result = []
            for task_id, task_obj in _tasks:
                if str(task_id) in dependencies:
                    result.append(task_obj)
            return result
        except:
            raise Exception("Exception in 'get_dependencies' function")

    # Get a task by id
    def get_task_by_code(_id_find, _task_list:list):
        for _task in _task_list:
            if _task[0] == _id_find:
                return _task[1]
            
        return None

    # Adding resources
    
    def build_chart(self):

        gantt.define_font_attributes(fill='black', stroke='black', stroke_width=0, font_family="Verdana")

        # Add holidays
        for day in list(self.data_holidays.Day):
            gantt.add_vacations(day)

        # Add resources to Gantt
        for name in list(self.data.external_owner.unique()):
            gantt.Resource(name)

        # Split sources and build gantts charts
        projects = []

        for _name in list(self.data.source.unique()):
            source = _name.upper().replace(' ', '_').replace(' ', '')
            export_filename = self.get_chart_filename(_name)
            data_source = self.data.loc[(self.data.source == _name)]
            color = random.choice(self.colors)
            start_date, end_date, tasks = self.get_tasks(data_source, color)
            
            # Create a project
            try:
                proj = gantt.Project(name=source)
                for (cod, t) in tasks:
                    proj.add_task(t)
            except KeyError:
                raise Exception('An error processing task')
            finally:
                print(f'All tasks from {source} where processed and added to new project')
                print(f"Start date: {start_date}, {type(start_date)}")
                print(f"End date: {end_date}")

            projects.append(proj)
            proj.make_svg_for_tasks(filename=f'./gantts/{export_filename}', \
                start=start_date, \
                today=datetime.datetime.today(), \
                end=end_date)

        full = gantt.Project(name=self.main_project_name)
        for prj in projects:
            full.add_task(prj)

        full.make_svg_for_tasks(filename='./gantts/full.svg')


    # Some differences and delays
    def calculate_diff_and_delay(self):

        date_type = 'datetime64[D]'

        ins_date = np.array(self.data['start_date'].values.astype(date_type))
        forecast_date = np.array(self.data['forecast'].values.astype(date_type))
        accomplished_date = np.array(self.data['accomplished'].values.astype(date_type))

        try:
            # Diff between init date and forecast date
            self.data['diff'] = np.busday_count(ins_date, forecast_date)

            # Diff between forecast date and accomplished date
            self.data['delay'] = np.busday_count(forecast_date, accomplished_date)

            print(self.data[['task', 'diff', 'delay']].head())
        
        except ValueError:
            raise Exception()

    def plot_data(self, _group):
        sources = self.data.groupby(_group)['pct_progress'].mean().sort_values(ascending=False).copy()
        print(sources)

        ax = sources.plot(kind='barh', title=f'Activity progress by {_group} source', figsize=self.barh_size)
        ax.set_xlabel('Progress (%)')
        plt.show()

    # Categorize tasks by 'pct_progress'
    def categorize_by_progress(self):
        self.data['progress'] = pd.cut(self.data.pct_progress, bins=[-1,30, 70, 101], \
                                       labels=['Initial Phase', 'In progress', 'Accomplished'])
        self.data.groupby('progress')['progress'].count() \
            .plot(kind='pie', title='Progress by status', figsize=self.pie_size)
        
        plt.show()

    # Categorize by time (just not accomplished taks - not 100%)
    def categorize_by_time(self):
        self.data['wip'] = pd.cut(self.data['diff'], bins=[-1,3,7,15,25,100], \
                                  labels=['Short', 'Medium', 'Long', 'Extra Long', 'Long Term']).astype('category')

        pending = self.data[self.data['pct_progress'] != 100].copy()
        pending.groupby('wip')['progress'].count().plot(kind="pie", title="Tasks by size", figsize=self.pie_size)
        
        plt.show()

    # Number of tasks by internal owner and accomplished average 
    def get_number_task_by_owner(self):
        return list(self.data.groupby('internal_owner')[['wip', 'task']]) 
