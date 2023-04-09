from ganttchart import GanttChart

mygantt = GanttChart('project_example_source.xlsx', 'MAIN PROJECT')
mygantt.load_data_and_holidays()

# test ok
# mygantt.build_chart()

# test ok
# mygantt.calculate_diff_and_delay()


fields = ['start_date', 'forecast', 'accomplished']
for _field in fields:
    print(f"Records with date before today, by '{_field}'")
    print(mygantt.records_with_date_before_today_by(_field))

    print(f"Records with date after today, by '{_field}'")
    print(mygantt.records_with_date_after_today_by(_field))
