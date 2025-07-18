import streamlit as st
import pandas as pd
from datetime import datetime

# Load data function
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        # Convert date columns to datetime
        date_cols = ['Picked on', 'First attempted on', 'Last attempted on', 
                    'First Out-For-Delivery on', 'Latest Out-For-Delivery on',
                    'Returned Datetime on', 'Delivered on', 'First Delivery Unable-To',
                    'Last Delivery Unable-To', 'RTO on', 'Date Placed', 'Expected delivery']
        
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def main():
    st.title("Delivery Status Analysis Dashboard")
    
    # File upload
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        if df is not None:
            # Delivery Hub filter
            delivery_hubs = sorted(df['Delivery Hub'].dropna().unique())
            selected_hubs = st.multiselect(
                "Select Delivery Hubs", 
                delivery_hubs,
                default=delivery_hubs
            )
            
            # Filter data based on selected hubs
            filtered_df = df[df['Delivery Hub'].isin(selected_hubs)] if selected_hubs else df
            
            # Convert 'Picked on' to date only (without time)
            filtered_df['Picked Date'] = filtered_df['Picked on'].dt.date
            
            # Get unique dates from 'Picked on'
            unique_dates = sorted(filtered_df['Picked Date'].dropna().unique())
            
            # Date range filter
            if len(unique_dates) > 0:
                min_date = min(unique_dates)
                max_date = max(unique_dates)
                selected_dates = st.date_input(
                    "Select Date Range",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(selected_dates) == 2:
                    start_date, end_date = selected_dates
                    # Further filter by date range
                    filtered_df = filtered_df[
                        (filtered_df['Picked Date'] >= start_date) & 
                        (filtered_df['Picked Date'] <= end_date)
                    ]
            
            # Status columns to count
            status_columns = [
                'Assigned', 'At-Hub', 'Moving-To-Hub',
                'Out-For-Delivery', 'Picked', 'Returned',
                'Returned-To-Hub', 'Unable-To-Deliver'
            ]
            
            # Create pivot table for counts
            try:
                # First get the records that will be included in the pivot table
                pivot_records = filtered_df[
                    (filtered_df['Status'].isin(status_columns)) &
                    (filtered_df['Picked Date'].notna())
                ].copy()
                
                # Create the pivot table from these records
                pivot_data = pivot_records.pivot_table(
                    index='Picked Date',
                    columns='Status',
                    values='Order Number',
                    aggfunc='count',
                    fill_value=0
                )
                
                # Reindex to include all status columns even if they don't appear in data
                pivot_data = pivot_data.reindex(columns=status_columns, fill_value=0)
                
                # Add Total column
                pivot_data['Total'] = pivot_data.sum(axis=1)
                
                # Create a copy for display with Grand Total
                display_data = pivot_data.copy()
                
                # Calculate grand totals (sum of each column)
                grand_totals = display_data.sum().to_dict()
                
                # Convert index to string for display
                display_data.index = display_data.index.astype(str)
                
                # Add Grand Total row
                display_data.loc['Grand Total'] = grand_totals
                
                # Display the pivot table with Grand Total
                st.subheader("Delivery Status Counts by Picked Date")
                
                # Style the DataFrame - apply gradient to all rows except Grand Total
                styled_df = display_data.style.apply(
                    lambda x: ['background: lightblue' if x.name == 'Grand Total' else '' for i in x],
                    axis=1
                ).background_gradient(cmap='Blues', subset=pd.IndexSlice[display_data.index[:-1], :])
                
                st.dataframe(styled_df, use_container_width=True)
                
                # Show summary statistics
                st.subheader("Summary Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Orders", display_data.loc['Grand Total', 'Total'])
                with col2:
                    st.metric("Unique Dates", len(pivot_data))
                with col3:
                    st.metric("Average Orders per Day", round(pivot_data['Total'].mean(), 1))
                
                # Show only the records that are included in the pivot table
                st.subheader("Records Included in Pivot Table")
                st.dataframe(pivot_records, use_container_width=True)
                
                # Download button for pivot records data
                csv = pivot_records.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Pivot Records Data as CSV",
                    data=csv,
                    file_name='pivot_records_data.csv',
                    mime='text/csv'
                )
                
            except Exception as e:
                st.error(f"Error creating pivot table: {e}")
                st.write("Please ensure your data contains the required columns.")
                st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
