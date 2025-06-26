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
            
            # Status columns to count
            status_columns = [
                'Assigned', 'At-Hub', 'At-Hub-RTO', 'Moving-To-Hub',
                'Out-For-Delivery', 'Out-For-Pickup', 'Picked', 'Returned',
                'Returned-To-Hub', 'Unable-To-Deliver'
            ]
            
            # Create pivot table for counts
            try:
                pivot_data = filtered_df.pivot_table(
                    index='Picked Date',
                    columns='Status',
                    values='Order Number',
                    aggfunc='count',
                    fill_value=0
                )
                
                # Reindex to include all status columns even if they don't appear in data
                pivot_data = pivot_data.reindex(columns=status_columns, fill_value=0)
                
                # Display the pivot table
                st.subheader("Delivery Status Counts by Picked Date")
                st.dataframe(pivot_data.style.background_gradient(cmap='Blues'), use_container_width=True)
                
                # Show raw data
                st.subheader("Raw Data")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download button for filtered data
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Filtered Data as CSV",
                    data=csv,
                    file_name='filtered_delivery_data.csv',
                    mime='text/csv'
                )
                
            except Exception as e:
                st.error(f"Error creating pivot table: {e}")
                st.write("Please ensure your data contains the required columns.")
                st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()