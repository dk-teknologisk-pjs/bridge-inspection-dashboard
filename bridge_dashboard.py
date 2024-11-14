import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

data = pd.read_excel('updated_data.xlsx')

data['report_date'] = pd.to_datetime(data['report_date'], format='mixed', errors='coerce')  # Adjust format if needed
data['construction_date'] = pd.to_datetime(data['construction_date'], format='mixed', errors='coerce')
data['general_inspection_date'] = pd.to_datetime(data['general_inspection_date'], format='mixed', errors='coerce')

st.title('Bridge Inspection Analysis')

st.sidebar.header('Filters')
selected_kommune = st.sidebar.multiselect('Kommune', data['kommune'].unique())
if selected_kommune:
    data = data[data['kommune'].isin(selected_kommune)]

if st.checkbox('Show Raw Data'):
    st.write(data)


# Bridge Condition Analysis
st.header('Bridge Condition')
# Calculate a 'condition score' (e.g., sum of ratings - lower is better)
rating_columns = ['Fl', 'Sk', 'Eu', 'Mu', 'Le', 'Bæ', 'Is', 'Kb', 'Au', 'Be', 'Fu', 'Af', 'Up', 'An']
data['condition_score'] = data[rating_columns].sum(axis=1)

# Display bridges with the worst condition first (highest condition_score)
worst_bridges = data.nlargest(10, 'condition_score') # Top 10 worst
st.write("Worst Condition Bridges:")
st.write(worst_bridges)

st.header('Trend Analysis')
selected_bridge = st.selectbox('Select Bridge for Trend Analysis', data['registration_number'].unique())
selected_element = st.selectbox('Select Element', rating_columns) 

if selected_bridge and selected_element:
    bridge_data = data[data['registration_number'] == selected_bridge].sort_values('general_inspection_date')
    if len(bridge_data) > 1:
        fig = px.line(bridge_data, x='general_inspection_date', y=selected_element, 
                      title=f'Trend for Bridge {selected_bridge} - Element {selected_element}')

        # Fix the y-axis range
        fig.update_yaxes(range=[0, 5], tickvals=[0, 1, 2, 3, 4, 5]) # or tickvals=list(range(5)) if you need more ticks

        st.plotly_chart(fig)
    else:
        st.write('Not enough historical data for trend analysis for this bridge.')

if selected_bridge:
    bridge_data = data[data['registration_number'] == selected_bridge].sort_values('general_inspection_date')
    if len(bridge_data) > 1:
        fig = px.line(bridge_data, x='general_inspection_date', y='condition_score', 
                      title=f'Trend for Bridge {selected_bridge}')
        st.plotly_chart(fig)
    else:
        st.write('Not enough historical data for trend analysis for this bridge.')

st.header('Average Ratings Over Time')


selected_element = st.selectbox('Select Element', rating_columns, key="element_select")
selected_bridge = st.selectbox('Select Bridge (Optional)', data['registration_number'].unique().tolist() + ['All Bridges'], key="bridge_select", index=len(data['registration_number'].unique()))  # Add "All Bridges" option


if selected_element:
    start_year = 1960
    end_year = data['general_inspection_date'].max().year
    intervals = []
    while start_year <= end_year:
        intervals.append((start_year, min(start_year + 9, end_year)))
        start_year += 10

    average_ratings_over_time = []
    for i, (start, end) in enumerate(intervals):
        interval_data = data[(data['general_inspection_date'].dt.year >= start) & (data['general_inspection_date'].dt.year <= end)]
        if not interval_data.empty:
            if selected_bridge == 'All Bridges':
                avg_rating = interval_data[selected_element].mean()
            else:
                bridge_interval_data = interval_data[interval_data['registration_number'] == selected_bridge]
                if not bridge_interval_data.empty:
                    avg_rating = bridge_interval_data[selected_element].mean()
                else:
                    avg_rating = None  # Handle case where selected bridge has no data in the interval

            if avg_rating is not None:  # Only append if avg_rating is calculated
                average_ratings_over_time.append({'Interval': f"{start}-{end}", 'Average Rating': avg_rating})

    if average_ratings_over_time:
        avg_ratings_df = pd.DataFrame(average_ratings_over_time)
        title = f'Average {selected_element} Rating Over Time'
        if selected_bridge != 'All Bridges':
            title += f' for Bridge {selected_bridge}'
        fig = px.bar(avg_ratings_df, x='Interval', y='Average Rating', title=title)
        fig.update_yaxes(range=[0, 4], tickvals=list(range(5)))
        st.plotly_chart(fig)
    else:
        st.write("No data available.")


#####

st.header('Outlier Bridge Ratings')

selected_element = st.selectbox('Select Element', rating_columns, key="element_select1")
start_date = st.date_input("Start Date", value=data['general_inspection_date'].min(), key="start_date")
end_date = st.date_input("End Date", value=data['general_inspection_date'].max(), key="end_date")
threshold = st.number_input("Threshold (Standard Deviations from Mean)", value=2.0, key="threshold")



if selected_element:

    # Filter data for the selected date range
    filtered_data = data[(data['general_inspection_date'] >= pd.to_datetime(start_date)) & (data['general_inspection_date'] <= pd.to_datetime(end_date))]


    if not filtered_data.empty:
        # Calculate mean and standard deviation for the selected element
        element_mean = filtered_data[selected_element].mean()
        element_std = filtered_data[selected_element].std()

        # Identify outlier bridges
        outlier_bridges = filtered_data[
            (filtered_data[selected_element] > element_mean + threshold * element_std) |
            (filtered_data[selected_element] < element_mean - threshold * element_std)
        ]

        if not outlier_bridges.empty:
            st.write(f"Bridges with {selected_element} ratings outside {threshold} standard deviations from the mean:")
            st.write(outlier_bridges)
        else:
            st.write("No outlier bridges found for the selected criteria.")

    else:
        st.write("No data available for the selected date range.")
